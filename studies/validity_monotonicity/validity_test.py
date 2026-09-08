"""Reproduce and search for non-monotone fixed-k validity.

A fixed k is valid when the Moreira-Santos walk closes without a dead end and
the resulting simple hull encloses every input point.  Monotone validity would
require that success at k implies success at every larger k.  The bundled
six-point set disproves that implication: k=3 succeeds, k=4 reaches a dead end,
and k=5 succeeds.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import random
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull
from concave_hull_experiment.geometry import points_outside_hull

Point = tuple[float, float]
HERE = Path(__file__).resolve().parent
DEFAULT_POINTS = HERE / "counterexample_points.csv"
DEFAULT_FIGURE = HERE / "counterexample.png"


@dataclass
class FixedKResult:
    k: int
    valid: bool
    closed: bool
    outside: int | None
    hull: list[Point] | None
    partial_hull: list[Point]


def load_points(path: Path) -> list[Point]:
    with path.open(newline="") as stream:
        return [
            (float(row["x"]), float(row["y"]))
            for row in csv.DictReader(stream)
        ]


def _cross(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def is_general_position(points: list[Point]) -> bool:
    """Reject collinear triples and kNN distance ties."""
    if any(_cross(*triple) == 0 for triple in itertools.combinations(points, 3)):
        return False
    for point in points:
        distances = [
            (point[0] - other[0]) ** 2 + (point[1] - other[1]) ** 2
            for other in points
            if other != point
        ]
        if len(distances) != len(set(distances)):
            return False
    return True


def run_fixed_k(points: list[Point], k: int, *, intersection: str = "naive") -> FixedKResult:
    config = ConcaveHullConfig(
        intersection_strategy=intersection,
        failure_strategy="restart",
        validate_final_hull="off",
    )
    states = []
    hull, _ = ConfigurableConcaveHull()._attempt(
        points, k, config, on_step=states.append
    )
    closed = hull is not None
    outside = points_outside_hull(points, hull) if hull is not None else None
    partial_hull = list(hull or (states[-1].hull if states else []))
    return FixedKResult(
        k=k,
        valid=closed and outside == 0,
        closed=closed,
        outside=outside,
        hull=hull,
        partial_hull=partial_hull,
    )


def sweep(points: list[Point], *, intersection: str = "naive") -> list[FixedKResult]:
    return [
        run_fixed_k(points, k, intersection=intersection)
        for k in range(3, len(set(points)))
    ]


def validity_reversals(results: list[FixedKResult]) -> list[tuple[FixedKResult, FixedKResult]]:
    return [
        (lower, higher)
        for lower, higher in zip(results, results[1:])
        if lower.valid and not higher.valid
    ]


def search(
    *, trials: int = 10_000, seed: int = 20_260_831, grid_max: int = 10
) -> tuple[list[Point], list[FixedKResult], int] | None:
    """Search general-position six-point subsets of an integer grid."""
    rng = random.Random(seed)
    grid = [(x, y) for x in range(grid_max + 1) for y in range(grid_max + 1)]
    for trial in range(trials):
        points = rng.sample(grid, 6)
        if not is_general_position(points):
            continue
        results = sweep(points)
        if validity_reversals(results):
            return points, results, trial
    return None


def make_figure(points: list[Point], results: list[FixedKResult], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = "ABCDEF"
    figure, axes = plt.subplots(1, len(results), figsize=(10.5, 3.5), sharex=True, sharey=True)
    for axis, result in zip(axes, results):
        path_points = result.hull or result.partial_hull
        if len(path_points) >= 2:
            axis.plot(
                [point[0] for point in path_points],
                [point[1] for point in path_points],
                "-o",
                color="tab:blue" if result.valid else "tab:red",
                linewidth=2,
                markersize=4,
            )
        axis.scatter(
            [point[0] for point in points],
            [point[1] for point in points],
            color="black",
            s=24,
            zorder=3,
        )
        for label, point in zip(labels, points):
            axis.annotate(label, point, xytext=(4, 4), textcoords="offset points")
        outcome = "valid" if result.valid else "dead end"
        axis.set_title(f"k = {result.k}: {outcome}")
        axis.set_aspect("equal", adjustable="box")
        axis.grid(alpha=0.2)
    figure.suptitle("Validity is not monotone in k")
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")


def print_results(results: list[FixedKResult]) -> None:
    for result in results:
        outcome = "valid" if result.valid else ("closed but excludes points" if result.closed else "dead end")
        print(f"k={result.k}: {outcome}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", action="store_true", help="repeat the seeded integer-grid search")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_831)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()

    if args.search:
        found = search(trials=args.trials, seed=args.seed)
        if found is None:
            raise SystemExit(f"no counterexample found in {args.trials} trials")
        points, results, trial = found
        print(f"counterexample found at trial {trial}: {points}")
    else:
        points = load_points(DEFAULT_POINTS)
        results = sweep(points)

    if not is_general_position(points):
        raise SystemExit("point set is degenerate")
    reversals = validity_reversals(results)
    if not reversals:
        raise SystemExit("point set does not contain a valid-to-invalid transition")

    print_results(results)
    make_figure(points, results, args.figure)
    print(f"figure: {args.figure}")


if __name__ == "__main__":
    main()
