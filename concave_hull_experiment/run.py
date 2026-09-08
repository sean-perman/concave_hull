"""Quick demo: compare k-growth strategies and failure strategies on the same point set.

Run either way:
  python -m concave_hull_experiment.run
  python concave_hull_experiment/run.py
"""
import time

import numpy as np

# Allow `python run.py` (no package context) by adding the parent dir to sys.path.
if __package__ in (None, ""):
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from concave_hull_experiment.concave_hull import ConfigurableConcaveHull
    from concave_hull_experiment.config import ConcaveHullConfig
else:
    from .concave_hull import ConfigurableConcaveHull
    from .config import ConcaveHullConfig


def make_unit_disk_points(n: int = 200, seed: int = 42) -> list[tuple[float, float]]:
    """Uniform points inside a unit disk — the classic kNN-concave-hull test case."""
    rng = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(-1.0, 1.0, size=2)
        if x * x + y * y <= 1.0:
            pts.append((float(x), float(y)))
    return pts


def run_one(points, *, k_strategy="linear", failure="restart", checkpoint="none",
            intersection="naive", validate="report", rate=2.0):
    cfg = ConcaveHullConfig(
        initial_k=3,
        knn_backend="scipy",
        k_growth_strategy=k_strategy,
        k_growth_rate=rate,
        failure_strategy=failure,
        checkpoint_strategy=checkpoint,
        intersection_strategy=intersection,
        validate_final_hull=validate,
    )
    t0 = time.perf_counter()
    result = ConfigurableConcaveHull().run(points, cfg)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, elapsed_ms


def _outside_str(n):
    return "n/a" if n is None else str(n)


def main():
    points = make_unit_disk_points(n=10000, seed=42)

    print(f"Input: {len(points)} points\n")
    print(f"{'label':<48} {'success':<8} {'final_k':<8} {'hull_len':<10} {'outside':<8} {'time_ms':<10}")
    print("-" * 96)

    variants = [
        ("linear / restart / naive (report)",      dict(k_strategy="linear", failure="restart",  intersection="naive",    validate="report")),
        ("linear / restart / naive (enforce)",     dict(k_strategy="linear", failure="restart",  intersection="naive",    validate="enforce")),
        ("linear / restart / bucketed (report)",   dict(k_strategy="linear", failure="restart",  intersection="bucketed", validate="report")),
        ("linear / restart / bucketed (enforce)",  dict(k_strategy="linear", failure="restart",  intersection="bucketed", validate="enforce")),
        ("checkpoint(extreme) / naive (report)",   dict(k_strategy="linear", failure="checkpoint", checkpoint="extreme",  intersection="naive",    validate="report")),
        ("checkpoint(extreme) / bucketed (report)",dict(k_strategy="linear", failure="checkpoint", checkpoint="extreme",  intersection="bucketed", validate="report")),
        ("checkpoint(extreme) / bucketed (enforce)",
         dict(k_strategy="linear", failure="checkpoint", checkpoint="extreme",
              intersection="bucketed", validate="enforce")),
    ]

    for label, kwargs in variants:
        result, elapsed_ms = run_one(points, **kwargs)
        print(
            f"{label:<48} {str(result.success):<8} "
            f"{result.final_k:<8} {len(result.hull):<10} "
            f"{_outside_str(result.points_outside):<8} {elapsed_ms:<10.2f}"
        )

    print("\nfinal_k for checkpoint variants is max(region_k_values).")
    print("outside = number of input points lying strictly outside the closed hull (None = not validated).")


if __name__ == "__main__":
    main()
