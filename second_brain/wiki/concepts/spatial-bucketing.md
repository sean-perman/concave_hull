# Spatial Bucketing

**Type:** concept · **Sources:** [[draft]] §6, [sean2025] §5,
[[franklin-uniform-grids]], [[experiment-harness]],
[[2026-08-27-spatial-bucketing-paper-benchmark]]

## Definition

A grid index over geometry so that a query touches only nearby cells instead of the
whole structure. In this paper it accelerates the **edge-intersection check** of the
[[gift-wrapping-walk]]: hull edges are filed into spatial buckets by location, and a
new candidate edge is tested only against edges in the relevant nearby buckets.

The index is an exact candidate filter, not an approximate intersection test. Every
edge returned by the grid is still checked by the same exact segment predicate used by
the naive implementation.

Uniform-grid indexing for intersection detection is established prior art
([franklin1989]). Our implementation selects square-cell width automatically as
`max(x_range, y_range) / sqrt(n)`. It enumerates segment crossings with grid lines,
adds midpoint samples between crossings, assigns boundary points to both adjacent
cells (four at a corner), deduplicates edge IDs, and then applies the exact predicate.

## Why it matters

Intersection checking is the dominant per-run cost (triangular-sum growth as the
hull lengthens; C-RT-4). Restricting it to local buckets makes it much faster in
practice — most candidate edges only interact with a small local part of the hull.

The corrected publication benchmark isolates this feature under the original restart
strategy. Across 120 paired trials, bucketing produced identical valid hulls, reduced
median runtime by 1.28–3.45×, and reduced calls to the exact intersection predicate by
6.9–188.6×. See [[2026-08-27-spatial-bucketing-paper-benchmark]].

## Exactness condition and repaired bug

The grid must register every cell touched by a hull edge, including cells touched only
at an endpoint, along a grid line, or at a grid corner. The earlier midpoint-only
rasterizer could omit such cells, creating a false negative when two edges intersected
in an omitted boundary cell. The corrected `_cells_for` implementation constructs an
exact supercover by including grid crossings and the adjacent boundary cells.

This condition is guarded by direct regressions, randomized comparisons, full-hull
naive/bucketed equality tests, and an exhaustive 90,000-pair integer-lattice comparison
against Shapely. All 20 repository tests passed before the publication benchmark.

## Folded sub-point: edge-intersection checking

The named operation being accelerated. Per candidate, cost drops from "vs all *h*
hull edges so far" O(h) to O(i) where *i* = edges in the relevant buckets; all *k*
candidates cost O(k·i) instead of O(k·h). *(If this op grows its own analysis or
gets linked independently, bud it off into its own page.)*

## Honest bound (golden-rule sensitive)

The draft **explicitly states the worst-case asymptotic bound does not improve** —
many edges can still fall in one bucket. The measured win is a **constant factor**,
not an asymptotic one. The *practical speedup* is `verified` (see C-OPT-2); the
stronger "expected O(1) per check" / asymptotic form remains `conjectured` and must
not be asserted as a proven speedup.

## Claims it supports

- **C-OPT-2** — spatially indexing hull edges gives a practical (constant-factor)
  speedup to candidate validation — ***verified***
  ([[2026-08-27-spatial-bucketing-paper-benchmark]]: 120 paired trials,
  1.28–3.45× median runtime speedup, 6.9–188.6× fewer exact-predicate calls, and
  identical valid hulls). The asymptotic "expected O(1) per check" form stays
  *conjectured* (draft §6.1's honest framing).
- **C-OPT-1** — bucketing for *k-NN* itself → sub-linear. **Not in the draft**: the
  draft buckets only intersection search. The unpublished details of the
  original Mathematica nearest-neighbour implementation are not established;
  do not attribute a spatial index to it. Currently unsupported by the draft.
- Linked to the headline **C-OPT-3** (O(n log n) main loop) — *conjectured*, never
  to be asserted as proven. See [[claims]].

## See also

[[gift-wrapping-walk]] · [[checkpoint-trimming]] · [[franklin-uniform-grids]] · [[experiment-harness]] ·
[[2026-08-27-spatial-bucketing-paper-benchmark]]
