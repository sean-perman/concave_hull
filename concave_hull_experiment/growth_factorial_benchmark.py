"""Publication benchmark for k-growth and spatial bucketing.

The experiment is a 2x2 factorial design:

    linear growth    x naive intersection   (original baseline)
    linear growth    x bucketed intersection
    geometric growth x naive intersection
    geometric growth x bucketed intersection

Failure recovery, initial k, nearest-neighbour backend, containment validation,
and input data are held constant.  All four variants run on the same point set
inside one isolated subprocess, with execution order rotated across trials.
Exact-intersection counts are collected in separate untimed runs.

Outputs are written to results/YYYY-MM-DD/:

    growth_factorial_<time>_raw.csv
    growth_factorial_<time>_summary.csv
    growth_factorial_<time>_metadata.json
    growth_factorial_<time>_paper_table.tex
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import multiprocessing
import platform
import queue
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from . import intersections as intersections_module
from .benchmark import (
    generate_star_points,
    generate_unit_disk_points,
    load_csv_points,
)
from .concave_hull import ConfigurableConcaveHull, HullResult
from .config import ConcaveHullConfig
from .intersections import auto_cell_size
from .k_growth import ExponentialKGrowth, LinearKGrowth
from .paper_benchmark import comparable_result, percentile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RATE = 2.0
DEFAULT_SIZES = (1_000, 5_000, 10_000, 50_000)

# key, growth strategy, intersection strategy, paper label
VARIANTS = (
    ("linear_naive", "linear", "naive", "Original"),
    ("linear_bucketed", "linear", "bucketed", "Bucketing"),
    ("geometric_naive", "exponential", "naive", "Geometric"),
    ("geometric_bucketed", "exponential", "bucketed", "Combined"),
)
VARIANT_KEYS = tuple(variant[0] for variant in VARIANTS)
VARIANT_BY_KEY = {variant[0]: variant for variant in VARIANTS}

SYNTHETIC_DATASETS = {
    "unit_disk": generate_unit_disk_points,
    "star_8tips": generate_star_points,
}
REAL_DATASETS = {
    "us_cities": "us_mainland_cities.csv",
    "gray_wolf": "gray_wolf_sightings.csv",
    "coast_redwood": "coast_redwood_sightings.csv",
}
OPTIONAL_DATASETS = {
    "world_capitals": "world_capitals.csv",
}


def factorial_config(variant_key: str, *, rate: float = DEFAULT_RATE) -> ConcaveHullConfig:
    _, growth, intersection, _ = VARIANT_BY_KEY[variant_key]
    return ConcaveHullConfig(
        initial_k=3,
        knn_backend="scipy",
        k_growth_strategy=growth,
        k_growth_rate=rate,
        failure_strategy="restart",
        checkpoint_strategy="none",
        intersection_strategy=intersection,
        intersection_bucket_size=0.0,
        validate_final_hull="enforce",
    )


def order_for_trial(trial: int) -> tuple[str, ...]:
    """Rotate and reverse order so timing position is balanced over eight trials."""
    base = VARIANT_KEYS if (trial // 4) % 2 == 0 else tuple(reversed(VARIANT_KEYS))
    shift = trial % 4
    return base[shift:] + base[:shift]


def attempted_k_values(
    result: HullResult,
    *,
    n: int,
    growth_strategy: str,
    rate: float = DEFAULT_RATE,
    initial_k: int = 3,
) -> list[int]:
    """Reconstruct the forward schedule through the result's final attempted k."""
    growth = (
        LinearKGrowth()
        if growth_strategy == "linear"
        else ExponentialKGrowth(rate=rate)
    )
    k = growth.initial_k(n, initial_k)
    values: list[int] = []
    while k is not None and k < n:
        values.append(k)
        if k == result.final_k:
            break
        k = growth.next_k(k, succeeded=False, n=n)
    if not values or values[-1] != result.final_k:
        raise AssertionError(
            f"final k={result.final_k} is not on {growth_strategy} schedule {values}"
        )
    return values


def polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    return abs(
        sum(
            x1 * y2 - x2 * y1
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
        )
    ) / 2.0


def convex_hull_area(points: list[tuple[float, float]]) -> float:
    from shapely.geometry import MultiPoint

    return float(MultiPoint(points).convex_hull.area)


def _warm_dependencies(points: list[tuple[float, float]], rate: float) -> None:
    warm = points[: min(200, len(points))]
    if len(warm) < 3:
        return
    for variant_key in VARIANT_KEYS:
        ConfigurableConcaveHull().run(warm, factorial_config(variant_key, rate=rate))
    convex_hull_area(warm)


def _timed_run(
    points: list[tuple[float, float]], variant_key: str, rate: float
) -> tuple[HullResult, float]:
    gc.collect()
    started = time.perf_counter()
    result = ConfigurableConcaveHull().run(
        points, factorial_config(variant_key, rate=rate)
    )
    return result, (time.perf_counter() - started) * 1000.0


def _counted_run(
    points: list[tuple[float, float]], variant_key: str, rate: float
) -> tuple[HullResult, int]:
    exact_calls = 0
    original = intersections_module.do_intersect

    def counted_do_intersect(*args):
        nonlocal exact_calls
        exact_calls += 1
        return original(*args)

    intersections_module.do_intersect = counted_do_intersect
    try:
        result = ConfigurableConcaveHull().run(
            points, factorial_config(variant_key, rate=rate)
        )
    finally:
        intersections_module.do_intersect = original
    return result, exact_calls


def run_factorial_in_process(
    points: list[tuple[float, float]],
    order: tuple[str, ...],
    *,
    rate: float = DEFAULT_RATE,
) -> dict[str, dict]:
    if set(order) != set(VARIANT_KEYS) or len(order) != len(VARIANT_KEYS):
        raise ValueError("order must contain each factorial variant exactly once")
    _warm_dependencies(points, rate)
    observations: dict[str, dict] = {}
    for variant_key in order:
        result, elapsed_ms = _timed_run(points, variant_key, rate)
        observations[variant_key] = {"result": result, "elapsed_ms": elapsed_ms}

    # Counting is deliberately outside the timed pass because the callback cost
    # would disproportionately penalize the naive intersection backend.
    for variant_key in order:
        counted_result, exact_calls = _counted_run(points, variant_key, rate)
        if comparable_result(counted_result) != comparable_result(
            observations[variant_key]["result"]
        ):
            raise AssertionError(f"timed/counted mismatch for {variant_key}")
        observations[variant_key]["exact_intersection_calls"] = exact_calls
    return observations


def _worker(points, order, rate, output_queue) -> None:
    try:
        output_queue.put(("ok", run_factorial_in_process(points, order, rate=rate)))
    except Exception as exc:
        output_queue.put(("error", type(exc).__name__, str(exc)))


def run_factorial(
    points: list[tuple[float, float]],
    order: tuple[str, ...],
    *,
    rate: float,
    timeout_s: float,
) -> dict[str, dict]:
    context = multiprocessing.get_context("spawn")
    output_queue = context.Queue()
    process = context.Process(target=_worker, args=(points, order, rate, output_queue))
    process.start()
    process.join(timeout_s)

    if process.is_alive():
        process.terminate()
        process.join()
        output_queue.close()
        raise TimeoutError(f"factorial run exceeded {timeout_s:.0f}s")

    try:
        message = output_queue.get(timeout=2.0)
    except queue.Empty as exc:
        raise RuntimeError(f"benchmark worker exited {process.exitcode}") from exc
    finally:
        output_queue.close()

    if message[0] == "error":
        raise RuntimeError(f"worker {message[1]}: {message[2]}")
    return message[1]


def factorial_rows(
    *,
    dataset: str,
    points: list[tuple[float, float]],
    trial: int,
    seed: int | None,
    rate: float,
    timeout_s: float,
) -> list[dict]:
    order = order_for_trial(trial)
    observations = run_factorial(points, order, rate=rate, timeout_s=timeout_s)

    # Intersection indexing must be behavior-preserving within each growth schedule.
    for growth in ("linear", "geometric"):
        naive = observations[f"{growth}_naive"]["result"]
        bucketed = observations[f"{growth}_bucketed"]["result"]
        if comparable_result(naive) != comparable_result(bucketed):
            raise AssertionError(
                f"naive/bucketed mismatch for {growth}, {dataset}, "
                f"n={len(points)}, trial={trial}"
            )

    for variant_key in VARIANT_KEYS:
        result = observations[variant_key]["result"]
        if not result.success or result.points_outside != 0:
            raise AssertionError(
                f"invalid {variant_key} hull for {dataset}, "
                f"n={len(points)}, trial={trial}"
            )

    convex_area = convex_hull_area(points)
    linear_hulls = {
        "naive": observations["linear_naive"]["result"].hull,
        "bucketed": observations["linear_bucketed"]["result"].hull,
    }
    common = {
        "dataset": dataset,
        "n": len(points),
        "unique_n": len(set(points)),
        "trial": trial,
        "seed": "" if seed is None else seed,
        "order": ";".join(order),
        "growth_rate": rate,
        "auto_cell_size": auto_cell_size(points),
    }

    rows = []
    for variant_key, growth_strategy, intersection, label in VARIANTS:
        observation = observations[variant_key]
        result = observation["result"]
        values = attempted_k_values(
            result,
            n=len(set(points)),
            growth_strategy=growth_strategy,
            rate=rate,
        )
        if len(values) != result.restarts + 1:
            raise AssertionError(
                f"attempt schedule {values} disagrees with restarts={result.restarts}"
            )
        area = polygon_area(result.hull)
        rows.append({
            **common,
            "variant": variant_key,
            "paper_label": label,
            "k_growth": "geometric" if growth_strategy == "exponential" else "linear",
            "intersection": intersection,
            "runtime_ms": observation["elapsed_ms"],
            "exact_intersection_calls": observation["exact_intersection_calls"],
            "success": result.success,
            "final_k": result.final_k,
            "attempts": len(values),
            "attempted_ks": ";".join(str(value) for value in values),
            "sum_attempted_k": sum(values),
            "hull_len": len(result.hull),
            "hull_area": area,
            "convex_hull_area": convex_area,
            "area_ratio": area / convex_area if convex_area else 0.0,
            "points_outside": result.points_outside,
            "restarts": result.restarts,
            "wasted_edges": result.total_restart_edges,
            "same_as_linear_same_intersection": (
                result.hull == linear_hulls[intersection]
            ),
            "same_intersection_pair": True,
        })
    return rows


def _stats(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
    }


def summarize(raw_rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in raw_rows:
        groups.setdefault((row["dataset"], row["n"]), []).append(row)

    summaries = []
    for (dataset, n), rows in sorted(groups.items()):
        by_variant = {
            variant: [row for row in rows if row["variant"] == variant]
            for variant in VARIANT_KEYS
        }
        trials = sorted({row["trial"] for row in rows})
        by_trial = {
            trial: {
                row["variant"]: row for row in rows if row["trial"] == trial
            }
            for trial in trials
        }
        if any(set(values) != set(VARIANT_KEYS) for values in by_trial.values()):
            raise ValueError(f"incomplete factorial rows for {dataset}, n={n}")

        summary: dict[str, object] = {
            "dataset": dataset,
            "n": n,
            "trials": len(trials),
        }
        for variant in VARIANT_KEYS:
            variant_rows = by_variant[variant]
            timing = _stats([row["runtime_ms"] for row in variant_rows])
            for stat_name, value in timing.items():
                summary[f"{variant}_{stat_name}_ms"] = value
            for field in (
                "attempts",
                "sum_attempted_k",
                "restarts",
                "wasted_edges",
                "final_k",
                "area_ratio",
                "exact_intersection_calls",
            ):
                summary[f"{variant}_median_{field}"] = statistics.median(
                    row[field] for row in variant_rows
                )

        def median_ratio(numerator: str, denominator: str, field: str) -> float:
            return statistics.median(
                by_trial[trial][numerator][field]
                / max(by_trial[trial][denominator][field], 1e-12)
                for trial in trials
            )

        summary.update({
            "median_linear_bucketing_speedup": median_ratio(
                "linear_naive", "linear_bucketed", "runtime_ms"
            ),
            "median_geometric_bucketing_speedup": median_ratio(
                "geometric_naive", "geometric_bucketed", "runtime_ms"
            ),
            "median_geometric_speedup_naive": median_ratio(
                "linear_naive", "geometric_naive", "runtime_ms"
            ),
            "median_geometric_speedup_bucketed": median_ratio(
                "linear_bucketed", "geometric_bucketed", "runtime_ms"
            ),
            "median_combined_speedup_vs_original": median_ratio(
                "linear_naive", "geometric_bucketed", "runtime_ms"
            ),
            "median_linear_exact_call_reduction": median_ratio(
                "linear_naive", "linear_bucketed", "exact_intersection_calls"
            ),
            "median_geometric_exact_call_reduction": median_ratio(
                "geometric_naive", "geometric_bucketed", "exact_intersection_calls"
            ),
            "geometric_matches_linear_fraction": statistics.fmean(
                float(by_trial[trial]["geometric_naive"]["same_as_linear_same_intersection"])
                for trial in trials
            ),
            "all_intersection_pairs_identical": all(
                row["same_intersection_pair"] for row in rows
            ),
            "all_outputs_valid": all(
                row["success"] and row["points_outside"] == 0 for row in rows
            ),
        })
        summaries.append(summary)
    return summaries


def source_hash() -> str:
    digest = hashlib.sha256()
    for relative in (
        "concave_hull_experiment/concave_hull.py",
        "concave_hull_experiment/config.py",
        "concave_hull_experiment/geometry.py",
        "concave_hull_experiment/intersections.py",
        "concave_hull_experiment/k_growth.py",
        "concave_hull_experiment/knn.py",
        "concave_hull_experiment/growth_factorial_benchmark.py",
    ):
        digest.update(relative.encode())
        digest.update((ROOT / relative).read_bytes())
    return digest.hexdigest()


def dependency_versions() -> dict[str, str]:
    import scipy
    import shapely

    return {
        "python": sys.version.replace("\n", " "),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "shapely": shapely.__version__,
    }


def _format_ms(value: float) -> str:
    return f"{value:.2f}" if value < 100 else f"{value:.1f}"


def latex_table(summary_rows: list[dict]) -> str:
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Two-factor comparison of linear (L) and geometric (G) $k$-growth with naive (N) and bucketed (B) intersection checking. Values are medians. Attempts include the successful attempt; $\rho$ is hull area divided by convex-hull area.}",
        r"\label{tab:growth-factorial}",
        r"\small",
        r"\begin{tabular}{lrrrrrrrrrrr}",
        r"\toprule",
        r"& & \multicolumn{4}{c}{Runtime (ms)} & \multicolumn{2}{c}{Attempts} & \multicolumn{2}{c}{Final $k$} & \multicolumn{2}{c}{$\rho$} \\",
        r"\cmidrule(lr){3-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}",
        r"Dataset & $n$ & L/N & L/B & G/N & G/B & L & G & L & G & L & G \\",
        r"\midrule",
    ]
    labels = {
        "unit_disk": "Unit disk",
        "star_8tips": "Eight-tip star",
        "us_cities": "U.S. cities",
        "gray_wolf": "Gray wolf",
        "coast_redwood": "Coast redwood",
        "world_capitals": "World capitals",
    }
    for row in summary_rows:
        lines.append(
            "{} & {:,} & {} & {} & {} & {} & {:.1f} & {:.1f} & {:.1f} & {:.1f} & {:.3f} & {:.3f} \\\\".format(
                labels.get(row["dataset"], str(row["dataset"]).replace("_", r"\_")),
                row["n"],
                _format_ms(row["linear_naive_median_ms"]),
                _format_ms(row["linear_bucketed_median_ms"]),
                _format_ms(row["geometric_naive_median_ms"]),
                _format_ms(row["geometric_bucketed_median_ms"]),
                row["linear_naive_median_attempts"],
                row["geometric_naive_median_attempts"],
                row["linear_naive_median_final_k"],
                row["geometric_naive_median_final_k"],
                row["linear_naive_median_area_ratio"],
                row["geometric_naive_median_area_ratio"],
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    return "\n".join(lines)


def write_outputs(
    raw_rows: list[dict], output_dir: Path, arguments: dict
) -> tuple[Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H-%M-%S")
    prefix = output_dir / f"growth_factorial_{stamp}"
    raw_path = Path(f"{prefix}_raw.csv")
    summary_path = Path(f"{prefix}_summary.csv")
    metadata_path = Path(f"{prefix}_metadata.json")
    table_path = Path(f"{prefix}_paper_table.tex")

    with raw_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw_rows[0]))
        writer.writeheader()
        writer.writerows(raw_rows)

    summary_rows = summarize(raw_rows)
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    metadata = {
        "created": datetime.now().astimezone().isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "source_sha256": source_hash(),
        "dependencies": dependency_versions(),
        "arguments": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in arguments.items()
        },
        "factorial_axes": {
            "k_growth": ["linear", "geometric"],
            "intersection": ["naive", "bucketed"],
        },
        "held_constant": {
            "initial_k": 3,
            "knn_backend": "scipy",
            "failure_strategy": "restart",
            "validate_final_hull": "enforce",
            "intersection_bucket_size": "auto: extent/sqrt(n)",
        },
        "interpretation_guardrail": (
            "Naive and bucketed outputs must match within a growth schedule. "
            "Linear and geometric growth may return different valid hulls."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    table_path.write_text(latex_table(summary_rows))
    return raw_path, summary_path, metadata_path, table_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_SIZES))
    parser.add_argument("--synthetic-trials", type=int, default=10)
    parser.add_argument("--real-trials", type=int, default=10)
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--datasets", nargs="+")
    parser.add_argument("--include-world-capitals", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    if args.rate <= 1.0:
        parser.error("--rate must be greater than 1")

    available = {**SYNTHETIC_DATASETS, **REAL_DATASETS}
    if args.include_world_capitals:
        available.update(OPTIONAL_DATASETS)
    selected = list(available) if args.datasets is None else args.datasets
    unknown = sorted(set(selected) - set(available))
    if unknown:
        parser.error(f"unknown or unavailable datasets: {', '.join(unknown)}")

    if args.smoke:
        args.sizes = [250]
        args.synthetic_trials = 1
        args.real_trials = 0
        if args.datasets is None:
            selected = list(SYNTHETIC_DATASETS)

    output_dir = args.output_dir or ROOT / "results" / datetime.now().strftime("%Y-%m-%d")
    jobs = []
    for dataset, generator in SYNTHETIC_DATASETS.items():
        if dataset not in selected:
            continue
        for n in args.sizes:
            for trial in range(args.synthetic_trials):
                jobs.append((dataset, generator(n, seed=trial), trial, trial))
    real_sources = {**REAL_DATASETS, **OPTIONAL_DATASETS}
    for dataset, filename in real_sources.items():
        if dataset not in selected:
            continue
        points = load_csv_points(filename)
        for trial in range(args.real_trials):
            jobs.append((dataset, points, trial, None))
    if not jobs:
        parser.error("selection produced no benchmark jobs")

    raw_rows = []
    for index, (dataset, points, trial, seed) in enumerate(jobs, 1):
        print(
            f"[{index:>3}/{len(jobs)}] {dataset:<15} n={len(points):>6} "
            f"trial={trial + 1}",
            flush=True,
        )
        new_rows = factorial_rows(
            dataset=dataset,
            points=points,
            trial=trial,
            seed=seed,
            rate=args.rate,
            timeout_s=args.timeout,
        )
        raw_rows.extend(new_rows)
        row_by_variant = {row["variant"]: row for row in new_rows}
        print(
            "      "
            + " ".join(
                f"{key}={row_by_variant[key]['runtime_ms']:.2f}ms"
                for key in VARIANT_KEYS
            ),
            flush=True,
        )

    arguments = vars(args) | {"selected_datasets": selected}
    paths = write_outputs(raw_rows, output_dir, arguments)
    for label, path in zip(("RAW", "SUMMARY", "METADATA", "PAPER_TABLE"), paths):
        print(label, path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
