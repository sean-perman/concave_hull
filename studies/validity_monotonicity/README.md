# Fixed-k validity is not monotone

## Result

The six-point integer set in `counterexample_points.csv` disproves the implication

> if the Moreira-Santos construction is valid at `k`, it is valid at every larger `k`.

Using the project's unmodified fixed-`k` construction and exact final-containment
check gives:

| k | result |
|---:|---|
| 3 | valid closed hull containing all six points |
| 4 | dead end after three vertices |
| 5 | valid closed hull containing all six points |

Thus the validity predicate follows `true, false, true`. Binary search for the
smallest valid `k` is not justified without a different monotone predicate or a
separate correctness mechanism.

The example is in general position: no three points are collinear, and every point
has distinct distances to the other five points. The outcome therefore does not
depend on collinearity or nearest-neighbor tie-breaking. Both the naive and bucketed
exact-intersection backends produce the same results.

## Reproduce

From the repository root, using an environment with SciPy, Shapely, and Matplotlib:

```sh
python studies/validity_monotonicity/validity_test.py
```

Repeat the seeded random search that produced the simplified integer example:

```sh
python studies/validity_monotonicity/validity_test.py --search
```

The default verification writes `counterexample.png`, showing the valid `k=3` hull,
the partial `k=4` walk at its dead end, and the valid `k=5` hull.
