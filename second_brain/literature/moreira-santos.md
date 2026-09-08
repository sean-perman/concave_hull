# Moreira & Santos (2007) — Concave Hull: A k-NN Approach

**Bib key:** `[moreira2007]`
**Type:** source-summary (literature — immutable)
**Full cite:** A. Moreira & M. Y. Santos, "Concave Hull: A k-Nearest Neighbours
Approach for the Computation of the Region Occupied by a Set of Points," GRAPP
2007 (Int. Conf. on Computer Graphics Theory and Applications), pp. 61–68.

## Thesis (one paragraph)

This is the **original algorithm this paper improves**. It computes a (possibly
non-convex) polygon describing the region occupied by a planar point set using a
k-nearest-neighbours variant of the Jarvis-march "gift-wrapping" walk: start at
the lowest-Y point, and at each step pick, among the *k* nearest unused points,
the candidate giving the largest right-hand turn from the previous edge. The
single parameter *k* controls smoothness — larger *k* yields smoother hulls.
Two special cases force backtracking: (a) the new edge **self-intersects** an
existing hull edge → try the next candidate, and if none works, restart with
*k*+1; (b) **non-uniform density** leaves far-away points outside, detected by a
final "all points inside?" check → restart with *k*+1. The implementation is a
Mathematica package; the authors report runtime growing **approximately linearly**
with *n* (Fig. 8, log-log) but explicitly leave **formal complexity analysis as
future work**.

## Key claims it makes (and how they bear on us)

- **k-NN gift-wrapping walk** (§3.1, Alg. 1): the procedure we preserve. Backs
  the [[gift-wrapping-walk]] concept and **C-BASE-1** (valid simple polygon for
  k≥3; criterion 6 = Jordan curve unless collinear).
- **Full restart on failure** (Alg. 1 lines 33 & 45, both
  `Return[ConcaveHull[pointsList, kk+1]]`): on either special case the algorithm
  re-invokes itself from scratch with *k*+1, **discarding all prior work**. This
  is exactly the inefficiency [[checkpoint-trimming]] targets. Backs **C-BASE-3**.
- **No complexity analysis** (criterion 9 in §4.3; restated in §5 conclusions):
  "The analysis of the computational complexity … is still future work." This is
  the gap our paper fills. Backs **C-BASE-2**.
- **Per-step costs we later analyze**: min-Y start `FindMinYPoint` (→ **C-RT-1**,
  O(n)); `NearestPoints` linear scan (→ **C-RT-2**, O(n) naive k-NN). The paper
  itself doesn't bound these — our `[sean2025]` analysis does.
- **Empirical near-linear runtime** (§4.2, Figs. 8–9): unoptimized Mathematica,
  random points in a unit disk, averaged over 20 sets. **Tension to track:** this
  empirical "≈ linear" sits against our `[sean2025]` worst/avg-case analysis
  (**C-RT-5** O(n²) avg, **C-RT-6** O(n⁴) worst). Not a contradiction — their
  measurement is small-n, single distribution, and recursion is rare on clean
  clustered data — but the draft must not cite their "linear" as a complexity
  result. It is empirical and unanalyzed by them.
- **Galton 9-criteria self-assessment** (§4.3): outliers excluded, boundary
  points always exist, topologically regular / Jordan curve unless collinear,
  connected, polygonal; large empty areas may or may not be excluded depending on
  *k*; 3-D generalization hard; complexity open. Connects to `[galton2006]`
  ([[galton-duckham]] — page planned, not yet written).

## Relation to our contribution

The whole improvement program is defined *against* this paper: we keep the walk
(C-BASE-1) and the correctness criteria, but replace the **discard-everything
restart** (C-BASE-3) with checkpoint trimming (C-CHK-1) and the naive scans
(C-RT-1/2) with spatial bucketing (C-OPT-1/2). Their unanalyzed complexity
(C-BASE-2) is what our runtime section supplies.

## Provenance / context

Developed in the LOCAL project for finding boundaries ("footprints") of POI
clusters, downstream of SNN density clustering. Distance metric is Euclidean but
swappable. Code was a Mathematica package with a web demo (LOCAL project site,
c. 2006 — likely dead now). Used on a real 18,914-POI dataset.

## Status

Ingested 2026-06-11. No claim status changes — this paper is the *evidence*
already cited by C-BASE-1/2/3 and C-RT-1/2 (all `established`); cross-citations
verified against the text and algorithm listing.
