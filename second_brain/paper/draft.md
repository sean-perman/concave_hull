# Improvements and Analysis of a k-Nearest Neighbours Approach for the Computation of the Region Occupied by a Set of Points

> **Submission status (2026-08-27):** This Markdown transcription is retained as
> the full historical draft. The active GRIVAPP manuscript is
> `../../scitepress_paper/short_paper_draft.tex`, scoped to runtime analysis,
> spatial bucketing, and k-nonmonotonicity. Checkpoint trimming has moved to
> Future Work for this submission.

**Author:** Sean Perman, Ritchie School of Engineering, University of Denver — sean.perman@du.edu
**Advisor:** Mario Lopez

> Maintainer note (Claude): this file is a faithful transcription of the working
> draft PDF (`Concave_Hull_Paper (4).pdf`, ingested 2026-06-11). Empty sections in
> the PDF are marked *(not yet drafted)*. Section→claim mappings are recorded in
> HTML comments for lint traceability. The author's prose is preserved verbatim
> (including a few typos flagged in `log.md`); do not silently reword.

## Abstract

This paper builds on the k-nearest neighbours concave hull algorithm of Moreira
and Santos for computing the region occupied by a planar point set. Their approach
is a novel variation of gift wrapping in which the next hull vertex is chosen from
the $k$-nearest candidate points, allowing the method to generate either convex or
non-convex boundaries while using $k$ to control smoothness.

We first analyze the runtime of the original algorithm, which its authors left
open. Breaking the cost into nearest-neighbour search, candidate ordering, and
edge-intersection checking, we show that a single run with a fixed $k$ costs
$O(kn^2)$ in the worst case, and that the algorithm's habit of discarding the
entire partial hull and restarting on failure can drive the total cost as high as
$O(n^4)$.

We then introduce two improvements. *Checkpoint trimming* replaces the full
restart with a localized rollback: using the convex-hull vertices as safe
checkpoints, the algorithm rewinds only to the last checkpoint and regrows that
section, preserving the rest of the boundary instead of discarding it. *Spatial
bucketing* accelerates the most expensive step by testing each new edge for
intersection only against nearby edges. On real and synthetic datasets, the
combined method runs up to $13\times$ faster than the restart baseline while
discarding far less work. We also give an eight-point counterexample showing that
$k$ does not control concavity monotonically, so it is best understood as a
heuristic smoothness control rather than a strict dial.

**Keywords:** Concave hull, convex hull, polygon, contour, k-nearest neighbours,
spatial bucketing, computational geometry.

## 1 Introduction

*(not yet drafted — heading only in the source PDF)*

## 2 Background and the Moreira–Santos Algorithm
<!-- claims: C-BASE-1, C-POS-1 -->

### 2.1 The Concave Hull Problem

#### 2.1.1 Convex Hulls and Their Limitations

Convex hull algorithms such as Graham scan [4] and Jarvis march [5] are classical
tools for enclosing a planar point set with the smallest convex polygon containing
all points. They are efficient, well understood, and produce a unique result for a
given input set. However, that uniqueness comes at a cost: the resulting boundary
often over-encloses the data and fails to capture important geometric structure such
as indentations, narrow inlets, or separated lobes.

For many applications, the convex hull is therefore too coarse to serve as a
faithful representation of the region occupied by the points. In particular, when
the data suggest a distinctly non-convex shape, a convex approximation may include
large empty regions that are not meaningfully part of the underlying object or
cluster.

#### 2.1.2 Concave Hulls as Shape Descriptions

The concave hull problem asks for a polygonal boundary that more accurately reflects
the perceived shape of a finite planar point set. Unlike the convex hull, a concave
hull is intended to follow irregularities in the data, including local recesses and
non-convex features. This makes it a more flexible shape descriptor in settings
where geometric detail matters.

A central difficulty, however, is that there is no single canonical concave hull.
Different applications may require different tradeoffs between simplicity,
smoothness, and fidelity to the point set. As a result, most concave hull methods
are inherently parameterized, either explicitly or implicitly, and the chosen
parameter controls how tightly the boundary conforms to the data [3, 1].

#### 2.1.3 Applications of Concave Hull Methods

Concave hull methods arise in a variety of settings where one seeks a meaningful
outer boundary for spatial data. In geographic information systems, they can be used
to estimate footprints or occupied regions from sampled locations. In clustering and
data analysis, they help visualize or extract non-convex cluster boundaries. They
are also relevant in spatial reasoning, where the goal is not merely to enclose
points, but to describe the region those points collectively occupy [3].

### 2.2 The Moreira–Santos K-Nearest Neighbours Algorithm
<!-- claims: C-BASE-1, C-BASE-3 -->

#### 2.2.1 Main Idea

Moreira and Santos [7] proposed a simple and intuitive concave hull algorithm based
on the idea of modifying Jarvis march [5]. Instead of selecting the next hull vertex
from all points, their method restricts attention to the $k$-nearest neighbours of
the current vertex. Among these candidates, it chooses the one that creates the
largest right-hand turn without introducing an intersection with the existing hull.

This restriction makes it possible to construct non-convex boundaries while
preserving the local, step-by-step flavor of gift wrapping [5]. The parameter $k$
governs how local the search is: smaller values tend to produce tighter and more
detailed hulls, while larger values yield smoother and more convex boundaries.

The algorithm begins by selecting an extreme point (minimum $y$-coordinate) as the
starting vertex. From the current hull vertex, it computes the $k$-nearest
neighbours that have not been excluded from consideration. These candidates are then
ordered according to the turning angle relative to the previous hull edge. A greedy
approach is then used to select a valid candidate that produces the largest
right-hand turn without intersecting the existing hull. This process repeats until
the walk returns to the starting point, thereby closing the polygon.

*Figure 1: The k-nearest neighbours approach.*

#### 2.2.2 Failure Cases and Restart Logic

The algorithm has two main failure cases. First, there may be no valid candidates
among the current $k$-nearest neighbours: each candidate edge intersects the
existing partial hull, so the algorithm cannot safely extend the boundary
(**dead end**). Second, after the hull has been closed, some input points may still
remain outside the polygon. In that case, the computed hull fails to enclose the
full point set (**excluded points**).

*Figure 2: All candidate edges intersect the current hull.*

#### 2.2.3 The Role of the Parameter $k$

The parameter $k$ is the central control variable in the algorithm. When $k$ is
small, candidate selection is highly local, allowing the boundary to follow fine
geometric detail and concave features. When $k$ is larger, the set of candidate
vertices broadens, and the resulting hull becomes smoother and closer to a convex
enclosure. In the case where $k = n$, large enough that all remaining points are
considered at each step, the method is identical to the Jarvis-march search and
produces the convex hull.

An important feature of the method is that $k$ is dimensionless: it is not a
geometric distance threshold, but rather a count of neighbours. This distinguishes
it from approaches such as alpha shapes, where the main parameter is directly tied
to spatial scale and may be sensitive to sampling density [2]. In the
Moreira–Santos method, the parameter has a more combinatorial interpretation, which
can make it easier to reason about across differently scaled datasets.

*Figure 3: (left = low $k$), (right = high $k$).*

#### 2.2.4 Comparison with Other Concave Hull Approaches
<!-- claims: C-POS-1 -->

Compared with alpha-shape-based methods and related shape reconstruction techniques,
the Moreira–Santos algorithm has the advantage of conceptual simplicity and a
parameter that is not directly tied to metric scale. In contrast, methods based on
geometric thresholds often require careful tuning relative to point spacing or
sampling density [2, 6].

The k-nearest-neighbours approach is therefore appealing both practically and
theoretically. It offers a direct geometric construction, adapts automatically by
increasing $k$ when necessary, and provides a natural bridge between highly detailed
concave boundaries and more convex approximations. These properties make it a useful
baseline for the improvements developed in the later sections of this paper.

## 3 Runtime Analysis of the Original Algorithm
<!-- claims: C-RT-1, C-RT-2, C-RT-3, C-RT-4, C-RT-5, C-RT-6 -->

### 3.1 Cost of One Successful or Failed Run with Fixed $k$

We first analyze one execution of the original Moreira–Santos algorithm with a fixed
neighbour parameter $k$. Let $n$ denote the number of input points, and let $s$
denote the number of steps completed before that run either closes a hull or fails
and triggers a restart. Since each non-closing step adds a new hull vertex and
removes a point from further consideration, we have $s = O(n)$.

At each step, the algorithm performs three main operations:

**Nearest-neighbour search.** At each step, the algorithm computes the $k$-nearest
neighbours of the current point. The original uses a pre-made nearest-neighbour
function in Mathematica, which internally uses spatial indexing. Even so, for
worst-case analysis we will use the upper bound:
$$T_{\text{knn}}(i) = O(n).$$

**Sorting the candidates.** Once the $k$ nearest neighbours have been selected, they
are sorted by angle relative to the previous hull direction. Sorting $k$ items costs
$$T_{\text{sort}}(i) = O(k \log k).$$

**Intersection checking.** Suppose the partial hull currently contains $i$ vertices.
A candidate edge must be checked against $O(i)$ existing hull edges. Since the
algorithm may test as many as $k$ candidates before finding a valid one or
concluding that no valid candidate exists, the intersection-checking cost at step
$i$ is
$$T_{\text{check}}(i) = O(k\,i).$$

Therefore, the total cost at step $i$ is
$$T(i) = O(n) + O(k \log k) + O(k\,i).$$

Summing over all $s$ steps in the run gives
$$C_{\text{run}}(k) = \sum_{i=1}^{s} \big( O(n) + O(k \log k) + O(k\,i) \big).$$

Separating the three contributions and using the triangular-sum identity
$\sum_{i=1}^{s} i = O(s^2)$:
$$C_{\text{run}}(k) = O(sn) + O(sk \log k) + O(k s^2).$$

Since $s = O(n)$, this yields
$$C_{\text{run}}(k) = O(n^2) + O(nk \log k) + O(k n^2).$$

A completed run also performs a final containment check to verify that all points
lie inside the constructed polygon. In the worst case, this adds at most $O(n^2)$,
which does not change the asymptotic bound above. Since $k \ge 1$, the term $O(kn^2)$
dominates, giving a single run with fixed $k$ worst-case cost:
$$\boxed{C_{\text{run}}(k) = O(k n^2).}$$

### 3.2 Cost of Restarts

The original algorithm may restart with a larger value of $k$ in two cases: first,
when all current candidates would produce an intersecting edge (dead end), and
second, when a closed hull is found but at least one input point lies outside the
resulting polygon (excluded points). In either case, the algorithm discards the
partially constructed hull and restarts from the beginning with $k + 1$.

Suppose the algorithm begins with $k_0$ and eventually succeeds only after trying
the sequence $k_0, k_0 + 1, \dots, K$. Then the total cost is
$$C_{\text{total}} = \sum_{k=k_0}^{K} C_{\text{run}}(k) = O\!\left( n^2 \sum_{k=k_0}^{K} k \right).$$

In the worst case, the algorithm may increase $k$ until $K = n - 1$. Therefore,
$$C_{\text{total}} = O\!\left( n^2 \sum_{k=1}^{n-1} k \right) = O(n^2 \cdot n^2) = \boxed{O(n^4).}$$

### 3.3 Main Takeaways from the Runtime Analysis

The runtime analysis highlights two main sources of cost in the original
Moreira–Santos algorithm. First, within a single run, the dominant expense comes
from edge-intersection checking. As the partial hull grows, each new candidate edge
may need to be tested against more previously constructed hull edges, producing the
triangular-sum behavior that drives the per-run cost.

The second, and more serious, issue is the restart mechanism. When the algorithm
encounters a difficult local configuration, it discards the entire partial hull and
starts again with a larger value of $k$. This means that even if most of the hull
was constructed successfully, a tricky section near the end can force the algorithm
to throw away almost all previous work. As a result, the ratio of wasted work to
retained work can become very large, and the total runtime can grow rapidly. In this
sense, the main weakness of the original algorithm is not only that each run is
expensive, but that local failures trigger repeated global reconstruction.

## 4 Termination Argument
<!-- claims: C-TERM-1, C-TERM-2 -->

*(not yet drafted — heading only in the source PDF. This is the section the ledger
flags as the main theoretical risk; see C-TERM-1.)*

## 5 Checkpoint-Based Trimming Modification
<!-- claims: C-CHK-1, C-CHK-2, C-CHK-3 -->

**1. Motivation.** The checkpoint mechanism is motivated by the observation that the
restart rule in the original algorithm is often too aggressive. When the algorithm
reaches a dead end (all candidate next edges intersect the current hull), the
algorithm abandons the entire partial solution and begins again with a larger value
of $k$. But this suggests two important questions. First, can the amount of discarded
work be reduced? Second, how can the algorithm determine which part of the current
hull is responsible for the dead end? If the failure is local, then only a suffix of
the hull may need to be reconsidered, while the earlier prefix can be preserved.

### 5.1 Convex Hull Vertices as Checkpoints
<!-- claims: C-CHK-2 -->

I propose a checkpoint-based version of the algorithm; we choose the checkpoints to
be the vertices of the convex hull of the input set, listed in cyclic order. This
choice is useful for two main reasons.

First, convex hull vertices are extreme points of the data set, so they are natural
outer anchors for any hull intended to enclose all input points. Under our hull
model, the boundary is constructed from points of the input set and is required to
enclose the full data set. Since the convex hull is the smallest convex set
containing the input, its vertices represent the outermost points of the set. For
this reason, they are the safest points to use as rollback targets: trimming back to
a convex hull vertex preserves a prefix of the walk that is still anchored on the
true outer structure of the point set.

Second, convex hull vertices come with a canonical cyclic order around the data set.
This makes them especially useful for checkpoint-based recovery, since they
partition the boundary into well-defined regions between consecutive checkpoints. The
walk is therefore expected to encounter these checkpoints in order. If the algorithm
reaches a later checkpoint before reaching the expected next one, then it has skipped
part of the outer boundary structure. In that case, the walk has either left some
extreme point outside the current hull, or has moved into a configuration that cannot
be completed correctly without backtracking. This makes checkpoint ordering a natural
consistency condition.

Together, these properties make convex hull vertices good checkpoints. They are
guaranteed outer boundary anchors, they impose a meaningful global order on the walk,
and they provide safe locations to which the algorithm can trim when a local dead end
occurs.

### 5.2 The Trim Operation
<!-- claims: C-CHK-1 -->

Before describing the trim operation, we define a few terms that will be used
throughout this section.

**Definitions.**

- A **checkpoint** is a selected convex hull vertex used as a safe rollback location.
  The checkpoints are ordered cyclically around the point set.
- A **region** is the portion of the boundary between two consecutive checkpoints.
  Each region has its own local value of $k$.
- A **dead end** occurs when the current hull endpoint has no valid continuation
  because every candidate next edge intersects the existing partial hull.
- A **rollback checkpoint** is the checkpoint to which the algorithm trims the hull
  after a dead end is detected.

**Step 1: dead end (trigger).** *(Figure 4)* The trim operation is triggered when
the current hull endpoint reaches a dead end, meaning that every candidate next edge
intersects an existing hull edge. At this point, the walk cannot be safely extended
using the current local value of $k$.

**Step 2: finding the rollback checkpoint.** *(Figure 5)* To determine how far back
the hull should be trimmed, the algorithm considers the highest-priority failed
candidate under the usual angle ordering. It then finds the earliest hull edge
intersected by that candidate. Starting from that conflict location, the algorithm
walks backward along the current hull until it reaches the most recent checkpoint.
This checkpoint becomes the rollback target.

**Step 3: trim and increase $k$.** *(Figure 6)* Once the rollback checkpoint has been
identified, the algorithm removes the suffix of the hull after that checkpoint and
returns the removed points to the active data set so that they may be reconsidered.
It then increases $k$ only for the region beginning at that checkpoint, rather than
increasing $k$ globally for the entire hull. The walk then resumes from the
checkpoint using the preserved prefix of the hull.

**Out-of-order checkpoints.** A trim is also triggered when the walk reaches a
checkpoint out of order. The boundary should encounter checkpoints in order as it
moves around the point set. If the walk reaches a later checkpoint before reaching
the expected next checkpoint, then it has skipped part of the outer boundary
structure. In this case, the newly constructed suffix is rejected and the algorithm
trims back to the current checkpoint. The points removed by this trim are returned to
the active data set, and the local value of $k$ for the affected region is increased
before the walk resumes. This prevents the algorithm from wrapping around the point
set incorrectly and helps preserve the intended region-by-region traversal of the
hull.

**Takeaways.** This modification prevents the algorithm from restarting from the
beginning every time a local failure occurs. Instead, it preserves the valid prefix
of the hull and recomputes only the section that is likely responsible for the
problem. Trimming may be triggered either by a dead end, when no candidate edge can
be added without intersection, or by reaching a checkpoint out of order, which
indicates that the walk has skipped part of the intended outer boundary structure. In
both cases, the algorithm responds locally by preserving useful work and increasing
$k$ only where additional flexibility is needed.

## 6 Spatial Bucketing Improvement
<!-- claims: C-OPT-2 -->

### 6.1 Spatial Bucketing for Intersection Search

I also added spatial bucketing to accelerate the intersection-search step. Instead of
checking a candidate edge against the entire partial hull constructed so far, hull
edges are organized into spatial buckets based on their location. Then, when a new
candidate edge is tested, the algorithm only compares it against edges stored in the
relevant nearby buckets.

This reduces the practical cost of intersection testing quite a bit, since most
candidate edges only interact with a small local part of the hull. If $i$ denotes the
number of hull edges stored in the relevant buckets, then the cost of checking one
candidate becomes $O(i)$ instead of being bounded by the total number of edges in the
partial hull. Thus, checking all $k$ candidates costs $O(ki)$ rather than $O(kh)$,
where $h$ is the number of hull edges constructed so far. The worst-case asymptotic
bound does not improve, since many edges may still fall into the same bucket, but in
practice this makes the intersection step much faster.

## 7 Heuristic Search
<!-- claims: C-HEUR-1 -->

*(not yet drafted — heading only in the source PDF.)*

## 8 Conclusion and Future Work

*(not yet drafted — heading only in the source PDF.)*

## References

(The draft uses its own numeric labels; internal wiki bib keys in brackets.)

1. Matt Duckham, Lars Kulik, Michael Worboys, and Antony Galton. Efficient
   generation of simple polygons for characterizing the shape of a set of points in
   the plane. *Pattern Recognition*, 41(10):3224–3236, 2008. `[duckham2008]`
2. Herbert Edelsbrunner, David Kirkpatrick, and Raimund Seidel. On the shape of a set
   of points in the plane. *IEEE Transactions on Information Theory*,
   29(4):551–559, 1983. `[edelsbrunner1983]`
3. Antony Galton and Matt Duckham. What is the region occupied by a set of points? In
   *GIScience*, pages 81–98, 2006. `[galton2006]`
4. Ronald L. Graham. An efficient algorithm for determining the convex hull of a
   finite planar set. *Information Processing Letters*, 1(4):132–133, 1972. `[graham1972]`
5. R. A. Jarvis. On the identification of the convex hull of a finite set of points
   in the plane. *Information Processing Letters*, 2(1):18–21, 1973. `[jarvis1973]`
6. Z. Liao, J. Liu, G. Shi, and J. Meng. Grid partition variable step alpha shapes
   algorithm. *Mathematical Problems in Engineering*, 2021. `[liao2021]`
7. Adriano Moreira and Maribel Yasmina Santos. Concave hull: A k-nearest neighbours
   approach for the computation of the region occupied by a set of points. In *GRAPP*,
   pages 61–68, 2007. `[moreira2007]`

## Appendix A — Supplementary Material

TODO: Code listings, additional figures, etc. *(placeholder in source PDF)*
