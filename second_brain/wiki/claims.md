# Claims Ledger

The single source of truth for what the paper may assert and how strongly.
See `CLAUDE.md` → "The claims ledger" for status definitions and the golden rule.

Bib keys: `[moreira2007]` original · `[galton2006]` region-occupied criteria ·
`[franklin1989]` uniform-grid intersection detection ·
`[liao2021]` grid alpha-shapes · `[yahya2015]` concave Graham scan ·
internal: `[sean2025]` runtime-analysis draft · `[sean2026]` optimization plan.

## Baseline (the algorithm we improve)

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-BASE-1 | The Moreira–Santos walk produces a valid simple polygon (Jordan curve unless collinear) for k≥3, raising k recursively until all points are interior. | established | [moreira2007] §3, criteria in [galton2006] | Background | The behavior we preserve. |
| C-BASE-2 | The original paper gives no Big-O / worst-case analysis. | established | [moreira2007] §4.3 lists complexity as future work | Background, Runtime | The gap this paper fills. |
| C-BASE-3 | On failure (dead end or excluded points) the original restarts from scratch with k+1, discarding all prior work. | established | [moreira2007] Alg. 1 lines 33, 45; `concavehull.py` recursive call | Runtime, Trimming | Motivates checkpoint trimming. |

## Runtime analysis of the original

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-RT-1 | Finding the start point (min-y) is O(n). | established | scan of all points | Runtime | Uncontroversial. |
| C-RT-2 | Naive k-NN per iteration is O(n). | established | linear scan in `get_k_nearest_points` | Runtime | |
| C-RT-3 | Sort-by-angle is O(k log k), worst O(n log n) when k→n. | established | [sean2025] §4.2 | Runtime | |
| C-RT-4 | Candidate validation is O(k·n), worst O(n²) when k→n. | established | [sean2025] §4.2; **draft §3.1** refines to per-step O(k·i) (i = current hull size), summing to O(k·s²). | Runtime | Each candidate checked vs all hull edges. Draft's per-step form is O(k·i), tighter than the O(k·n) here; consider rewording C-RT-4 to match the draft's triangular-sum framing. |
| C-RT-5 | Average case overall ≈ O(n²) for small constant k over O(n) iterations. | conjectured | [sean2025] §4.2 (informal) | Runtime | **Draft does NOT assert this.** Draft §3.1 derives a *single-run worst case* C_run(k)=O(k·n²) (= O(n²) for constant k), not an average case. Either (a) add a new claim for the single-run O(k·n²) worst bound, or (b) reframe C-RT-5 as that. State assumptions (k=O(1), O(n) iters) explicitly before asserting any average bound. |
| C-RT-6 | Under linear k-growth, repeated restart attempts have a worst-case upper bound of O(n⁴). | proven | [sean2025] §4.3 (informal); active short draft §3.2 derives C_total = O(n² · Σ_{k=1}^{n-1} k) = O(n⁴). | Runtime, Abstract | Proven only as an **upper bound** under the stated per-attempt bound and linear +1 growth. No matching lower-bound construction is given, so never write Θ(n⁴) or call it tight. Promoted 2026-08-27 when the scope-aligned abstract was accepted. |

## Spatial bucketing

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-OPT-1 | Bucketing reduces k-NN to expected sub-linear cost. | conjectured | `knn_query` (grid expansion) in `seans_concavehull_4.py`; [sean2025] §5 | Bucketing | **Not in the draft, and NOT in the experiment harness.** The harness's k-NN (`knn.py`) uses scipy `cKDTree` (tombstoned deletes + lazy rebuild), not a hand-rolled grid; only the *intersection* check is grid-bucketed (→ C-OPT-2). So the "grid bucketing for k-NN" idea currently has no live implementation backing it beyond the older `seans_concavehull_4.py`. Keep distinct from C-OPT-2. **Inconsistency to resolve:** [sean2025] says "expected O(log n)" but a uniform-density grid is closer to expected O(1) amortized. Pick one bound and justify it from the density model. |
| C-OPT-2 | Spatially indexing hull edges gives a practical (constant-factor) speedup to candidate validation. | verified | [franklin1989] establishes uniform grids as intersection-detection prior art; [factorial benchmark 2026-09-01](../experiments/2026-09-01-geometric-growth-factorial.md): 1.40–3.41× with linear growth, 220 schedule-matched identical-output comparisons; [paper benchmark 2026-08-27](../experiments/2026-08-27-spatial-bucketing-paper-benchmark.md): corrected grid, 1.28–3.45×, 6.9–188.6× fewer predicates; [exp 2026-06-12](../experiments/2026-06-12-checkpoint-vs-restart-ablation.md); `intersections.py` | Bucketing | **Verified empirically after the grid-boundary correctness fix.** Franklin et al. supports the general technique, not our implementation-specific exactness or timings. The new factorial corroborates the output-preserving speedup under both linear and geometric growth. *Scope:* practical constant-factor speedup only; the worst case remains unchanged. Do not assert an asymptotic improvement. |
| C-OPT-3 | The optimized main loop runs in O(n log n). | conjectured | [sean2025] §5–6 | Bucketing, Conclusion | **Headline claim, already softened.** [sean2026] §2 explicitly declines to assert a hard asymptotic improvement. Draft may only present this as conjecture/empirical, never as proven. |

## k-growth strategy (new axis from the experiment harness)

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-KG-1 | How fast k escalates after failure is a tunable axis: linear (+1, the original), geometric (constant ratio with an explicit all-candidates cap), or binary-search (bisect for the smallest valid k). | implemented | `concave_hull_experiment/k_growth.py`; [[experiment-harness]] | Runtime, Future Work | Original fixed this implicitly at +1. The geometric implementation now matches the proof: `ceil(k*rate)` capped at `n-1`. **Implementation is not a correctness claim:** the binary-search variant is unsound in general because C-MONO-2 disproves monotone validity. |
| C-KG-2 | Faster k-growth (exponential/binary-search) cuts the number of attempts from O(n) to O(log n), reshaping the §3.2 restart-cost sum — at the cost of overshooting the minimal k (exponential → smoother-than-needed hull) or expensive large-k attempts (binary search). | superseded | [[k-growth-strategy]]; C-KG-3; C-KG-4; C-MONO-2 | Runtime | This mixed claim concealed a correctness difference. Geometric forward growth has the proved bound in C-KG-3; ordinary binary search is contradicted as a reliable minimum-valid-k method by C-KG-4/C-MONO-2. Also do not promise that overshoot makes the hull smoother: C-MONO-1 disproves monotone shape. |
| C-KG-3 | For constant-ratio geometric growth capped at the all-candidates value, the draft's per-run bound gives an O(n³) worst-case restart upper bound. | proven | [[k-growth-strategy]]: tested values form a geometric series, so $C_{total}=O(n^2\sum_j k_j)=O(n^3)$ | Runtime | This is a modified growth rule, not the original algorithm's C-RT-6 bound. It terminates without assuming monotone validity because the cap is explicitly tested. It may skip smaller valid k values and change the hull. |
| C-KG-4 | Ordinary binary search reliably returns the smallest valid k for the Moreira--Santos construction. | contradicted | [validity counterexample 2026-08-31](../experiments/2026-08-31-k-validity-nonmonotone.md): $V(3)=T,V(4)=F,V(5)=T$ | Runtime, Future Work | Binary search requires a false-then-true validity partition. C-MONO-2 disproves that premise for the unmodified fixed-k walk. Do not recommend binary search without a different monotone predicate or separate correctness mechanism. |
| C-KG-5 | Constant-ratio geometric growth reduces practical restart cost and runtime relative to linear growth on inputs that require multiple attempts. | verified | [factorial benchmark 2026-09-01](../experiments/2026-09-01-geometric-growth-factorial.md): all 11 groups improved; 1.36–44.57× paired median speedups with naive checking, 1.21–43.52× with bucketing; attempts fell 1.5–16.3× | Experiments, Conclusion | Verified on the tested real and synthetic inputs for r=2. Geometric growth matched the linear hull in only 11/110 inputs; report final k and area ratio and frame this as a runtime--shape tradeoff, not a quality-preserving optimization or universal speedup theorem. |
| C-KG-6 | Combining r=2 geometric growth with corrected spatial bucketing gives a practical speedup over the original linear-growth, naive-intersection baseline. | verified | [factorial benchmark 2026-09-01](../experiments/2026-09-01-geometric-growth-factorial.md): 1.89–147.94× paired median speedups across 11 dataset/size groups; all outputs valid | Experiments, Abstract, Conclusion | This combines two independent factors. The bucketing component preserves the result for a fixed schedule; the geometric component may change the selected valid hull. Do not present the entire combined speedup as output-preserving. |

## Final-hull validation (new axis from the experiment harness)

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-VAL-1 | The all-points-inside containment check is a selectable mode: off / report (count leaked points, don't act) / enforce (treat a leaky hull as failure → higher-k retry, the original Moreira–Santos correctness rule). | implemented | `concave_hull_experiment/config.py`, `concave_hull.py` (`points_outside_hull`); [[experiment-harness]] | Background, Empirical | `enforce` reproduces the original; `report` separates "leaky" from "wrong" for measurement. `enforce` is incompatible with checkpoint mode (use `report`). |

## Checkpoint trimming (implemented; deferred from the active short paper)

**Submission scope update (2026-08-27):** C-CHK-1 through C-CHK-5 remain valid
project-history claims, but checkpoint trimming is no longer a main-body
contribution of `short_paper_draft.tex`. It may appear only as a compact Future
Work direction in this submission. Do not use these claims to enlarge the active
paper without an explicit scope reversal.

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-CHK-1 | Replace full restart with: trim the hull back to the last checkpoint, increase k only for that region, continue. | implemented | `seans_concavehull_4.trim_to_checkpoint`; **draft §5.2** describes the trim operation (dead-end + out-of-order-checkpoint triggers). | Trimming | Working in code and now written up; not yet measured. Draft adds a second trigger — *out-of-order checkpoint* — beyond the dead-end case; make sure C-CHK-1's statement covers both. |
| C-CHK-2 | Checkpoints are either the 4 cardinal extreme points or all convex-hull vertices (selectable). | implemented | `find_extreme_points`, `compute_convex_hull`, `checkpoint_mode`; confirmed in harness `checkpoints.py` (`select_extreme_points`, `compute_convex_hull`, `checkpoint_strategy` ∈ {none, extreme, convex_hull}) | Trimming | Both modes confirmed in two implementations. **Best mode depends on k-scope (C-CHK-5):** under *per_region* k, `extreme` looked better (exp 2026-06-12); but under *global* k, **`convex_hull` is the winner** (exp 2026-06-13 — convex+global beats restart on all 4 real sets; extreme+global over-raises k and can be worse). So the recommended config is **convex_hull + global**, which *vindicates* the draft §5.1 choice of convex-hull checkpoints (it just needs global k). |
| C-CHK-3 | Trimming (as `convex_hull + global` k) improves practical runtime and reduces wasted work vs the restart baseline. | verified | [exp 2026-06-12](../experiments/2026-06-12-checkpoint-vs-restart-ablation.md) (against, per_region); [exp 2026-06-13](../experiments/2026-06-13-checkpoint-k-scope.md) (for, global — 4 real + 2 synthetic, n→50k) | Trimming, Discussion | **Verified for `convex_hull + global` only** (restated from the original per_region framing, which was contradicted — see C-CHK-5). Beats restart on runtime AND wasted work across all 4 real sets and both synthetic sets at every size (2–13× faster, ⅓–1/10 the work). **Caveat (must hedge in draft):** the hulls still leak ~1–2 pts (C-CHK-4 open), so part of the speed is from quitting slightly early; margins are large enough that fixing the leak is unlikely to erase the win, but the claim isn't a *valid*-and-faster claim until C-CHK-4 closes. |
| C-CHK-4 | Checkpoint mode lacks the original's excluded-points recovery: it returns `success` as soon as the walk closes, so it can produce hulls that fail to enclose all input points. | verified | [exp 2026-06-12](../experiments/2026-06-12-checkpoint-vs-restart-ablation.md); [exp 2026-06-13](../experiments/2026-06-13-checkpoint-k-scope.md); `concave_hull.py:337-346` (no containment recheck); cf. [moreira2007] Alg. 1 lines 39–45 | Trimming, Termination, Discussion | Still open — the **last blocker** to a clean win. `global` k shrinks leakage a lot (redwood 12→0; synthetic per_region 16 → global ~1 at n=50k) but doesn't eliminate it (wolf 5; synthetic ~1–2 pts at 50k). The config forbids `validate_final_hull="enforce"` with checkpoint, and the loop never re-enters on excluded points (`concave_hull.py:337-346`). Fix = add excluded-points recovery. Until then C-CHK-3's win is "faster but ~valid", not "faster and valid". Qualifies C-TERM-1. |
| C-CHK-5 | A *global* rising k (shared across regions) cuts trimming's cost on many-region inputs vs *per-region* k, which forces each region to re-climb from initial_k. | verified | [exp 2026-06-13](../experiments/2026-06-13-checkpoint-k-scope.md); `concave_hull_experiment` `checkpoint_k_scope`, `_bump_region_k` | Trimming, Discussion | redwood convex_hull: per_region 372 rollbacks/14278 edges → global 113/3304, 6× faster. The author's diagnosis. Benefit is specific to many-region (convex_hull) inputs; on few-region `extreme` (4 anchors) global over-raises k and can be *worse* (redwood). This is what makes C-CHK-3 viable. |
| C-OPT-4 | The all-candidates-intersect case can be handled by reordering hull segments to insert the new edge in O(1). | superseded | proposed in [sean2025] §5; **not** implemented — `seans_concavehull_4.py` uses trimming instead | — | Superseded by C-CHK-1. Do not assert. Mention only as an abandoned earlier idea if useful. |

## Termination

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-TERM-1 | The modified algorithm always terminates: the point set is finite and every trim strictly increases per-region k, so it cannot cycle. | conjectured | [sean2026] §3; `region_k_values` increments on trim | Termination | **Main theoretical risk — still unwritten: draft §4 (Termination Argument) is a heading only.** New discrepancy from the draft: §5.2 says the dead-end trim walks back "until it reaches the **most recent checkpoint**" and out-of-order trim goes "back to the current checkpoint" — i.e. the *prose* implies a checkpoint floor, whereas the code/ledger note that `trim_to_checkpoint` allows trimming *past* confirmed checkpoints ("No floor"). Resolve which is true: a floor would make the monotonicity argument far easier; no-floor needs the region-k-increase-dominates argument. Whichever holds, §4 must actually contain the proof. **Update (exp 2026-06-12):** checkpoint *does* terminate, but **not necessarily with a valid hull** (see C-CHK-4 — it can exclude points). So restate any termination claim as "terminates" — not "terminates with a correct/enclosing hull." |
| C-TERM-2 | A global `max_iterations = n³` guard backstops termination in code. | implemented | `seans_concavehull_4.concavehull` | Termination | A safety net is a *smell*: its presence suggests C-TERM-1 isn't yet proven. Either prove C-TERM-1 and frame the guard as defensive, or report it honestly as a current limitation. |
| C-TERM-3 | The original restart algorithm terminates: linear k-growth is bounded, and once all remaining points are candidates the walk reduces to Jarvis march and returns the convex hull. | proven | [moreira2007] restart rule; [jarvis1973]; active short draft abstract and Background §2.2.3 | Abstract, Runtime | This is about the **original restart algorithm**, not checkpoint trimming (C-TERM-1). The body currently states the Jarvis-march endpoint but still needs a compact explicit termination proposition matching the abstract. Use “all remaining points are considered” to avoid an n versus n−1 convention dispute. |

## Heuristics (future work)

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-HEUR-1 | A weighted candidate score (turn angle + distance + direction-to-next-checkpoint + region difficulty) improves stability over angle-only ordering. | open | [sean2026] §4 | Heuristics, Future Work | Untested idea; keep in Future Work until there's evidence. |

## Monotonicity of k

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-MONO-1 | The relationship between k and concavity is not monotone: increasing k can produce a strictly more concave hull (lower area ratio ρ), even when both hulls enclose all input points. | proven | 8-point counterexample in draft §k-nonmonotone: ρ drops from 0.9942 (k=5) to 0.8079 (k=6), both hulls outside=0; verified computationally via `concavity_monotonicity/monotonicity_test.py` | §k-nonmonotone, §2.2.3 (background) | Proven by one clean counterexample. Implication: k is a heuristic smoothness control only. This shape result is distinct from the nonmonotone validity result C-MONO-2. See [[k-nonmonotone]]. |
| C-MONO-2 | Fixed-k validity is not monotone: a valid hull at k does not imply that every larger k succeeds. | proven | [six-point integer counterexample](../experiments/2026-08-31-k-validity-nonmonotone.md): $V(3)=T,V(4)=F,V(5)=T$; `validity_monotonicity/validity_test.py`; two passing regression tests; naive and bucketed backends agree | §k-nonmonotone, Runtime | General-position set with no k-NN distance ties. Distinct from C-MONO-1: this is a success/dead-end reversal, not merely a shape reversal between two valid hulls. Directly contradicts C-KG-4 and rules out ordinary binary search. See [[k-validity-nonmonotone]]. |

## Positioning

| ID | Statement | Status | Evidence | Paper loc | Notes |
|----|-----------|--------|----------|-----------|-------|
| C-POS-1 | Alpha shapes run in ~O(n²); the optimized method aims to beat that. | conjectured | [liao2021]; [sean2025] §5 | Intro, Conclusion | The comparison only holds if C-OPT-3 holds — keep them linked so a downgrade of one downgrades the other. |
