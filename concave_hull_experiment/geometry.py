"""Pure geometry helpers extracted from concavehull.py."""
import math


Point = tuple[float, float]


def find_lowest_point(points: list[Point]) -> Point:
    """Lowest y; ties broken by largest x."""
    return min(points, key=lambda p: (p[1], -p[0]))


def cleanList(points: list[Point]) -> list[Point]:
    """Return points with duplicates removed, preserving order."""
    seen = set()
    out = []
    for p in points:
        key = tuple(p) if isinstance(p, list) else p
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def compute_angle(p1: Point, p2: Point) -> float:
    """Angle of the vector p1 -> p2 measured from the positive x-axis (radians)."""
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def sortByAngle(candidates: list[Point], current: Point, prev_angle: float) -> list[Point]:
    """Sort candidates by relative angle to prev_angle, going clockwise from current.

    Matches concavehull.py:100 — relative angle = (atan2(dy, dx) - prev_angle) mod 2π.

    Note: the original concavehull.py coerced coordinates to int as a numpy-int64
    workaround. We keep them as floats so non-integer datasets work.
    """
    def relative_angle(point):
        dx = point[0] - current[0]
        dy = point[1] - current[1]
        angle = math.atan2(dy, dx)
        return (angle - prev_angle) % (2 * math.pi)

    sorted_pts = sorted(candidates, key=relative_angle)
    return [tuple(p) for p in sorted_pts]


def points_outside_hull(points: list[Point], hull: list[Point]) -> int:
    """Count input points that lie strictly outside the closed hull polygon.

    Hull vertices themselves are treated as inside (shapely's `contains` returns
    False for boundary points, so we filter hull-membership before testing).

    Imports shapely lazily to keep this module dependency-free at import time.
    """
    if len(hull) < 3:
        return len(points)
    from shapely.geometry import Polygon
    from shapely.geometry import Point as ShPoint
    from shapely.prepared import prep

    poly = prep(Polygon([tuple(p) for p in hull]))
    hull_set = {tuple(p) for p in hull}
    return sum(
        1 for p in points
        if tuple(p) not in hull_set and not poly.contains(ShPoint(p))
    )


def do_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """True iff segments p1-p2 and p3-p4 intersect, excluding shared-endpoint cases."""
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False

    def cross(a, b): return a[0] * b[1] - a[1] * b[0]
    def sub(a, b): return (a[0] - b[0], a[1] - b[1])
    def direction(a, b, c): return cross(sub(c, a), sub(b, a))
    def on_segment(a, b, c):
        return (min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and
                min(a[1], c[1]) <= b[1] <= max(a[1], c[1]))

    d1 = direction(p3, p4, p1)
    d2 = direction(p3, p4, p2)
    d3 = direction(p1, p2, p3)
    d4 = direction(p1, p2, p4)

    if (d1 * d2 < 0) and (d3 * d4 < 0):
        return True
    if d1 == 0 and on_segment(p3, p1, p4): return True
    if d2 == 0 and on_segment(p3, p2, p4): return True
    if d3 == 0 and on_segment(p1, p3, p2): return True
    if d4 == 0 and on_segment(p1, p4, p2): return True
    return False
