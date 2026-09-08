# Advisor Guidance and Project Commitments

**Source:** pasted Slack history between Sean Perman and Mario Lopez  
**Source dates:** not preserved in the pasted export  
**Ingested:** 2026-07-29  
**Type:** project-history and advisor-guidance note

This page records only durable information that affects the concave-hull paper.
Unrelated academic administration, personal matters, and casual conversation
from the source archive are intentionally omitted.

## Confirmed advisor guidance

### Project selection

During the original computational-geometry project selection, Sean considered a
curse-of-dimensionality paper and a kNN-based concave/approximate-hull paper.
Mario judged the **concave-hull paper to be the more appropriate project** and
directed Sean to work on it.

This establishes that the current paper grew from the advisor-approved
computational-geometry project rather than from the abandoned
curse-of-dimensionality direction.

### Publication direction

After Sean reported implementing the concave-hull algorithm, partially
implementing improvements, and observing large speedups, Mario suggested that
they review the work and **consider publishing it in the same forum used by the
previous authors**.

Sean later described a plan to submit to GRAPP, the conference that published
Moreira--Santos. Mario acknowledged the write-up and said he would review it,
but the Slack excerpt does not contain an explicit acceptance decision or paper
review. The stronger evidence for the venue direction is Mario's earlier
suggestion to consider the original forum.

GRAPP has since merged into GRIVAPP. The current venue decision and dates are in
[[grivapp-2027-submission]].

### Fair baseline and shared kNN

When Sean asked whether the original 2007 Mathematica implementation should be
modeled with brute-force kNN or a spatial index, Mario's methodological
direction was:

1. implement the original algorithmic version; and
2. use the **same kNN implementation for both the baseline and enhanced
   versions**.

The purpose is a controlled comparison: the experiment should attribute
differences to restart/checkpoint and intersection strategies, not to different
nearest-neighbor implementations.

The current `concave_hull_experiment` harness satisfies this direction:

- `ConcaveHullConfig.knn_backend` has only one allowed value, `scipy`;
- all variants therefore use the same SciPy `cKDTree` implementation; and
- restart/checkpoint and naive/bucketed intersection are varied independently.

Important wording constraint: this is a **fair controlled reimplementation** of
the original algorithm. It is not evidence that Moreira--Santos used a KD-tree
inside Mathematica; their paper does not provide enough implementation detail
to establish that.

## Author plans visible in the Slack history

These are useful provenance, but they are not recorded as advisor-approved
results unless explicitly noted above:

- Sean proposed an amortized comparison of full restart versus incremental
  hull editing. This remains a logical analysis direction, but the current
  submission plan allows the full amortized analysis to remain Future Work.
- Sean considered segment trees or spatial hashing for intersection checking.
  The implemented paper contribution became spatial bucketing.
- Early ideas included extending hull construction to 3D or n dimensions.
  No advisor decision or completed work on that extension appears in this
  archive; it is outside the minimum viable GRIVAPP submission.
- Sean's proposed paper structure included runtime analysis, checkpoint
  trimming, spatial bucketing, experiments, and a monotonicity-of-k result.
  The later draft sent to Mario contained those components.

## Paper-delivery history

The Slack chronology shows the following progression, though the pasted export
does not preserve calendar dates:

1. Sean implemented the original concave-hull algorithm and partial
   improvements and reported large speedups.
2. Sean sent an overview/write-up with a rough timeline and paper structure.
3. Sean later reported completing the background, algorithm description, and
   runtime analysis, with checkpoint work next.
4. Mario asked Sean to send the completed independent-study paper for review.
5. Sean sent a later draft described as containing the original runtime
   analysis, checkpoint trimming, spatial bucketing, experiments, and the
   monotonicity-of-k proof.

This history supports treating the current repository paper as the continuation
of the independent-study deliverable, now being revised for submission. It does
not establish that Mario has completed a detailed review of the current draft.

## Background recommendation

Mario recommended *Computational Geometry: Algorithms and Applications* by
de Berg et al. as preparation for computational geometry and noted that it was
available through the university library. This is a background resource, not a
required paper citation unless a specific result from it is used.

## Actionable implications

- Keep one shared kNN backend across every benchmark comparison.
- Describe the baseline as a faithful algorithmic reimplementation with a
  controlled shared backend, not as a bit-for-bit reconstruction of the
  unpublished Mathematica package.
- Preserve restart/checkpoint and intersection-strategy ablations so each
  claimed speedup has an identifiable cause.
- Seek an actual advisor review of the submission-shaped GRIVAPP draft; the
  Slack archive records intent to review, not completed approval.
- Keep 3D/n-dimensional work and a full amortized analysis out of the required
  pre-submission scope unless they replace, rather than add to, existing work.
