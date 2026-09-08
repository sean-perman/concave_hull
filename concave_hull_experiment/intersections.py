"""Pluggable intersection-checking backends.

Each backend tracks the hull's edges and answers
"does (a, b) cross any of the stored edges?".

The naive backend scans every stored edge. The bucketed backend keeps a grid
of cells, each cell holding the IDs of edges that pass through it; queries
only check edges in the cells the candidate edge crosses.

Note: do_intersect already returns False when two segments share an
endpoint (geometry.py:do_intersect), so we don't need any "skip the previous
hull edge" logic at the call site.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import math

from .geometry import do_intersect


Point = tuple[float, float]


class IntersectionIndex(ABC):
    @abstractmethod
    def add_edge(self, a: Point, b: Point) -> None: ...

    @abstractmethod
    def remove_edge(self, a: Point, b: Point) -> None: ...

    @abstractmethod
    def would_intersect(self, a: Point, b: Point) -> bool: ...

    @abstractmethod
    def clear(self) -> None: ...


class NaiveIntersectionIndex(IntersectionIndex):
    """Linear scan over every stored edge."""

    def __init__(self):
        self._edges: list[tuple[Point, Point]] = []

    def add_edge(self, a, b):
        self._edges.append((tuple(a), tuple(b)))

    def remove_edge(self, a, b):
        key = (tuple(a), tuple(b))
        try:
            self._edges.remove(key)
        except ValueError:
            pass

    def would_intersect(self, a, b):
        a, b = tuple(a), tuple(b)
        for ea, eb in self._edges:
            if do_intersect(a, b, ea, eb):
                return True
        return False

    def clear(self):
        self._edges = []


class BucketedIntersectionIndex(IntersectionIndex):
    """Spatial grid: cell -> set of edge IDs whose segment touches that cell.

    Queries rasterize the candidate edge to its cells, gather the union of
    edge IDs in those cells, and only run do_intersect on that subset.
    """

    def __init__(self, cell_size: float):
        if cell_size <= 0:
            raise ValueError(f"cell_size must be > 0, got {cell_size}")
        self.cell_size = cell_size
        self._cells: dict[tuple[int, int], set[int]] = defaultdict(set)
        self._edges: dict[int, tuple[Point, Point]] = {}
        self._edge_cells: dict[int, list[tuple[int, int]]] = {}
        self._key_to_id: dict[tuple[Point, Point], int] = {}
        self._next_id = 0

    def _cells_for(self, a: Point, b: Point) -> list[tuple[int, int]]:
        """Every grid cell the segment a-b enters. Exact supercover.

        Algorithm: collect every t in [0,1] where the segment crosses a vertical or
        horizontal grid line, then inspect both the crossing points and the midpoint
        between each pair of crossings.  A point on a grid line belongs to the cells
        on both sides; a point on a grid corner belongs to all four adjacent cells.
        Including the crossing points is essential because two segments can intersect
        at a cell boundary or at the endpoint of one segment without sharing either
        segment's open-interval midpoint cell.
        """
        cs = self.cell_size
        dx = b[0] - a[0]
        dy = b[1] - a[1]

        def axis_cells(value: float) -> set[int]:
            """Grid indices whose closed intervals contain value.

            Usually a coordinate lies inside one cell.  On a grid line it touches
            the cells immediately below/above (or left/right), so return both.  The
            tolerance is deliberately conservative: an extra candidate edge only
            costs one exact intersection test, while omitting a touched cell can
            cause a false negative.
            """
            scaled = value / cs
            cell = math.floor(scaled)
            out = {cell}
            nearest_line = round(scaled)
            if math.isclose(scaled, nearest_line, rel_tol=0.0, abs_tol=1e-12):
                out.add(nearest_line - 1)
            return out

        def add_point_cells(seen: set[tuple[int, int]], t: float) -> None:
            x = a[0] + t * dx
            y = a[1] + t * dy
            for ix in axis_cells(x):
                for iy in axis_cells(y):
                    seen.add((ix, iy))

        t_breaks: set[float] = {0.0, 1.0}
        if dx != 0:
            x_min, x_max = (a[0], b[0]) if a[0] < b[0] else (b[0], a[0])
            i_lo = int(math.ceil(x_min / cs))
            i_hi = int(math.floor(x_max / cs))
            for i in range(i_lo, i_hi + 1):
                t = (i * cs - a[0]) / dx
                if 0.0 < t < 1.0:
                    t_breaks.add(t)
        if dy != 0:
            y_min, y_max = (a[1], b[1]) if a[1] < b[1] else (b[1], a[1])
            j_lo = int(math.ceil(y_min / cs))
            j_hi = int(math.floor(y_max / cs))
            for j in range(j_lo, j_hi + 1):
                t = (j * cs - a[1]) / dy
                if 0.0 < t < 1.0:
                    t_breaks.add(t)

        ts = sorted(t_breaks)
        seen: set[tuple[int, int]] = set()
        for t in ts:
            add_point_cells(seen, t)
        for k in range(len(ts) - 1):
            t_mid = 0.5 * (ts[k] + ts[k + 1])
            add_point_cells(seen, t_mid)
        return sorted(seen)

    def add_edge(self, a, b):
        key = (tuple(a), tuple(b))
        eid = self._next_id
        self._next_id += 1
        self._edges[eid] = key
        self._key_to_id[key] = eid
        cells = self._cells_for(a, b)
        self._edge_cells[eid] = cells
        for c in cells:
            self._cells[c].add(eid)

    def remove_edge(self, a, b):
        key = (tuple(a), tuple(b))
        eid = self._key_to_id.pop(key, None)
        if eid is None:
            return
        for c in self._edge_cells.pop(eid, []):
            self._cells[c].discard(eid)
            if not self._cells[c]:
                del self._cells[c]
        del self._edges[eid]

    def would_intersect(self, a, b):
        a, b = tuple(a), tuple(b)
        seen: set[int] = set()
        for c in self._cells_for(a, b):
            for eid in self._cells.get(c, ()):
                if eid in seen:
                    continue
                seen.add(eid)
                ea, eb = self._edges[eid]
                if do_intersect(a, b, ea, eb):
                    return True
        return False

    def clear(self):
        self._cells.clear()
        self._edges.clear()
        self._edge_cells.clear()
        self._key_to_id.clear()
        self._next_id = 0


def auto_cell_size(points: list[Point]) -> float:
    """Pick a reasonable cell size so each cell holds ~1 point on average."""
    if len(points) < 2:
        return 1.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    extent = max(max(xs) - min(xs), max(ys) - min(ys))
    if extent <= 0:
        return 1.0
    return extent / math.sqrt(len(points))


def make_intersection_index(
    strategy: str, points: list[Point], explicit_cell_size: float
) -> IntersectionIndex:
    if strategy == "naive":
        return NaiveIntersectionIndex()
    if strategy == "bucketed":
        cs = explicit_cell_size if explicit_cell_size > 0 else auto_cell_size(points)
        return BucketedIntersectionIndex(cell_size=cs)
    raise ValueError(f"unknown intersection_strategy: {strategy!r}")
