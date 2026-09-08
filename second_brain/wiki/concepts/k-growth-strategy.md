# k-Growth Strategy

**Type:** concept (new, from the code harness) · **Sources:** [[experiment-harness]]
(`k_growth.py`), draft §3.2 (the cost it reshapes)

## Definition

The rule that decides **how fast k escalates after a failed attempt** — an axis the
original algorithm fixed implicitly at "+1". The harness makes it pluggable
(`k_growth.py`):

- **linear** — k ← k+1, stop at first success. The original's behavior. Returns the
  *minimal* valid k; up to K attempts where K is the answer.
- **geometric** (config name: `exponential`) —
  k ← min(max(k+1, ⌈k·rate⌉), n−1), stop at first success. This explicitly tests
  the all-candidates cap if earlier attempts fail. It uses ~O(log K) attempts, but
  the first success may **overshoot** the minimal k and return a different hull.
  C-MONO-1 means the overshoot cannot be described reliably as smoother or more
  convex.
- **binary_search** — implemented as a bisection for the *smallest* valid k, but
  **not correct in general**. [[k-validity-nonmonotone]] gives
  V(3)=true, V(4)=false, V(5)=true, disproving the monotone predicate bisection
  requires. It is also incompatible with `failure_strategy='checkpoint'`.

## Why it matters

The draft's restart-cost bound (§3.2) is
$C_{\text{total}} = O(n^2 \sum_{k=k_0}^{K} k)$, and the O(n⁴) worst case follows from
summing *linear* growth up to K = n−1. For constant-ratio geometric forward growth,
the tested values form a geometric series with $\sum_j k_j=O(n)$, giving an
**O(n³) worst-case upper bound** under the same per-run model. This does not need
monotone validity: after any failure the schedule continues upward and explicitly
tests the all-candidates cap. Ordinary binary search is excluded because its
success/failure predicate is now proven nonmonotone.

## Trade-off summary

| strategy | attempts | returns minimal k? | per-attempt cost |
|----------|----------|--------------------|------------------|
| linear | O(K) | yes | grows with k |
| geometric (`exponential`) | O(log K) | no (may overshoot) | grows with k |
| binary_search | O(log n) | **no correctness guarantee** | high (starts at n/2) |

## Active-paper reference and experiment

The abstract, Introduction, runtime analysis, and Conclusion now include geometric
growth ($k \leftarrow \min\{\lceil rk \rceil,n-1\}$ for constant $r > 1$) and the
O(n³) upper-bound corollary. The binary-search alternative must stay out: C-MONO-2
supplies the valid→invalid counterexample showing that ordinary bisection is not a
reliable replacement.

The paper-ready 2×2 harness in `growth_factorial_benchmark.py` crosses linear versus
geometric growth with naive versus bucketed intersection checking. It records runtime,
attempt count, sum of attempted k, final k, containment, exact-predicate calls, and area
ratio. After synthetic and real-data smoke validation, the full run completed:
geometric growth improved paired median runtime in all 11 dataset/size
groups, by 1.36–44.57× with naive checking and 1.21–43.52× with bucketing. It reduced
attempts by 1.5–16.3× but matched the linear-growth hull in only 11/110 inputs. See
[[2026-09-01-geometric-growth-factorial]].

## Claims it supports

- **C-KG-1** — k-growth is a tunable axis (linear/exponential/binary_search);
  linear = original. *implemented.*
- **C-KG-2** — old mixed geometric/binary claim; *superseded*.
- **C-KG-3** — geometric forward growth gives an O(n³) restart upper bound under
  the draft's per-run model; *proven*.
- **C-KG-4** — binary search reliably finds the minimum valid k; *contradicted* by
  C-MONO-2. See [[claims]].
- **C-KG-5** — geometric growth reduces practical restart cost/runtime on the tested
  inputs; *verified*, with a changed-hull tradeoff.
- **C-KG-6** — geometric growth plus bucketing gives a 1.89–147.94× practical
  speedup over the original baseline on the tested groups; *verified*.

## See also

[[checkpoint-trimming]] · [[gift-wrapping-walk]] · [[experiment-harness]] ·
[[k-validity-nonmonotone]] · [[k-nonmonotone]]
