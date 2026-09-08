# Fixed-k Validity Nonmonotonicity Counterexample

**Date:** 2026-08-31  
**Status:** reproduced; regression-tested  
**Question:** If the Moreira--Santos construction produces a valid hull for some
$k$, must it also produce a valid hull for every larger $k$?

## Result

No. The fixed-$k$ validity predicate is not monotone. The following six-point
integer set produces the sequence **valid, dead end, valid** for $k=3,4,5$:

| label | x | y |
|---|---:|---:|
| A | 9 | 9 |
| B | 7 | 9 |
| C | 0 | 2 |
| D | 0 | 8 |
| E | 4 | 7 |
| F | 3 | 1 |

- **$k=3$:** valid closed hull containing all six points, with walk
  $F\to E\to A\to B\to D\to C\to F$.
- **$k=4$:** failure after the partial walk $F\to B\to A$; every available
  continuation intersects an existing hull edge, so the attempt reaches a dead
  end.
- **$k=5$:** valid closed hull containing all six points, with walk
  $F\to A\to B\to D\to C\to F$; point E is enclosed.

Thus success at $k=3$ does not imply success at the larger value $k=4$, even
though the all-candidates endpoint $k=5=n-1$ succeeds.

## Method

The search and verification use the experiment harness's unmodified fixed-$k$
construction, `ConfigurableConcaveHull._attempt`, followed by the exact
all-points-contained check. A seeded search samples six-point subsets of the
integer grid $\{0,\ldots,10\}^2$ and rejects:

1. every set with a collinear triple; and
2. every set with an equal-distance nearest-neighbour tie from any point.

The saved example was found at trial 629 with seed `20260831`. Removing these
degeneracies makes the result independent of collinearity handling and k-NN
tie-breaking. Both the naive and corrected bucketed exact-intersection backends
produce the same `true, false, true` validity sequence.

Six points is the minimum possible size for this pattern under the paper's
$3\leq k\leq n-1$ convention: the terminal all-candidates value is valid, so a
valid-to-invalid transition requires a still-larger terminal value at which
validity returns.

## Reproduce

From the repository root in the project's Python 3.12 environment:

```sh
python3.12 validity_monotonicity/validity_test.py
python3.12 validity_monotonicity/validity_test.py --search --trials 1000
python3.12 -m unittest discover -s tests -p 'test_validity_monotonicity.py' -v
```

Verification result: both regression tests pass; the 1,000-trial seeded search
rediscovers the saved example at trial 629.

## Artifacts

- Points: `validity_monotonicity/counterexample_points.csv`
- Search and verification: `validity_monotonicity/validity_test.py`
- Figure: `validity_monotonicity/counterexample.png`
- Regression: `tests/test_validity_monotonicity.py`
- Explanation: `validity_monotonicity/README.md`

## Paper consequence

This is stronger than C-MONO-1's shape result. C-MONO-1 shows that hull concavity
need not change monotonically while both outputs remain valid; this experiment
shows that the Boolean success predicate itself can reverse. Therefore ordinary
binary search cannot be used to find the smallest valid $k$: its required
false-then-true partition does not exist in general.

Geometric forward growth remains terminating when capped at the all-candidates
value because it never treats a success as proof about untested values; it simply
continues upward after any tested failure. Under the draft's
$C_{\mathrm{run}}(k)=O(kn^2)$ bound, constant-ratio geometric growth also gives
$\sum k_j=O(n)$ and hence an $O(n^3)$ restart upper bound. It may skip smaller
valid values and therefore change the returned hull.

**Integrated 2026-08-31:** the active short-paper draft now folds this six-point
example into the renamed Non-Monotone Effects of $k$ section as a second
subsection, retaining the distinct eight-point shape result. It includes the
integer coordinates, exact $k=3,4,5$ walks, general-position and no-distance-tie
qualifications, the three-panel figure, and the binary-search consequence. The
runtime section also states the C-KG-3 geometric-growth corollary. The compiled
paper remains seven A4 pages.
