"""Test whether the Moreira-Santos parameter k monotonically controls concavity.

The original paper presents k as a smoothness dial: larger k -> smoother / more
convex, with k = n giving the convex hull. That claim is informal. This script
checks it empirically by running the REAL construction (the harness's fixed-k pass,
`ConfigurableConcaveHull._attempt`) at every k and measuring a concavity metric.

Concavity metric: area ratio = area(produced hull) / area(convex hull) in [0, 1].
1.0 = convex; smaller = more concave. If the monotonic claim held, the ratio would
be non-decreasing in k. A k where ratio(k+1) < ratio(k) is a counterexample.

No scipy in this environment, so we (a) inject a pure-numpy kNN backend with the
harness's interface and (b) compute the convex hull ourselves (monotone chain).
"""
import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import concave_hull_experiment.concave_hull as ch_mod
from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull

try:
    from concave_hull_experiment.geometry import points_outside_hull
except Exception:
    points_outside_hull = None  # shapely may be unavailable; leak count is optional

Point = tuple[float, float]


# ---------------------------------------------------------------------------
# Pure-numpy kNN with the harness's KNNIndex interface (replaces the scipy one).
# ---------------------------------------------------------------------------
class BruteKNNIndex:
    def __init__(self):
        self._active: list[Point] = []

    def build(self, points):
        self._active = [tuple(p) for p in points]

    def query(self, p, k):
        if not self._active or k <= 0:
            return []
        arr = np.asarray(self._active, dtype=float)
        d = np.sum((arr - np.asarray(p, dtype=float)) ** 2, axis=1)
        idx = np.argsort(d, kind="stable")[:k]
        return [self._active[i] for i in idx]

    def remove(self, p):
        key = tuple(p)
        if key in self._active:
            self._active.remove(key)

    def add(self, p):
        self._active.append(tuple(p))

    def size(self):
        return len(self._active)


def _patched_make_knn_index(backend: str):
    return BruteKNNIndex()


# Inject into the module the algorithm actually calls.
ch_mod.make_knn_index = _patched_make_knn_index


# ---------------------------------------------------------------------------
# Geometry: polygon area (shoelace) and convex-hull area (monotone chain).
# ---------------------------------------------------------------------------
def polygon_area(poly: list[Point]) -> float:
    pts = [tuple(p) for p in poly]
    if len(pts) >= 2 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        return 0.0
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def convex_hull(points: list[Point]) -> list[Point]:
    pts = sorted(set(tuple(p) for p in points))
    if len(pts) < 3:
        return pts

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
    return lower[:-1] + upper[:-1]


def convex_area(points: list[Point]) -> float:
    return polygon_area(convex_hull(points))


def _point_in_poly(pt, poly) -> bool:
    """Ray-casting point-in-polygon (boundary counts as inside). Pure Python."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (x1, y1) == (x, y):
            return True
        if (y1 > y) != (y2 > y):
            xint = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if abs(xint - x) < 1e-12:
                return True
            if x < xint:
                inside = not inside
    return inside


def count_outside(points: list[Point], hull: list[Point]) -> int:
    poly = [tuple(p) for p in hull]
    if len(poly) >= 2 and poly[0] == poly[-1]:
        poly = poly[:-1]
    if len(poly) < 3:
        return len(points)
    hset = set(poly)
    out = 0
    for p in points:
        if tuple(p) in hset:
            continue
        if not _point_in_poly(tuple(p), poly):
            out += 1
    return out


# ---------------------------------------------------------------------------
# The k-sweep over the real fixed-k construction.
# ---------------------------------------------------------------------------
def k_sweep(points: list[Point], kmax: int | None = None):
    """Return list of dicts: for each k that yields a closed hull, its area ratio."""
    algo = ConfigurableConcaveHull()
    cfg = ConcaveHullConfig(
        knn_backend="scipy",  # ignored; we patched make_knn_index
        intersection_strategy="naive",
        failure_strategy="restart",
        validate_final_hull="off",
    )
    n = len(set(tuple(p) for p in points))
    ca = convex_area(points)
    if ca <= 0:
        return []
    hi = (kmax or n - 1)
    hi = min(hi, n - 1)
    rows = []
    for k in range(3, hi + 1):
        hull, _ = algo._attempt(points, k, cfg)
        if hull is None or len(hull) < 4:
            rows.append({"k": k, "ok": False, "ratio": None,
                         "outside": None, "hull": None})
            continue
        ratio = polygon_area(hull) / ca
        outside = count_outside(points, hull)
        rows.append({"k": k, "ok": True, "ratio": ratio,
                     "outside": outside, "hull": hull})
    return rows


def find_violations(rows, eps=1e-9, require_valid=False):
    """Successive successful k's where the area ratio DROPS (more concave at larger k).

    require_valid=True keeps only 'clean' reversals: both the k and k+1 hulls enclose
    every input point (outside == 0), isolating a genuine shape reversal from the
    degenerate case where a larger k makes the walk close early and leak points.
    """
    ok = [r for r in rows if r["ok"]]
    viol = []
    for a, b in zip(ok, ok[1:]):
        if b["ratio"] < a["ratio"] - eps:
            if require_valid and not (a["outside"] == 0 and b["outside"] == 0):
                continue
            viol.append({
                "k_lo": a["k"], "k_hi": b["k"],
                "ratio_lo": a["ratio"], "ratio_hi": b["ratio"],
                "drop": a["ratio"] - b["ratio"],
            })
    return viol


def load_csv(path) -> list[Point]:
    pts = []
    with open(path) as f:
        for row in csv.DictReader(f):
            pts.append((float(row["x"]), float(row["y"])))
    return pts


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------
def run_datasets():
    ddir = os.path.join(REPO, "datasets")
    # Keep to sets small enough for a full k-sweep (O(n^3)); skip wolf/redwood (~1000+).
    names = ["world_capitals.csv", "us_mainland_cities.csv", "star_8_tips.csv"]
    print("=== Real datasets (full k-sweep) ===")
    out = {}
    for name in names:
        path = os.path.join(ddir, name)
        if not os.path.exists(path):
            continue
        pts = load_csv(path)
        rows = k_sweep(pts)
        viol = find_violations(rows)
        clean = find_violations(rows, require_valid=True)
        ok = [r for r in rows if r["ok"]]
        print(f"\n{name}: n={len(set(map(tuple,pts)))}, "
              f"{len(ok)} of {len(rows)} k-values produced a closed hull, "
              f"{len(viol)} non-monotone steps ({len(clean)} of them all-enclosing)")
        for v in sorted(clean, key=lambda d: -d["drop"])[:5]:
            print(f"   [valid] k {v['k_lo']:>3}->{v['k_hi']:<3}  "
                  f"ratio {v['ratio_lo']:.4f} -> {v['ratio_hi']:.4f}  "
                  f"(drop {v['drop']:.4f})")
        out[name] = rows
    return out


def random_search(n_values=(8, 10, 12, 15, 20), seeds=400):
    """Hunt for the smallest CLEAN counterexample (both hulls all-enclosing)."""
    print("\n=== Random uniform point sets (search for minimal clean counterexample) ===")
    best = None  # (n, seed, max_drop, pts, rows, viol)
    rng_master = np.random.default_rng(0)
    for n in n_values:
        hits = 0
        clean_hits = 0
        for s in range(seeds):
            rng = np.random.default_rng(rng_master.integers(1 << 30))
            pts = [tuple(p) for p in rng.random((n, 2))]
            if len(set(pts)) < n:
                continue
            rows = k_sweep(pts)
            if find_violations(rows):
                hits += 1
            clean = find_violations(rows, require_valid=True)
            if clean:
                clean_hits += 1
                max_drop = max(v["drop"] for v in clean)
                cand = (n, s, max_drop, pts, rows, clean)
                # Prefer fewest points, then the clearest drop.
                if best is None or (n < best[0]) or (n == best[0] and max_drop > best[2]):
                    best = cand
        print(f"  n={n:>3}: {hits}/{seeds} non-monotone, "
              f"{clean_hits}/{seeds} with an all-enclosing reversal")
    return best


def make_figure(pts, rows, k_lo, k_hi, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ok = [r for r in rows if r["ok"]]
    ks = [r["k"] for r in ok]
    ratios = [r["ratio"] for r in ok]
    hull_lo = next(r["hull"] for r in ok if r["k"] == k_lo)
    hull_hi = next(r["hull"] for r in ok if r["k"] == k_hi)
    px = [p[0] for p in pts]
    py = [p[1] for p in pts]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    ax = axes[0]
    ax.plot(ks, ratios, "-o", ms=3)
    ax.plot([k_lo, k_hi], [dict(zip(ks, ratios))[k_lo], dict(zip(ks, ratios))[k_hi]],
            "r-o", lw=2, label="reversal")
    ax.set_xlabel("k"); ax.set_ylabel("area ratio (1 = convex)")
    ax.set_title("Area ratio vs. k"); ax.legend()

    for ax, hull, k in ((axes[1], hull_lo, k_lo), (axes[2], hull_hi, k_hi)):
        hx = [p[0] for p in hull]; hy = [p[1] for p in hull]
        ax.plot(hx, hy, "-", lw=1.5)
        ax.scatter(px, py, s=18, zorder=3)
        r = dict(zip(ks, ratios))[k]
        ax.set_title(f"k = {k}   (ratio {r:.3f})")
        ax.set_aspect("equal", adjustable="datalim")

    fig.suptitle("Increasing k can decrease the area ratio (more concave): "
                 f"k={k_lo}->{k_hi}")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print(f"  figure saved: {path}")


if __name__ == "__main__":
    ds_rows = run_datasets()
    best = random_search()

    if best is not None:
        n, s, drop, pts, rows, viol = best
        v = max(viol, key=lambda d: d["drop"])
        print("\n=== Minimal clean counterexample (both hulls enclose all points) ===")
        print(f"n={n}, max all-enclosing area-ratio drop={drop:.4f}")
        print(f"  area ratio rises then FALLS: "
              f"k={v['k_lo']} -> {v['ratio_lo']:.4f}, "
              f"k={v['k_hi']} -> {v['ratio_hi']:.4f}")
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "counterexample_points.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["x", "y"])
            w.writerows(pts)
        make_figure(pts, rows, v["k_lo"], v["k_hi"],
                    os.path.join(here, "counterexample.png"))
        print("  saved counterexample_points.csv + counterexample.png")
    else:
        print("\nNo all-enclosing counterexample found in the random search.")
