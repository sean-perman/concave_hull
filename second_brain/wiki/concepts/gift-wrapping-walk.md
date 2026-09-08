# Gift-Wrapping Walk (k-NN modified Jarvis march)

**Type:** concept · **Sources:** [[moreira-santos]] §3.1, [[draft]] §2.2

## Definition

The construction at the heart of the whole method: a variant of the Jarvis-march
("gift wrapping") convex-hull walk in which the next boundary vertex is chosen not
from *all* remaining points but only from the **k-nearest neighbours** of the
current vertex — picking the candidate giving the largest right-hand turn that does
not intersect the partial hull. Start at the minimum-*y* point; repeat until the
walk returns to the start, closing the polygon.

## Why it matters

This is the mechanism every contribution acts on. The improvements don't change the
walk — they change what happens when it fails (→ [[checkpoint-trimming]]) and how
fast each step's intersection test runs (→ [[spatial-bucketing]]).

## Folded sub-points (attributes, not separate pages)

- **The parameter *k* / smoothness control.** *k* is dimensionless (a count, not a
  distance). Small *k* → tighter, more concave; large *k* → smoother; *k = n*
  reproduces the convex hull (plain Jarvis march). Controls fidelity vs smoothness.
- **Min-*y* start + angle ordering.** Candidates are sorted by turn angle relative
  to the previous edge; the greedy pick is the first non-intersecting one.
- **The two failure cases** (dead end = all candidates intersect; excluded points =
  closed hull leaves points outside) — both originally handled by full restart with
  *k*+1. The full-restart behavior is described under [[checkpoint-trimming]] as the
  thing being replaced.

## Claims it supports

- **C-BASE-1** — valid simple polygon (Jordan curve unless collinear) for k≥3.
- **C-BASE-3** — original restarts from scratch on failure (the cost this motivates).
- Per-step costs analyzed in C-RT-1 (min-*y* O(n)), C-RT-2 (k-NN O(n)),
  C-RT-3 (sort O(k log k)), C-RT-4 (intersection check). See [[claims]].

## See also

[[checkpoint-trimming]] · [[spatial-bucketing]] · [[termination-argument]]
