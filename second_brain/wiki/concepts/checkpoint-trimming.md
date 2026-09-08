# Checkpoint-Based Trimming

**Type:** concept (implemented, deferred from active submission) · **Sources:** [[draft]] §5, [sean2026] §2

> **Submission scope (2026-08-27):** Checkpoint trimming was removed from the
> main body of the active short-paper draft. Retain this page as project history
> and Future Work support; do not treat trimming as a current submission claim
> unless the author explicitly reverses the scope decision.

## Definition

Replace the original's **full restart** (throw away the whole partial hull, redo
from scratch with *k*+1) with a **local** recovery: when the [[gift-wrapping-walk]]
fails, trim the hull back only to the most recent **checkpoint**, increase *k* only
for that region, and resume — preserving the valid prefix.

## Why it matters

The restart is the original algorithm's dominant inefficiency: a tricky section near
the end can discard nearly all prior work, driving the worst case to O(n⁴)
(C-RT-6). Trimming was intended to localize that cost (**C-CHK-3**).

## Experimental status (2026-06-13) — verified for convex_hull + global

First pass ([[2026-06-12-checkpoint-vs-restart-ablation]]) **contradicted C-CHK-3**: with
**per-region** k, trimming wastes ≥ the restart baseline and leaks points. Diagnosis: each
region re-climbs k from initial_k, and convex_hull has many regions.

Follow-up ([[2026-06-13-checkpoint-k-scope]]) added a **global** k scope (one shared rising
k, prefix still preserved) — and **`convex_hull + global` beats the valid restart baseline
on all 4 real sets** (13× faster on redwood, ⅕ the wasted work; new C-CHK-5 on k-scope). The
synthetic n-sweep (unit_disk + star, n→50k, 5 seeds) then confirmed the win **at every size**
(2–5× faster, ⅓–1/10 the wasted work), moving **C-CHK-3 → `verified`** (scoped to
`convex_hull + global`, as a runtime/wasted-work improvement). One caveat stands: the
**leak** (C-CHK-4) is reduced but not eliminated under global (~1–2 pts / 50k; wolf still
leaks 5), so the win is "faster but ~valid", not yet "faster *and* valid". Recommended
config: **convex_hull + global**; fix excluded-points recovery next to close C-CHK-4.

## Folded sub-points (sections here, not separate pages)

- **Convex-hull-vertex checkpoints** ([[draft]] §5.1, C-CHK-2): checkpoints are the
  convex-hull vertices in cyclic order. Rationale: they're guaranteed outer anchors
  (safe rollback targets) and impose a global order on the walk. *Note:* the code
  also offers a 4-cardinal-extreme-points mode; the draft currently presents only
  the convex-hull-vertex mode (draft/code divergence — see C-CHK-2).
- **Regions & per-region *k*:** consecutive checkpoints bound a region, each with its
  own local *k*. Trimming raises *k* for one region, not globally.
- **Trigger 1 — dead end:** every candidate edge intersects the partial hull. Find
  the earliest hull edge hit by the top failed candidate, walk back to the most
  recent checkpoint, trim, raise that region's *k*.
- **Trigger 2 — out-of-order checkpoint:** the walk reaches a later checkpoint before
  the expected next one ⇒ it skipped outer structure; reject the suffix, trim to the
  current checkpoint, raise *k*.

## Claims it supports

- **C-CHK-1** (trim-not-restart, *implemented*) · **C-CHK-2** (checkpoint modes,
  *implemented* — best mode is `convex_hull`, under global k).
- **C-CHK-3** (runtime / wasted-work benefit — *verified* for `convex_hull + global`;
  C-CHK-4 leak is the standing caveat).
- **C-CHK-5** (global k-scope cuts cost on many-region inputs — *verified*; the mechanism
  behind the C-CHK-3 win).
- **C-CHK-4** (checkpoint omits excluded-points recovery → leaky hulls — *verified*; open
  blocker, qualifies [[termination-argument]]).
- Motivated by **C-BASE-3** (full restart) and the runtime analysis **C-RT-6**.
- **C-OPT-4** is *superseded* by this (the reorder-segments idea was abandoned in
  favor of trimming — do not assert). See [[claims]].

## Open / risk

Termination under "No floor" trimming (can a trim pass a confirmed checkpoint?) is
unresolved — see [[termination-argument]]. The draft's prose implies a floor; the
code may not.

## See also

[[gift-wrapping-walk]] · [[termination-argument]] · [[spatial-bucketing]]
