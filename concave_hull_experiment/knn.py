"""Pluggable k-nearest-neighbor backends.

Each backend exposes the same interface so the main algorithm doesn't care
which one it's using.
"""
from abc import ABC, abstractmethod

import numpy as np


Point = tuple[float, float]


class KNNIndex(ABC):
    @abstractmethod
    def build(self, points: list[Point]) -> None: ...

    @abstractmethod
    def query(self, p: Point, k: int) -> list[Point]: ...

    @abstractmethod
    def remove(self, p: Point) -> None: ...

    @abstractmethod
    def add(self, p: Point) -> None: ...

    @abstractmethod
    def size(self) -> int: ...


class ScipyKNNIndex(KNNIndex):
    """cKDTree with lazy rebuild after deletions.

    cKDTree is immutable, so we keep a 'deleted' set and over-query, then
    rebuild once deletions exceed REBUILD_THRESHOLD of the active set.
    """

    REBUILD_THRESHOLD = 0.25

    def __init__(self):
        self._points: list[Point] = []
        self._deleted: set[Point] = set()
        self._tree = None

    def build(self, points):
        self._points = [tuple(p) for p in points]
        self._deleted = set()
        self._rebuild_tree()

    def _rebuild_tree(self):
        from scipy.spatial import cKDTree
        active = [p for p in self._points if p not in self._deleted]
        self._points = active
        self._deleted = set()
        if active:
            self._tree = cKDTree(np.array(active))
        else:
            self._tree = None

    def query(self, p, k):
        if self._tree is None or not self._points:
            return []
        active_count = len(self._points) - len(self._deleted)
        if active_count <= 0:
            return []
        # Over-query to compensate for tombstoned (deleted) points.
        k_request = min(k + len(self._deleted), len(self._points))
        dists, idxs = self._tree.query(np.array(p), k=k_request)
        if np.isscalar(idxs):
            idxs = [int(idxs)]
        else:
            idxs = idxs.tolist()
        out = []
        for i in idxs:
            if i >= len(self._points):
                continue
            pt = self._points[i]
            if pt in self._deleted:
                continue
            out.append(pt)
            if len(out) >= k:
                break
        return out

    def remove(self, p):
        key = tuple(p)
        if key in self._deleted:
            return
        # Only mark as deleted if it actually exists in the tree.
        # (Cheap membership: linear, but fine — we already pay O(n) elsewhere per step.)
        if key in self._points:
            self._deleted.add(key)
        if len(self._deleted) > self.REBUILD_THRESHOLD * max(len(self._points), 1):
            self._rebuild_tree()

    def add(self, p):
        key = tuple(p)
        # If the point was tombstoned, just un-tombstone it — no rebuild needed.
        if key in self._deleted:
            self._deleted.discard(key)
            return
        self._points.append(key)
        self._rebuild_tree()

    def size(self):
        return len(self._points) - len(self._deleted)


def make_knn_index(backend: str) -> KNNIndex:
    if backend == "scipy":
        return ScipyKNNIndex()
    raise ValueError(f"unknown knn_backend: {backend!r} (expected 'scipy')")
