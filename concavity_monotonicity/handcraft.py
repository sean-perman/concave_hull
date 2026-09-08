"""Probe the walk so we can hand-design an obvious non-monotone counterexample.

Prints, for a given point set and k, the sequence of chosen points and (optionally)
the angle-ordered candidate set at each step, plus the area ratio. Lets us see exactly
which point the selection rule picks and why it changes when k grows by one.
"""
import os, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import concave_hull_experiment.concave_hull as ch
from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull
from monotonicity_test import polygon_area, convex_area, convex_hull, count_outside, BruteKNNIndex

ch.make_knn_index = lambda b: BruteKNNIndex()
ALGO = ConfigurableConcaveHull()
CFG = ConcaveHullConfig(intersection_strategy="naive")


def probe(points, k, verbose=True):
    steps = []
    def on_step(s):
        if not s.rolled_back:
            steps.append((tuple(round(c, 2) for c in s.current),
                          tuple(round(c, 2) for c in s.accepted) if s.accepted else None,
                          [tuple(round(c, 2) for c in p) for p in s.candidates]))
    hull, _ = ALGO._attempt(points, k, CFG, on_step=on_step)
    if hull is None:
        if verbose:
            print(f"  k={k}: DEAD END (no closed hull)")
        return None
    ca = convex_area(points)
    ratio = polygon_area(hull) / ca
    out = count_outside(points, hull)
    if verbose:
        print(f"  k={k}: ratio={ratio:.3f} outside={out} "
              f"hull={[tuple(round(c,2) for c in p) for p in hull[:-1]]}")
    return {"hull": hull, "ratio": ratio, "outside": out, "steps": steps}


def compare(points, klo, khi, show_steps=False):
    print(f"n={len(points)}  conv_area={convex_area(points):.3f}")
    a = probe(points, klo)
    b = probe(points, khi)
    if a and b:
        nonmono = b["ratio"] < a["ratio"] - 1e-9 and a["outside"] == 0 and b["outside"] == 0
        print(f"  --> non-monotone & both valid: {nonmono} "
              f"(ratio {a['ratio']:.3f} -> {b['ratio']:.3f})")
        if show_steps and nonmono:
            for label, r in ((klo, a), (khi, b)):
                print(f"  walk at k={label}:")
                for cur, acc, cands in r["steps"]:
                    print(f"     at {cur} -> {acc}   candidates(angle order): {cands}")
    return a, b


def search_clean(n_values=(6, 7, 8), coord=12, seeds=20000):
    """Find integer-coordinate sets where k=3 gives the convex hull (ratio 1.0) and
    k=4 poable inward (ratio < threshold), both valid. The clearest possible story."""
    rng = np.random.default_rng(7)
    best = None
    for _ in range(seeds):
        n = int(rng.choice(n_values))
        pts = set()
        while len(pts) < n:
            pts.add((int(rng.integers(0, coord + 1)), int(rng.integers(0, coord + 1))))
        pts = [tuple(map(float, p)) for p in pts]
        a = probe(pts, 3, verbose=False)
        b = probe(pts, 4, verbose=False)
        if not a or not b:
            continue
        if a["outside"] == 0 and b["outside"] == 0 and a["ratio"] > 0.999 \
                and b["ratio"] < 0.93:
            gap = a["ratio"] - b["ratio"]
            cand = (n, gap, pts, a, b)
            if best is None or n < best[0] or (n == best[0] and gap > best[1]):
                best = cand
    return best


if __name__ == "__main__":
    print("Searching for a clean k=3-convex / k=4-concave integer example...")
    best = search_clean()
    if best:
        n, gap, pts, a, b = best
        print(f"\nFOUND n={n}, ratio {a['ratio']:.3f} (k=3) -> {b['ratio']:.3f} (k=4)")
        print("points:", [tuple(map(int, p)) for p in pts])
        compare(pts, 3, 4, show_steps=True)
    raise SystemExit

if False:
    # ---- Hand design v1: a square outline with an interior point in a "pocket" ----
    # Start is the unique lowest point. Idea: with small k the walk strides across the
    # top edge (convex); with k+1 an interior point enters the candidate set and offers
    # a sharper right-hand turn, pulling the boundary inward.
    designs = {}

    designs["v1 square+pocket"] = [
        (5, 0),    # S  unique lowest -> start
        (10, 4),
        (10, 9),
        (5, 10),
        (0, 9),
        (0, 4),
        (5, 6),    # interior pocket point
    ]

    designs["v2 wide top bay"] = [
        (6, 0),
        (12, 3),
        (12, 8),
        (8, 8),
        (4, 8),
        (0, 8),
        (0, 3),
        (6, 5),    # interior, under the top edge
    ]

    for name, pts in designs.items():
        print("="*60, "\n", name)
        for klo in (3, 4, 5):
            compare(pts, klo, klo + 1)
