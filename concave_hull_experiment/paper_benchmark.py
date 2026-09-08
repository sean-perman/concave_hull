"""Focused, reproducible benchmark for the spatial-bucketing paper claim.

This benchmark varies exactly one feature: the intersection backend.  The
original restart algorithm, linear k growth, initial k=3, SciPy cKDTree, and
final containment enforcement are held constant.

Each trial runs naive and bucketed construction on the same points in one
isolated subprocess.  Dependencies are warmed before timing, execution order
alternates, every raw observation is retained, and the paired hull results must
be identical. Exact-predicate calls are collected in a separate untimed pass so
the counter cannot bias the runtime comparison. Outputs are written to
results/YYYY-MM-DD/:

    paper_benchmark_<time>_raw.csv
    paper_benchmark_<time>_summary.csv
    paper_benchmark_<time>_metadata.json
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


ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("naive", "bucketed")
DEFAULT_SIZES = (1_000, 5_000, 10_000, 50_000)
SYNTHETIC_DATASETS = (
    ("unit_disk", generate_unit_disk_points),
    ("star_8tips", generate_star_points),
)
REAL_DATASETS = (
    ("us_cities", "us_mainland_cities.csv"),
    ("gray_wolf", "gray_wolf_sightings.csv"),
    ("coast_redwood", "coast_redwood_sightings.csv"),
    ("world_capitals", "world_capitals.csv"),
)


def paper_config(strategy: str) -> ConcaveHullConfig:
    return ConcaveHullConfig(
        initial_k=3,
        knn_backend="scipy",
        k_growth_strategy="linear",
        failure_strategy="restart",
        checkpoint_strategy="none",
        intersection_strategy=strategy,
        intersection_bucket_size=0.0,
        validate_final_hull="enforce",
    )


def _warm_dependencies(points: list[tuple[float, float]]) -> None:
    """Load lazy SciPy/Shapely paths before the measured runs."""
    warm = points[: min(200, len(points))]
    if len(warm) < 3:
        return
    for strategy in STRATEGIES:
        ConfigurableConcaveHull().run(warm, paper_config(strategy))


def _timed_run(
    points: list[tuple[float, float]], strategy: str
) -> tuple[HullResult, float]:
    gc.collect()
    started = time.perf_counter()
    result = ConfigurableConcaveHull().run(points, paper_config(strategy))
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return result, elapsed_ms


def _counted_run(
    points: list[tuple[float, float]], strategy: str
) -> tuple[HullResult, int]:
    exact_calls = 0
    original = intersections_module.do_intersect

    def counted_do_intersect(*args):
        nonlocal exact_calls
        exact_calls += 1
        return original(*args)

    intersections_module.do_intersect = counted_do_intersect
    try:
        result = ConfigurableConcaveHull().run(points, paper_config(strategy))
    finally:
        intersections_module.do_intersect = original
    return result, exact_calls


def run_pair_in_process(
    points: list[tuple[float, float]], order: tuple[str, str]
) -> dict[str, dict]:
    _warm_dependencies(points)
    observations: dict[str, dict] = {}
    for strategy in order:
        result, elapsed_ms = _timed_run(points, strategy)
        observations[strategy] = {
            "result": result,
            "elapsed_ms": elapsed_ms,
        }
    # Count in separate, untimed runs. Instrumenting every exact predicate call
    # inside the timer would penalize the naive backend much more heavily.
    for strategy in order:
        counted_result, exact_calls = _counted_run(points, strategy)
        if comparable_result(counted_result) != comparable_result(
            observations[strategy]["result"]
        ):
            raise AssertionError(f"timed/counted result mismatch for {strategy}")
        observations[strategy]["exact_intersection_calls"] = exact_calls
    return observations


def _pair_worker(points, order, output_queue) -> None:
    try:
        output_queue.put(("ok", run_pair_in_process(points, order)))
    except Exception as exc:
        output_queue.put(("error", type(exc).__name__, str(exc)))


def run_pair(
    points: list[tuple[float, float]],
    order: tuple[str, str],
    timeout_s: float,
) -> dict[str, dict]:
    context = multiprocessing.get_context("spawn")
    output_queue = context.Queue()
    process = context.Process(target=_pair_worker, args=(points, order, output_queue))
    process.start()
    process.join(timeout_s)

    if process.is_alive():
        process.terminate()
        process.join()
        output_queue.close()
        raise TimeoutError(f"paired run exceeded {timeout_s:.0f}s")

    try:
        message = output_queue.get(timeout=2.0)
    except queue.Empty as exc:
        raise RuntimeError(f"benchmark worker exited {process.exitcode}") from exc
    finally:
        output_queue.close()

    if message[0] == "error":
        raise RuntimeError(f"worker {message[1]}: {message[2]}")
    return message[1]


def comparable_result(result: HullResult) -> tuple:
    return (
        result.success,
        result.hull,
        result.final_k,
        result.points_outside,
        result.restarts,
        result.total_restart_edges,
    )


def paired_rows(
    *, dataset: str, points: list[tuple[float, float]], trial: int,
    seed: int | None, timeout_s: float,
) -> list[dict]:
    order = STRATEGIES if trial % 2 == 0 else tuple(reversed(STRATEGIES))
    observations = run_pair(points, order, timeout_s)
    naive = observations["naive"]["result"]
    bucketed = observations["bucketed"]["result"]
    identical = comparable_result(naive) == comparable_result(bucketed)
    if not identical:
        raise AssertionError(
            f"naive/bucketed mismatch for {dataset}, n={len(points)}, trial={trial}"
        )
    if not naive.success or naive.points_outside != 0:
        raise AssertionError(
            f"invalid final hull for {dataset}, n={len(points)}, trial={trial}"
        )

    common = {
        "dataset": dataset,
        "n": len(points),
        "unique_n": len(set(points)),
        "trial": trial,
        "seed": "" if seed is None else seed,
        "order": "-then-".join(order),
        "auto_cell_size": auto_cell_size(points),
        "identical_pair": identical,
    }
    rows = []
    for strategy in STRATEGIES:
        observation = observations[strategy]
        result = observation["result"]
        rows.append({
            **common,
            "strategy": strategy,
            "runtime_ms": observation["elapsed_ms"],
            "exact_intersection_calls": observation["exact_intersection_calls"],
            "success": result.success,
            "final_k": result.final_k,
            "hull_len": len(result.hull),
            "points_outside": result.points_outside,
            "restarts": result.restarts,
            "wasted_edges": result.total_restart_edges,
        })
    return rows


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize(raw_rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in raw_rows:
        groups.setdefault((row["dataset"], row["n"]), []).append(row)

    summary = []
    for (dataset, n), rows in sorted(groups.items()):
        by_strategy = {
            strategy: [row for row in rows if row["strategy"] == strategy]
            for strategy in STRATEGIES
        }
        naive_times = [row["runtime_ms"] for row in by_strategy["naive"]]
        bucket_times = [row["runtime_ms"] for row in by_strategy["bucketed"]]
        naive_calls = [row["exact_intersection_calls"] for row in by_strategy["naive"]]
        bucket_calls = [row["exact_intersection_calls"] for row in by_strategy["bucketed"]]
        naive_by_trial = {row["trial"]: row for row in by_strategy["naive"]}
        bucket_by_trial = {row["trial"]: row for row in by_strategy["bucketed"]}
        speedups = [
            naive_by_trial[t]["runtime_ms"] / bucket_by_trial[t]["runtime_ms"]
            for t in sorted(naive_by_trial)
        ]
        call_ratios = [
            naive_by_trial[t]["exact_intersection_calls"]
            / max(bucket_by_trial[t]["exact_intersection_calls"], 1)
            for t in sorted(naive_by_trial)
        ]

        def stats(values):
            return {
                "mean": statistics.fmean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "q1": percentile(values, 0.25),
                "q3": percentile(values, 0.75),
            }

        ns = stats(naive_times)
        bs = stats(bucket_times)
        summary.append({
            "dataset": dataset,
            "n": n,
            "trials": len(speedups),
            "naive_mean_ms": ns["mean"],
            "naive_median_ms": ns["median"],
            "naive_stdev_ms": ns["stdev"],
            "naive_q1_ms": ns["q1"],
            "naive_q3_ms": ns["q3"],
            "bucketed_mean_ms": bs["mean"],
            "bucketed_median_ms": bs["median"],
            "bucketed_stdev_ms": bs["stdev"],
            "bucketed_q1_ms": bs["q1"],
            "bucketed_q3_ms": bs["q3"],
            "median_paired_speedup": statistics.median(speedups),
            "median_naive_exact_calls": statistics.median(naive_calls),
            "median_bucketed_exact_calls": statistics.median(bucket_calls),
            "median_exact_call_reduction": statistics.median(call_ratios),
            "all_pairs_identical": all(row["identical_pair"] for row in rows),
        })
    return summary


def source_hash() -> str:
    digest = hashlib.sha256()
    for relative in (
        "concave_hull_experiment/concave_hull.py",
        "concave_hull_experiment/config.py",
        "concave_hull_experiment/geometry.py",
        "concave_hull_experiment/intersections.py",
        "concave_hull_experiment/knn.py",
        "concave_hull_experiment/paper_benchmark.py",
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


def write_outputs(raw_rows: list[dict], output_dir: Path, arguments: dict) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H-%M-%S")
    prefix = output_dir / f"paper_benchmark_{stamp}"
    raw_path = Path(f"{prefix}_raw.csv")
    summary_path = Path(f"{prefix}_summary.csv")
    metadata_path = Path(f"{prefix}_metadata.json")

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
        "arguments": arguments,
        "held_constant": {
            "initial_k": 3,
            "knn_backend": "scipy",
            "k_growth_strategy": "linear",
            "failure_strategy": "restart",
            "validate_final_hull": "enforce",
            "intersection_bucket_size": "auto: extent/sqrt(n)",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return raw_path, summary_path, metadata_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_SIZES))
    parser.add_argument("--synthetic-trials", type=int, default=10)
    parser.add_argument("--real-trials", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    if args.smoke:
        args.sizes = [250, 1_000]
        args.synthetic_trials = 2
        args.real_trials = 1

    output_dir = args.output_dir or ROOT / "results" / datetime.now().strftime("%Y-%m-%d")
    jobs = []
    for dataset, generator in SYNTHETIC_DATASETS:
        for n in args.sizes:
            for trial in range(args.synthetic_trials):
                jobs.append((dataset, generator(n, seed=trial), trial, trial))
    for dataset, filename in REAL_DATASETS:
        points = load_csv_points(filename)
        for trial in range(args.real_trials):
            jobs.append((dataset, points, trial, None))

    raw_rows = []
    for index, (dataset, points, trial, seed) in enumerate(jobs, 1):
        print(
            f"[{index:>3}/{len(jobs)}] {dataset:<15} n={len(points):>6} "
            f"trial={trial + 1}",
            flush=True,
        )
        raw_rows.extend(
            paired_rows(
                dataset=dataset,
                points=points,
                trial=trial,
                seed=seed,
                timeout_s=args.timeout,
            )
        )
        naive = raw_rows[-2]
        bucketed = raw_rows[-1]
        print(
            f"      naive={naive['runtime_ms']:.2f}ms "
            f"bucketed={bucketed['runtime_ms']:.2f}ms "
            f"speedup={naive['runtime_ms'] / bucketed['runtime_ms']:.2f}x "
            f"calls={naive['exact_intersection_calls']}/"
            f"{bucketed['exact_intersection_calls']}",
            flush=True,
        )

    paths = write_outputs(raw_rows, output_dir, vars(args))
    print("RAW", paths[0], flush=True)
    print("SUMMARY", paths[1], flush=True)
    print("METADATA", paths[2], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
