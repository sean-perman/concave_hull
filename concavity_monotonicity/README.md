# Does k monotonically control concavity?

**Question.** The Moreira–Santos paper presents the neighbour parameter *k* as a
smoothness dial: larger *k* → smoother / more convex, with *k = n* giving the convex
hull. Is that relationship actually *monotone* — does every increase in *k* make the
hull at least as convex?

**Answer: no.** Increasing *k* by one can make the produced hull *more* concave, and
this happens routinely.

## Method

`monotonicity_test.py` runs the **real** construction — the harness's fixed-*k* pass
(`ConfigurableConcaveHull._attempt`) — at every *k* from 3 upward, and measures

```
area ratio = area(produced hull) / area(convex hull)      (1.0 = convex, smaller = more concave)
```

A *k* where `ratio(k+1) < ratio(k)` is a counterexample to monotonicity. We separate
two cases with a point-in-polygon test:

- **all-enclosing reversal** — both the *k* and *k+1* hulls still contain every input
  point. This is a genuine shape reversal and the clean counterexample.
- degenerate reversal — the larger *k* makes the walk close early and leave points
  outside (a small-area polygon). This also breaks monotonicity but overlaps with the
  separate excluded-points issue, so we report it separately.

(No scipy in this environment: we inject a pure-numpy kNN with the harness's interface
and compute the convex hull / containment ourselves. The hull-construction logic under
test is the unmodified harness code.)

## Findings

Every real dataset tested shows **all-enclosing** (valid) non-monotone steps:

| dataset | n | non-monotone steps | of which all-enclosing | example (valid) |
|---|--:|--:|--:|---|
| world_capitals | 194 | 4 | 3 | k 78→79: ratio 0.864 → 0.863 |
| us_mainland_cities | 202 | 7 | 4 | k 54→55: ratio 0.936 → 0.934 |
| star_8_tips | 300 | 3 | 2 | k 76→77: ratio 0.976 → 0.975 |

On the real data the valid reversals are small (the boundary nudges into a slightly
deeper notch). The large drops seen on the real sets (e.g. cities k 88→89:
0.97 → 0.02) are the *degenerate* kind — the hull closes early and leaks points — not
clean shape reversals.

Random uniform point sets show all-enclosing reversals are common and grow with n:

| n | seeds | non-monotone | all-enclosing reversal |
|--:|--:|--:|--:|
| 8  | 400 | 23 | 4 |
| 10 | 400 | 35 | 4 |
| 12 | 400 | 46 | 18 |
| 15 | 400 | 69 | 35 |
| 20 | 400 | 80 | 49 |

## Minimal clean counterexample

`counterexample_points.csv` (n = 8) — see `counterexample.png`:

- **k = 5:** ratio **0.994** (nearly the convex hull)
- **k = 6:** ratio **0.808** (a clear concave notch)

Both hulls enclose all 8 points, so this is a genuine reversal: a *larger* k produced a
*more* concave hull. This is the figure to use in the paper.

## Takeaway for the paper

The claim "k controls concavity" holds only at the endpoint k = n (convex hull) and as
a loose average trend. It is **not monotone**: the greedy largest-right-turn rule can,
on adding one more candidate, route the boundary into a deeper concavity. This is now an
*observation* (measured), not a conjecture. Natural framing: state it as a remark with
the n = 8 figure, and note that a principled k-vs-shape relationship is future work.

## Reproduce

```
python3 monotonicity_test.py
```
Outputs `counterexample_points.csv` and `counterexample.png` in this folder.
