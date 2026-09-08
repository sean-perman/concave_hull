"""Runtime + failure-count sweep across user-defined variants.

Mirrors the old `legacy/runtime_comparison.py` shape but driven by the new
ConcaveHullConfig:
edit the VARIANTS list at the bottom to compare whatever axes you want.

Each variant is a (label, dict-of-config-kwargs) pair. For every variant and
every dataset size, the script runs `num_runs` trials, records average runtime,
and counts failures. Failure = (`HullResult.success is False`) OR a subprocess
timeout OR an unexpected exception.

Results written as a tidy CSV to results/YYYY-MM-DD/benchmark_<HH-MM-SS>.csv —
one row per (dataset, variant, n) with all metrics as columns. Chart it later in
whatever tool you like. A readable summary table is also printed per dataset.

Run as a script:
  python -m concave_hull_experiment.benchmark
  python concave_hull_experiment/benchmark.py
"""
import csv
import math
import multiprocessing
import os
import queue
import sys
import time
from datetime import datetime

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from concave_hull_experiment.concave_hull import ConfigurableConcaveHull
    from concave_hull_experiment.config import ConcaveHullConfig
else:
    from .concave_hull import ConfigurableConcaveHull
    from .config import ConcaveHullConfig

DATASETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets"
)


def generate_unit_disk_points(n: int, seed: int) -> list[tuple[float, float]]:
    rng = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(-1.0, 1.0, size=2)
        if x * x + y * y <= 1.0:
            pts.append((float(x), float(y)))
    return pts


def generate_star_points(n: int, seed: int, *, num_tips: int = 8,
                         outer_r: float = 100.0, inner_r: float = 4.0,
                         jitter: float = 3.0) -> list[tuple[float, float]]:
    """8-tip star cloud, ported from legacy/monolithic/seans_concavehull_4.py:1111-1130.

    Points cluster around the star outline with a radial bias toward the boundary
    (the `0.7 + 0.3*random()` factor) plus uniform xy jitter. This dataset has
    deep concavities at the inter-tip valleys — much harder for the kNN concave
    hull than the unit disk.
    """
    rng = np.random.default_rng(seed)
    pts = []
    for _ in range(n):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        sector = angle / (math.pi / num_tips)
        frac = sector - int(sector)
        if int(sector) % 2 == 0:
            base_r = outer_r + (inner_r - outer_r) * frac
        else:
            base_r = inner_r + (outer_r - inner_r) * frac
        r = base_r * (0.7 + 0.3 * rng.random())
        x = r * math.cos(angle) + rng.uniform(-jitter, jitter)
        y = r * math.sin(angle) + rng.uniform(-jitter, jitter)
        pts.append((float(x), float(y)))
    return pts


def load_csv_points(filename: str) -> list[tuple[float, float]]:
    """Load an x,y CSV from datasets/ into a list of (x, y) tuples."""
    path = os.path.join(DATASETS_DIR, filename)
    pts: list[tuple[float, float]] = []
    with open(path) as f:
        reader = csv.reader(f)
        next(reader, None)  # header row: x,y
        for row in reader:
            if len(row) >= 2:
                pts.append((float(row[0]), float(row[1])))
    return pts


def csv_dataset(filename: str):
    """Wrap a real CSV as a generator(n, seed) -> points that always returns the
    FULL dataset (n and seed ignored).

    Real GIS sets are fixed shapes — we run them once at their native size, NOT
    subsampled. Random subsampling would change the very geometry we want to test
    (the hull of 100 random redwood points is a different shape than the full set),
    conflating density with shape. Scaling studies belong to the synthetic
    generators, where n varies but the shape is controlled. The `.native_size`
    attribute tells the driver to run a single size for this dataset.
    """
    points = load_csv_points(filename)

    def gen(n=None, seed=None) -> list[tuple[float, float]]:
        return list(points)

    gen.native_size = len(points)
    return gen


def _run_worker(points, cfg_kwargs: dict, output_queue) -> None:
    """Execute one timed algorithm run in a child process."""
    # Default to "report" so the final-hull containment check runs and points_outside
    # is recorded. A variant that sets validate_final_hull explicitly (e.g. "enforce"
    # for a faithful original baseline) overrides this.
    cfg = ConcaveHullConfig(**{"validate_final_hull": "report", **cfg_kwargs})
    try:
        t0 = time.perf_counter()
        result = ConfigurableConcaveHull().run(points, cfg)
        elapsed = time.perf_counter() - t0
        output_queue.put(("result", result, elapsed))
    except Exception as exc:
        output_queue.put(("exception", type(exc).__name__, None))


def run_one(points, cfg_kwargs: dict, timeout_s: float = 30.0):
    """Run once in a killable subprocess so timeouts cannot poison later timings."""
    context = multiprocessing.get_context("spawn")
    output_queue = context.Queue()
    process = context.Process(
        target=_run_worker,
        args=(points, cfg_kwargs, output_queue),
    )
    process.start()
    process.join(timeout=timeout_s)

    if process.is_alive():
        process.terminate()
        process.join()
        output_queue.close()
        return None, timeout_s, "timeout"

    try:
        kind, payload, elapsed = output_queue.get(timeout=1.0)
    except queue.Empty:
        output_queue.close()
        return None, 0.0, f"worker-exit:{process.exitcode}"
    finally:
        output_queue.close()

    if kind == "exception":
        return None, 0.0, f"exception:{payload}"
    res = payload
    if res is None or not res.success:
        reason = res.failure_reason if res is not None else "no result"
        return res, elapsed, f"fail:{reason}"
    return res, elapsed, None


def run_sweep(variants, dataset_sizes, generator, num_runs=10, timeout_s=30.0):
    """For each (variant, n), run num_runs times, return per-variant runtime/failure lists.

    `generator` is a callable (n, seed) -> list[(x, y)] — a synthetic generator or a
    `csv_dataset(...)` wrapper around a real dataset.
    """
    results = {label: [] for label, _ in variants}
    failures = {label: [] for label, _ in variants}
    final_ks = {label: [] for label, _ in variants}
    hull_lens = {label: [] for label, _ in variants}
    restarts = {label: [] for label, _ in variants}
    wasted_edges = {label: [] for label, _ in variants}
    points_outside = {label: [] for label, _ in variants}
    total = len(variants) * len(dataset_sizes) * num_runs
    done = 0

    for label, cfg_kwargs in variants:
        for n in dataset_sizes:
            successes = []
            fails = 0
            ks = []
            hls = []
            rs = []
            edge_totals = []  # res.total_restart_edges per successful run
            outs = []         # res.points_outside per successful run (validation = "report")
            for run in range(num_runs):
                pts = generator(n, seed=run)
                res, elapsed, fail_reason = run_one(pts, cfg_kwargs, timeout_s=timeout_s)
                if fail_reason is not None:
                    fails += 1
                else:
                    successes.append(elapsed)
                    ks.append(res.final_k)
                    hls.append(len(res.hull))
                    rs.append(res.restarts)
                    edge_totals.append(res.total_restart_edges)
                    if res.points_outside is not None:
                        outs.append(res.points_outside)
                done += 1
                print(
                    f"  [{done:>4d}/{total}] {label:<28s} n={n:>5d} run={run + 1:>2d}/{num_runs} "
                    f"{'OK' if fail_reason is None else fail_reason}",
                    flush=True,
                )

            avg = sum(successes) / len(successes) if successes else None
            avg_restarts = sum(rs) / len(rs) if rs else None
            avg_wasted_edges = sum(edge_totals) / len(edge_totals) if edge_totals else None
            avg_points_outside = sum(outs) / len(outs) if outs else None
            # Pool edges and restarts across runs first, then divide — keeps it
            # well-defined for sizes where some runs had zero restarts.
            total_r = sum(rs)
            total_e = sum(edge_totals)
            avg_restart_size = (total_e / total_r) if total_r > 0 else None
            results[label].append(avg)
            failures[label].append(fails)
            final_ks[label].append(int(sum(ks) / len(ks)) if ks else None)
            hull_lens[label].append(int(sum(hls) / len(hls)) if hls else None)
            restarts[label].append(avg_restarts)
            wasted_edges[label].append(avg_wasted_edges)
            points_outside[label].append(avg_points_outside)
            print(
                f"  -> {label:<28s} n={n:>5d}  avg_ms={1000 * avg if avg else float('nan'):8.2f}  "
                f"fails={fails:>2d}/{num_runs}  "
                f"avg_k={final_ks[label][-1]}  avg_hull={hull_lens[label][-1]}  "
                f"avg_restarts={avg_restarts if avg_restarts is not None else float('nan'):6.2f}  "
                f"avg_restart_size={avg_restart_size if avg_restart_size is not None else float('nan'):6.2f}  "
                f"outside={avg_points_outside if avg_points_outside is not None else float('nan'):5.1f}",
                flush=True,
            )

    return results, failures, final_ks, hull_lens, restarts, wasted_edges, points_outside


# Tidy long-format columns: one row per (dataset, variant, n). Chart-tool friendly.
CSV_COLUMNS = [
    "dataset", "variant", "n", "num_runs", "successes", "failures",
    "avg_runtime_ms", "avg_restarts", "avg_wasted_edges", "avg_restart_size",
    "avg_final_k", "avg_hull_len", "avg_points_outside",
]


def rows_from_sweep(dataset, variants, dataset_sizes, num_runs,
                    results, failures, final_ks, hull_lens, restarts, wasted_edges,
                    points_outside):
    """Flatten the per-variant sweep dicts into one row per (dataset, variant, n).

    avg_restart_size = avg wasted edges / avg restart count (edges discarded per
    failure event); blank when there were no failures. None stays None -> blank cell.
    """
    rows = []
    for label, _ in variants:
        for i, n in enumerate(dataset_sizes):
            runtime = results[label][i]
            rest = restarts[label][i]
            waste = wasted_edges[label][i]
            fails = failures[label][i]
            outside = points_outside[label][i]
            restart_size = (waste / rest) if (rest and waste is not None) else None
            rows.append({
                "dataset": dataset,
                "variant": label,
                "n": n,
                "num_runs": num_runs,
                "successes": num_runs - fails,
                "failures": fails,
                "avg_runtime_ms": round(runtime * 1000, 4) if runtime is not None else None,
                "avg_restarts": round(rest, 3) if rest is not None else None,
                "avg_wasted_edges": round(waste, 2) if waste is not None else None,
                "avg_restart_size": round(restart_size, 2) if restart_size is not None else None,
                "avg_final_k": final_ks[label][i],
                "avg_hull_len": hull_lens[label][i],
                "avg_points_outside": round(outside, 2) if outside is not None else None,
            })
    return rows


def write_results_csv(rows, *, base_folder="results", suffix=""):
    """Write all collected rows to one tidy CSV (None -> empty cell)."""
    date_folder = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(base_folder, date_folder)
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%H-%M-%S")
    path = os.path.join(folder, f"benchmark_{stamp}{suffix}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ("" if r.get(k) is None else r[k]) for k in CSV_COLUMNS})
    print(f"\nSaved data -> {path}  ({len(rows)} rows)")
    return path


def print_summary_table(dataset, variants, dataset_sizes, rows):
    """Readable aligned table for one dataset (quick eyeball; full data is in the CSV)."""
    by = {(r["variant"], r["n"]): r for r in rows if r["dataset"] == dataset}

    def cell(v, width, prec=None):
        if v is None:
            return f"{'—':>{width}}"
        return f"{v:>{width}.{prec}f}" if prec is not None else f"{v:>{width}}"

    header = (f"{'variant':<26s} {'n':>6s} {'ms':>10s} {'restarts':>9s} "
              f"{'wasted':>8s} {'final_k':>8s} {'hull':>6s} {'outside':>8s} {'fails':>7s}")
    print(f"\n----- {dataset} -----")
    print(header)
    print("-" * len(header))
    for label, _ in variants:
        for n in dataset_sizes:
            r = by[(label, n)]
            print(
                f"{label:<26s} {n:>6d} {cell(r['avg_runtime_ms'], 10, 2)} "
                f"{cell(r['avg_restarts'], 9, 1)} {cell(r['avg_wasted_edges'], 8, 0)} "
                f"{cell(r['avg_final_k'], 8)} {cell(r['avg_hull_len'], 6)} "
                f"{cell(r['avg_points_outside'], 8, 1)} "
                f"{str(r['failures']) + '/' + str(r['num_runs']):>7s}"
            )


# -------------------------------------------------------------------------------
# EDIT THIS LIST to compare whatever you want.
#
# Each entry is (label, config-kwargs). Any subset of ConcaveHullConfig fields
# is accepted; everything else falls back to the dataclass default.
# -------------------------------------------------------------------------------
# k-scope comparison: restart baseline vs checkpoint with per_region vs global k.
# All bucketed (verified fastest); knn=scipy, k_growth=linear held constant.
# Every variant uses validate_final_hull="enforce", so all reported successes enclose
# every input point. Checkpoint variants recover excluded points by raising their
# starting k and retrying the checkpoint construction.
# Hypothesis: per_region k makes each region re-climb from initial_k, inflating work;
# global k shares one rising k across regions (keeping the trimmed prefix) — closer to
# restart and, on many-region (convex_hull) inputs, much cheaper.
VARIANTS = [
    ("restart · bucketed",
        dict(
            failure_strategy="restart",
            intersection_strategy="bucketed",
            validate_final_hull="enforce",
        )),
    ("ckpt extreme · per_region",
        dict(
            failure_strategy="checkpoint",
            checkpoint_strategy="extreme",
            checkpoint_k_scope="per_region",
            intersection_strategy="bucketed",
            validate_final_hull="enforce",
        )),
    ("ckpt extreme · global",
        dict(
            failure_strategy="checkpoint",
            checkpoint_strategy="extreme",
            checkpoint_k_scope="global",
            intersection_strategy="bucketed",
            validate_final_hull="enforce",
        )),
    ("ckpt convex_hull · per_region",
        dict(
            failure_strategy="checkpoint",
            checkpoint_strategy="convex_hull",
            checkpoint_k_scope="per_region",
            intersection_strategy="bucketed",
            validate_final_hull="enforce",
        )),
    ("ckpt convex_hull · global",
        dict(
            failure_strategy="checkpoint",
            checkpoint_strategy="convex_hull",
            checkpoint_k_scope="global",
            intersection_strategy="bucketed",
            validate_final_hull="enforce",
        )),
]

# Top end trimmed from 200000 -> 50000: with several datasets and the restart
# baseline, the largest synthetic sizes mostly hit the timeout (and leaked threads
# poison later timings). Raise it back once timeouts are run in killable subprocesses.
DATASET_SIZES = [100, 250, 500, 1000, 2500, 5000, 10000, 20000, 50000]
NUM_RUNS = 5
TIMEOUT_S = 30.0  # killable per-run guard; successful paper-scale runs finish in seconds

# -------------------------------------------------------------------------------
# Datasets to test. Each entry: (name, generator(n, seed) -> points).
#   - synthetic generators sweep the full DATASET_SIZES (scaling study).
#   - csv_dataset(...) real GIS sets run once at native size (no subsampling).
# Comment/uncomment to choose what runs; all rows land in one combined CSV.
# -------------------------------------------------------------------------------
DATASETS = [
    # Synthetic (scaling sweeps over DATASET_SIZES):
    ("unit_disk",    generate_unit_disk_points),                  # the original paper's test data
    ("star_8tips",   generate_star_points),                       # hard case: deep concavities
    # Real GIS sets — full set, native size, one run each:
    ("coast_redwood",  csv_dataset("coast_redwood_sightings.csv")),
    ("gray_wolf",      csv_dataset("gray_wolf_sightings.csv")),
    ("us_cities",      csv_dataset("us_mainland_cities.csv")),
    ("world_capitals", csv_dataset("world_capitals.csv")),
]


def sizes_for(generator):
    """Synthetic generators get the full n-sweep; real CSV datasets run once at
    their native size (no subsampling — see csv_dataset)."""
    native = getattr(generator, "native_size", None)
    if native is None:
        return DATASET_SIZES
    return [native]


def main():
    # Warmup: one untimed run so the first measured (variant, n) doesn't eat the
    # process startup tax (scipy/numpy import, KDTree class init, OS page cache).
    print("Warmup...", flush=True)
    ConfigurableConcaveHull().run(generate_unit_disk_points(200, seed=0), ConcaveHullConfig())

    all_rows = []
    for name, generator in DATASETS:
        sizes = sizes_for(generator)
        # Real GIS sets are fixed + deterministic: one run is enough (extra runs only
        # re-time identical work). Synthetic sets average NUM_RUNS seeds.
        is_real = getattr(generator, "native_size", None) is not None
        runs = 1 if is_real else NUM_RUNS
        print(
            f"\n=== Dataset: {name}  "
            f"({len(VARIANTS)} variants × {len(sizes)} sizes × {runs} run{'s' if runs != 1 else ''}) ===",
            flush=True,
        )
        sweep = run_sweep(VARIANTS, sizes, generator, num_runs=runs, timeout_s=TIMEOUT_S)
        rows = rows_from_sweep(name, VARIANTS, sizes, runs, *sweep)
        print_summary_table(name, VARIANTS, sizes, rows)
        all_rows.extend(rows)

    # One combined tidy CSV across all datasets (filter by the `dataset` column to chart).
    write_results_csv(all_rows)


if __name__ == "__main__":
    main()
