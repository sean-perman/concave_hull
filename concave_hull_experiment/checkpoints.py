"""Checkpoints — anchor points used by the checkpoint failure strategy.

The hull is structured as a sequence of regions between checkpoints. On
intersection failure, the algorithm trims back to the latest checkpoint at or
before the failed edge instead of restarting from scratch. Different regions
can grow their k independently.
"""
from dataclasses import dataclass

from .geometry import compute_angle, do_intersect, find_lowest_point
from .intersections import IntersectionIndex
from .knn import KNNIndex


Point = tuple[float, float]


def select_extreme_points(points: list[Point]) -> list[Point]:
    """Up to 4 cardinal extremes in CCW order, deduplicated, starting from min-y.

    Port of legacy/monolithic/seans_concavehull_4.py:440-462.
    """
    min_x_pt = min(points, key=lambda p: (p[0], p[1]))
    max_x_pt = max(points, key=lambda p: (p[0], -p[1]))
    min_y_pt = find_lowest_point(points)
    max_y_pt = max(points, key=lambda p: (p[1], p[0]))

    ordered = [min_y_pt, max_x_pt, max_y_pt, min_x_pt]
    seen: set[Point] = set()
    out: list[Point] = []
    for p in ordered:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            out.append(tuple(p))
    return out


def compute_convex_hull(points: list[Point]) -> list[Point]:
    """Convex hull via Andrew's monotone chain, CCW, starting from min-y, no closing duplicate.

    Port of legacy/monolithic/seans_concavehull_4.py:464-500.
    """
    pts = sorted({tuple(p) for p in points})
    if len(pts) <= 1:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    hull = lower[:-1] + upper[:-1]
    # Rotate so the lowest-y point is first (the algorithm's first_point).
    start = find_lowest_point(hull)
    idx = hull.index(start)
    return hull[idx:] + hull[:idx]


def select_checkpoints(points: list[Point], mode: str) -> list[Point]:
    if mode == "extreme":
        return select_extreme_points(points)
    if mode == "convex_hull":
        return compute_convex_hull(points)
    raise ValueError(f"unknown checkpoint mode: {mode!r}")


@dataclass
class RollbackResult:
    hull: list[Point]
    current: Point
    prev_angle: float
    step: int
    current_region: int
    last_checkpoint_index: int


def trim_to_checkpoint(
    hull: list[Point],
    knn: KNNIndex,
    edges: IntersectionIndex,
    candidates_sorted: list[Point],
    checkpoints: list[Point],
    checkpoint_set: set[Point],
    first_point: Point,
) -> RollbackResult:
    """Roll the hull back to the latest checkpoint at or before the failed edge.

    Identifies the failed edge by re-testing the *best* candidate (cPoints[0])
    against each hull edge from index 0; the earliest intersecting edge is the
    failure point. Trims hull to the latest checkpoint at or before that edge,
    re-adds trimmed points (except first_point) to the kNN pool, and removes
    trimmed edges from the intersection index.

    Caller is responsible for bumping region_k_values[current_region].
    Port of legacy/monolithic/seans_concavehull_4.py:515-579.
    """
    # 1. Identify the earliest hull edge that the best candidate would cross.
    best = candidates_sorted[0] if candidates_sorted else None
    earliest_edge_start = len(hull) - 2  # default: last edge
    if best is not None:
        for edge_idx in range(len(hull) - 1):
            if do_intersect(hull[-1], best, hull[edge_idx], hull[edge_idx + 1]):
                earliest_edge_start = edge_idx
                break

    # 2. Walk backward from that edge to find the latest checkpoint hull index.
    trim_to = 0
    for idx in range(max(earliest_edge_start, 0), -1, -1):
        if tuple(hull[idx]) in checkpoint_set:
            trim_to = idx
            break

    # 3. Slice. Restore trimmed points to kNN (except first_point) and trimmed
    #    edges to the intersection index.
    removed = hull[trim_to + 1:]
    new_hull = hull[: trim_to + 1]
    for pt in removed:
        if pt == first_point:
            continue
        knn.add(pt)
    # Edges removed: (hull[trim_to], hull[trim_to+1]), ..., (hull[-2], hull[-1]).
    for i in range(trim_to, len(hull) - 1):
        edges.remove_edge(hull[i], hull[i + 1])

    # 4. Recompute prev_angle and step.
    if len(new_hull) >= 2:
        prev_angle = compute_angle(new_hull[-1], new_hull[-2])
    else:
        prev_angle = 0.0
    new_step = len(new_hull) + 1
    new_current = new_hull[-1]

    # 5. Resolve which checkpoint index the trim point corresponds to.
    new_region = 0
    for ci, cp in enumerate(checkpoints):
        if tuple(cp) == tuple(new_current):
            new_region = ci
            break

    return RollbackResult(
        hull=new_hull,
        current=new_current,
        prev_angle=prev_angle,
        step=new_step,
        current_region=new_region,
        last_checkpoint_index=trim_to,
    )
