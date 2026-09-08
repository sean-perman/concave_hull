## [2026-06-11] ingest | [moreira2007] Moreira & Santos — original k-NN concave hull

Ingested the original Moreira–Santos (2007) paper, the algorithm this work
improves. Wrote `literature/moreira-santos.md` (source-summary).

- Verified the citations of every claim that leans on this paper, against the
  text + Algorithm 1 listing:
  - C-BASE-1 (valid simple polygon, k≥3, Jordan unless collinear) — §3 + criterion 6. ✓
  - C-BASE-2 (no Big-O; complexity is future work) — criterion 9 (§4.3) + §5. ✓
  - C-BASE-3 (full restart with k+1 on failure) — Alg. 1 lines 33 & 45. ✓
  - C-RT-1 (min-Y start O(n)) — `FindMinYPoint`, line 8. ✓
  - C-RT-2 (naive k-NN O(n)) — `NearestPoints`, line 17. ✓
- No status changes: all the above are already `established` and this paper *is*
  their cited evidence; the ingest confirms rather than moves them.
- Flagged a tension to watch: the paper reports **empirically ≈linear** runtime
  (Fig. 8, unoptimized Mathematica, small n, unit-disk uniform) against our
  `[sean2025]` analysis C-RT-5 (O(n²) avg) / C-RT-6 (O(n⁴) worst). Not a
  contradiction, but the draft must not cite their "linear" as a complexity
  result — it is empirical and unanalyzed by them.
- Added the `moreira2007` entry to `paper/references.bib` (new file).
- `index.md` already catalogs `literature/moreira-santos.md`; no edit needed.

## [2026-06-11] fix | align Obsidian vault with the wiki root

The wiki was scaffolded in `second_brain/`, but the Obsidian vault (the `.obsidian/`
folder) was the subfolder `concavehull algorythem/` — so Obsidian indexed nothing
("no nodes"). Made `second_brain/` the vault by moving `.obsidian/` up to it; matches
CLAUDE.md's declared root. Also: the `wiki/` folder had been dragged into `.obsidian/`
(non-indexed) and lost `concepts/`/`sections/` — restored `wiki/{claims.md,concepts,
sections}` at the root and removed the now-empty `concavehull algorythem/`. Fixed a
bad Obsidian link in the literature note (`[[../literature/galton-duckham]]` →
`[[galton-duckham]]`). A duplicate `claims.md` still sits unused at
`.obsidian/wiki/claims.md` (pending user OK to delete). User must reopen `second_brain`
as the vault in Obsidian.

## [2026-06-11] ingest-draft | working draft (Perman) → paper/draft.md + ledger reconcile

Transcribed `Concave_Hull_Paper (4).pdf` into `paper/draft.md` (faithful; empty
sections marked; section→claim HTML comments added). Synced `paper/references.bib` to
the 7 works the draft cites. Reconciled against the claims ledger:

- **Golden-rule lint: no outright violations.** The draft is conservative — §6
  explicitly states bucketing does NOT improve the worst-case asymptotic bound, and it
  never asserts the O(n log n) headline (C-OPT-3) or the alpha-shape "beat" (C-POS-1).
- **C-RT-6** (worst O(n⁴)): draft §3.2 now contains a full derivation (boxed
  C_total = O(n⁴)). Updated evidence; **recommended promotion conjectured → `proven`**
  as a worst-case *upper* bound, pending human sign-off (achievability/tightness is
  asserted, not constructed). Until promoted, presenting it un-hedged is a latent
  golden-rule tension. Flagged.
- **C-RT-5**: draft does NOT assert an average case; it derives a single-run worst
  case O(k·n²). Noted; suggest adding a claim for that bound or reframing C-RT-5.
- **C-RT-4**: draft §3.1 refines per-step cost to O(k·i) (triangular sum). Noted.
- **C-OPT-2**: added draft §6.1 as evidence; framing matches `conjectured`.
- **C-OPT-1** (k-NN bucketing): not in the draft — draft buckets only intersection
  search. Flagged as currently unsupported by the draft.
- **C-CHK-1**: draft §5.2 documents the trim; adds a second trigger (out-of-order
  checkpoint) beyond dead-end. Evidence updated.
- **C-CHK-2**: draft §5.1 commits to convex-hull-vertex checkpoints only; the
  4-cardinal mode in code is absent from the draft. Draft/code divergence flagged.
- **C-TERM-1**: draft §4 is a heading only (the main theoretical gap). New wrinkle:
  §5.2 prose ("trim to the most recent checkpoint") implies a checkpoint *floor*,
  contradicting the code/ledger "No floor" note. Must be resolved before the proof.
- No status was actually flipped; promotions left as recommendations for the author
  to judge.

Typos noticed in the source (preserved verbatim in draft.md, listed here to fix):
"algorythem" and "reches" (§5 Motivation); several figure captions are literally
"Enter Caption" (Figs 4–6).

## [2026-06-11] meta | add "Concept granularity" rule to CLAUDE.md + exercise on existing nodes

Added a **Concept granularity** section to `CLAUDE.md` (after Page types): list named
concepts during ingest; a concept earns a page only if named/reusable AND referenced
from 2+ places; else fold (bud-off rule); ceiling ~12–18 pages; every concept page
links its claims + sources.

Exercised the rule on the two ingested artifacts ([[moreira-santos]], [[draft]]):

- **Created 4 concept pages:** [[gift-wrapping-walk]] (folds: parameter-k/smoothness,
  min-y start, angle ordering, the two failure cases), [[checkpoint-trimming]] (folds:
  convex-hull-vertex checkpoints, regions & per-region k, dead-end + out-of-order
  triggers, full-restart motivation), [[spatial-bucketing]] (folds: edge-intersection
  checking), [[termination-argument]] (the §4 stub + No-floor risk + n³-guard smell).
  Each links its claim IDs and sources.
- **Folded (no new node):** convex-hull-vertex checkpoints, out-of-order trigger,
  full-restart, parameter k, edge-intersection checking — all sections of the 4 above.
- **Held (create when their source lands):** `concave-hull-problem` + Galton-9-criteria
  → with [galton2006]; `knn-grid-query` → with `code/optimized` (draft has no k-NN
  bucketing); `candidate-heuristics` → future work, single ref (C-HEUR-1).
- Side effect: the previously-phantom `[[gift-wrapping-walk]]` / `[[checkpoint-trimming]]`
  links in `literature/moreira-santos.md` now resolve. `index.md` concepts list updated.
- Running concept-page count: 4 (well under the 12–18 ceiling).

## [2026-06-11] ingest-code | concave_hull_experiment/ → high-level features + new claims

Read the `concave_hull_experiment/` package (modular port of
`legacy/monolithic/seans_concavehull_4.py`;
docstrings cite exact source line ranges). Wrote `code/experiment-harness.md`
enumerating the feature axes, plus concept `wiki/concepts/k-growth-strategy.md`.

Feature axes pulled out (all toggles on `ConcaveHullConfig`):
failure_strategy (restart|checkpoint), checkpoint_strategy (none|extreme|convex_hull),
k_growth_strategy (linear|exponential|binary_search), intersection_strategy
(naive|bucketed), knn_backend (scipy cKDTree), validate_final_hull (off|report|enforce).

Ledger changes:
- **Added C-KG-1** (k-growth is a tunable axis; linear=original) — `implemented`.
- **Added C-KG-2** (faster growth cuts attempts O(n)→O(log n), reshaping the §3.2
  restart sum, at the cost of overshoot / expensive attempts) — `conjectured`.
  This is the most paper-worthy new idea: it directly touches the C-RT-6 O(n⁴) bound,
  which assumes linear +1 growth.
- **Added C-VAL-1** (final-hull validation modes off/report/enforce; enforce =
  original correctness rule) — `implemented`.
- **C-CHK-2**: both checkpoint modes (extreme, convex_hull) now confirmed in a second
  implementation (`checkpoints.py`). Evidence updated; draft/code divergence still open.
- **C-OPT-1**: flagged that the harness's k-NN is scipy `cKDTree` (tombstone + lazy
  rebuild), NOT grid bucketing — so "grid bucketing for k-NN" has no live backing here;
  only the intersection check is grid-bucketed. Keep C-OPT-1  vs C-OPT-2 distinct.
- **C-OPT-2**: added `intersections.py` (`BucketedIntersectionIndex`, exact supercover
  rasterization, auto cell size ≈ extent/√n) as a second implementation. Still
  `conjectured` — harness worst case still degrades, matching draft §6.1.

Experiment status: `benchmark.py`'s default VARIANTS already compare restart-naive vs
restart-bucketed vs checkpoint-convex_hull and record wasted-edges + restart/rollback
counts — i.e. the exact instrument to move **C-CHK-3** to `verified`. But no numeric
results were reported (only `results/<date>/*.png` plots exist). Per the experiment-log
rule, C-CHK-3 stays `conjectured` until the human reports measured numbers. Did NOT
fabricate results from the PNGs.

Concept-page count now 5.

## [2026-06-12] ingest-data | datasets/ → code/datasets.md

Characterized the 5 test clouds (measured counts/extents/dups) and filed
`code/datasets.md`. Easy→hard ladder: capitals/cities (sparse near-convex) →
redwood/wolf (real concave strip/spread) → star_8_tips (deep synthetic concavity,
the C-CHK-3 stress case). Provenance: `_extract.py` pulls 4 real geo sets from
`legacy/monolithic/seans_concavehull_4.py` literals + procedural star (seed 42,
300 pts).

Findings worth a sentence in the draft (recorded on the page as limitations):
- **Antimeridian wrap** in `world_capitals` (x ∈ [−175.2, 179.2]) — planar Euclidean
  treats date-line-adjacent capitals as ~354° apart; a limitation of running on raw
  lon/lat, and a wrinkle for the k-dimensionless argument (draft §2.2.3): k is a
  count but the metric it ranks is wrong on the sphere.
- **Duplicate points**: redwood 33, cities 17 — exercise `cleanList` dedup
  ([moreira2007] Alg. 1 line 2) on real data.
- Sizes ≤1190 → qualitative/shape figures only; runtime scaling comes from the
  procedural sweep, not these.
No new claims (these are inputs/limitations, not assertions). No status changes.

## [2026-06-13] experiment | checkpoint-vs-restart ablation → C-CHK-3 contradicted, C-OPT-2 verified

Logged `experiments/2026-06-12-checkpoint-vs-restart-ablation.md` (6-variant factorial,
2 real + 2 synthetic datasets, run 2026-06-12). Ledger moves, all with linked evidence:

- **C-CHK-3 → `contradicted`.** Across all four datasets, checkpoint trimming wastes ≥ as
  much total work as the valid (`enforce`) restart baseline (many small rollbacks vs few
  big restarts), is usually slower, and returns invalid hulls. The paper's intended
  headline does not hold as implemented.
- **C-OPT-2 → `verified`** (restated to the empirical speedup: 1.3–8×, identical hulls;
  asymptotic form stays conjectured per draft §6.1).
- **Added C-CHK-4 (`verified`):** checkpoint omits the original's excluded-points recovery
  (`concave_hull.py:337-346` returns success on close without a containment recheck; cf.
  [moreira2007] Alg.1 L39–45), so it leaks 3–16 points on every set ≥1000 pts. Root-cause
  traced. Fixing it would likely *raise* checkpoint's wasted work, not lower it.
- **C-CHK-2:** experiment shows `extreme` > `convex_hull` (less waste + leakage). Note: the
  draft §5.1 argues for `convex_hull` — the mode that tested *worse*. Reconcile.
- **C-TERM-1:** qualified — checkpoint terminates but not necessarily with a *valid* hull.

⚠️ **Golden-rule flag for the draft:** `paper/draft.md` §5 still presents checkpoint
trimming positively ("preserves useful work"), which now asserts a `contradicted` claim
(C-CHK-3) and ignores C-CHK-4. The draft is currently overstating the contribution and must
be revised (or the bug fixed + re-measured) before that section is honest. Not yet edited —
flagging per "never leave the draft silently wrong."

## [2026-06-13] experiment | checkpoint k-scope (global vs per_region) → C-CHK-3 revived

Author's insight: checkpoint's high cost came from **per-region** k (each region re-climbs
from initial_k; convex_hull has many regions). Implemented a new `checkpoint_k_scope` axis
(`per_region` | `global`) in `concave_hull_experiment` (`config.py`, `_bump_region_k` in
`concave_hull.py`) and ran the 5-variant comparison on the 4 real sets
(`results/2026-06-13/benchmark_16-03-56.csv`). Logged
`experiments/2026-06-13-checkpoint-k-scope.md`.

Result: **`convex_hull + global` beats the valid restart baseline on all 4 real sets** —
less wasted work AND faster (redwood 13×, ⅕ the work, valid). `global` reduces rollbacks/
waste vs `per_region` almost everywhere (exception: few-region `extreme`, where global
over-raises k). Ledger moves:

- **C-CHK-3:** `contradicted` → **`conjectured`** (promising). The per_region contradiction
  stands, but the global variant supports the claim. Not `verified` yet (wolf still leaks;
  synthetic sweep not rerun). Supersedes last turn's flat contradiction.
- **Added C-CHK-5 (`verified`):** global k avoids per-region re-climbing; the mechanism
  behind the win. Specific to many-region (convex_hull) inputs.
- **C-CHK-2:** best mode flips with scope — `convex_hull + global` is now the winner, which
  *vindicates* draft §5.1's convex-hull choice (it just needed global k).
- **C-CHK-4:** still open — global mitigates leakage (redwood 12→0) but wolf still leaks 5.
- Updated [[checkpoint-trimming]] concept + `code/experiment-harness.md` (new axis).

Note: the earlier golden-rule flag on draft §5 softens — trimming may be defensible after
all, but only as `convex_hull + global`, and only once the leak (C-CHK-4) is fixed.

## [2026-06-13] experiment | synthetic n-sweep confirms convex_hull+global → C-CHK-3 verified

Ran the 5 k-scope variants on unit_disk + star (n→50k, 5 seeds);
`results/2026-06-13/benchmark_17-08-52.csv`; appended results to
`experiments/2026-06-13-checkpoint-k-scope.md`. **`convex_hull + global` beats restart at
every size on both synthetic sets** (2–5× faster, ⅓–1/10 wasted work) — the real-data win
holds at scale. Leak under global is small but persistent (~1–2 pts / 50k vs per_region's
16). Moved **C-CHK-3 → `verified`** (scoped to convex_hull+global, runtime/wasted-work
improvement), with **C-CHK-4 (residual leak) as the standing caveat** — the only thing
between here and a "faster *and* valid" claim. Updated C-CHK-3/4 rows.

## [2026-06-12] revise | datasets page reframed around use case + prospective applications

Reworked `code/datasets.md` to lead with **use case** rather than geometry, per
request. Taxonomy: (1) synthetic/benchmark — uniform unit disk is exactly what
[moreira2007] §4.2 used for timing + the adversarial star; (2) GIS footprints — split
into species-range (wolf, redwood) and settlement (cities, capitals), the original
LOCAL-project motivation. Added two **prospective use cases** the method could serve:
(3) cluster-boundary extraction (post-clustering, e.g. SNN as in the original, or 2-D
embeddings — outline non-convex clusters / flag outliers), and (4) sensor & coverage
footprints (LIDAR obstacle outlines, drone/satellite survey coverage, GPS traces).
These feed draft §1 (applications) and §8 (future work); no datasets exist for (3)/(4)
yet. Kept the compact characterization table + gotchas (antimeridian, dups, sizes).

## [2026-06-12] assess | dataset coverage gaps + fixed datasets.md orphan

Linked `code/datasets.md` from `experiment-harness.md` ([[datasets]]) — it was an
orphan (no inbound links), which both hid it in the graph and tripped the orphan lint.

Coverage assessment added to `code/datasets.md`. Verdict: good easy→hard ladder of
real single-blob shapes + one tunable adversarial synthetic, but blind spots. Priority
gaps: (1) **non-uniform density / separated clusters** — the algorithm's own documented
hard case ([moreira2007] Fig. 6b / Fig. 2), currently untested; (2) an adversarial case
for checkpoint trimming itself (few CH vertices + deep interior concavity, where trim ≈
restart) to keep C-CHK-3 honest; (3) degenerate geometry (collinear/lattice/cocircular)
for the termination risk C-TERM-1 + n³-guard smell. Lower: variable intra-shape density,
annulus/hole (limitation figure). Methodological steer: synthetic *families as axes*
(sweep separation, concavity depth; seeded) carry quantitative claims; real CSVs are
qualitative figures.

## [2026-06-13] lint | full vault review + mechanical sync fixes

Ran the CLAUDE.md lint over the whole vault. Findings, then the safe fixes applied
(draft edits and the C-RT-6 promotion left for the author — judgment calls).

Applied:
- **Deleted the stale duplicate ledger.** Removed the entire `.obsidian/wiki/` folder
  (a pre-2026-06-11 snapshot of `claims.md` that still showed C-CHK-3/C-OPT-2 as
  `conjectured` and lacked C-CHK-4/5, C-KG-1/2, C-VAL-1, plus two empty `concepts/`/
  `sections/` dirs). It contradicted the live ledger and polluted the graph.
- **Synced [[checkpoint-trimming]] to the ledger.** Experimental-status section now
  reflects C-CHK-3 → `verified` (convex_hull+global, after the synthetic n-sweep), and
  the claims-it-supports footer lists C-CHK-3 (verified), C-CHK-4, C-CHK-5 — previously
  it stopped at the per_region→global revival and still called C-CHK-3 conjectured.
- **Synced [[spatial-bucketing]] to the ledger.** C-OPT-2 reframed from the
  `conjectured` asymptotic "expected O(1)" form to the `verified` constant-factor
  speedup (asymptotic form still conjectured).
- **Fixed `index.md` literature table.** Marked the five phantom pages (galton-duckham,
  alpha-shapes-grid, concave-graham, sean-2025-runtime, sean-2026-plan) as *not yet
  written*; flagged `yahya2015` as not in `references.bib` / uncited; noted
  [sean2025]/[sean2026] as the most-cited internal sources still lacking pages.
- **Annotated the broken `[[galton-duckham]]` forward-link** in [[moreira-santos]] as a
  planned page.

Flagged, NOT changed (need author judgment):
- **Golden-rule, draft §5:** the trim write-up describes **per-region** k (the variant
  exp 2026-06-12 *contradicted*) and never mentions global k or the C-CHK-4 leak. The
  verified win is `convex_hull + global` only. §5 currently presents the losing config
  positively and omits the leak caveat — revise the section, or fix the excluded-points
  bug and re-measure, before it is honest.
- **C-RT-6** is boxed un-hedged in draft §3.2 but is `conjectured`; ledger recommends
  promotion → `proven` (upper bound) pending sign-off on achievability.
- **§4 Termination** still a stub; floor vs. "No floor" contradiction (draft §5.2 prose
  vs. code) unresolved — determines the proof shape.
- **Missing layer:** `wiki/sections/` (section-briefs) does not exist, though CLAUDE.md
  and index.md treat briefs as the page type the draft is written from.
- **Missing pages:** [sean2025]/[sean2026] summaries (most-cited internal sources).
Other citations are consistent: the draft's 7 numeric refs all resolve in
`references.bib` and nothing in the bib is uncited.

## [2026-06-17] ingest-draft | §k-nonmonotone + Future Work → new concept + claim

Reviewed the current full draft (`concave_hull_paper.tex`). Two new sections added
since last ingest: the §k-nonmonotone counterexample section and an expanded §Future
Work. Changes to the second brain:

- **Created `wiki/concepts/k-nonmonotone.md`** — the non-monotone k behavior and the
  area ratio ρ metric. Referenced from §2.2.3 (background, now hedged "tends to be
  smoother") and the new dedicated §k-nonmonotone. Meets the 2+ reference threshold.
- **Added C-MONO-1 → `proven`** — "k does not monotonically control concavity":
  ρ drops from 0.9942 (k=5) to 0.8079 (k=6) on the 8-point set, both hulls outside=0.
  Verified computationally (`monotonicity_test.py`). One clean counterexample is enough
  to prove the claim.
- **Updated `wiki/concepts/k-growth-strategy.md`** — noted that §Future Work now
  explicitly names geometric growth (k ← ⌈rk⌉) and that the binary-search direction
  carries a new qualification from C-MONO-1 (if valid → invalid transitions can occur,
  bisection needs a correctness argument).
- **Did NOT create pages for:** parallel construction (single ref, future work),
  amortized analysis (single ref, future work), excluded-points recovery (already
  tracked as C-CHK-4 and folded into [[checkpoint-trimming]] — not yet large enough
  to bud off).

Concept-page count now 6.

## [2026-07-29] ingest-venue | GRAPP lineage → GRIVAPP 2027 submission plan

Confirmed that the original Moreira--Santos paper was published at the Second
International Conference on Computer Graphics Theory and Applications
(**GRAPP 2007**, Barcelona, pp. 61--68). The organizer states that, beginning in
2026, GRAPP, IVAPP, and HUCAPP merged into **GRIVAPP**. Recorded **GRIVAPP 2027**
as the target venue in `paper/grivapp-2027-submission.md`.

Key dates recorded from the official call: Regular Paper **2026-09-15** (primary),
second Position/Regular Paper round **2026-10-22** (fallback), notification
2026-11-13, camera-ready 2026-11-27, conference 2027-02-26 through 2027-02-28.
Also recorded the double-blind, SCITEPRESS-template, 10,000--50,000-character,
publication-length, and AI-disclosure requirements.

Author constraint: limited working time and an already-long draft. Current
`concave_hull_paper.tex` is approximately 7,114 words / 41,622 non-whitespace
LaTeX characters. Adopted a **minimum viable submission** rule: do not add new
research by default; keep existing claims honest, satisfy venue requirements,
compress repetition, and move nonessential unresolved work to a short Future
Work section.

Submission strategy:

- Preserve the runtime analysis, exact spatial-bucketing result, global-k
  checkpoint experiment, and visible excluded-points limitation.
- Keep the k-nonmonotonicity counterexample if it fits after compression.
- Treat checkpoint-aware excluded-points recovery, broader evaluation,
  boundary-quality metrics, amortized/tight analysis, parallel construction,
  richer heuristics, and k-growth experiments as explicitly deferrable.
- Never convert limited time into an overstated "faster and valid" claim:
  C-CHK-4 remains a disclosed limitation.
- Remove the empty supplementary placeholder and compress Future Work/repeated
  motivation before cutting evidence-bearing material.

No claim statuses or draft text changed in this ingest; this entry records the
venue, deadline, and author-approved scope policy.

## [2026-07-29] ingest-advisor | Slack history → project decisions and experiment control

Ingested the paper-relevant parts of Sean Perman's pasted Slack history with
Mario Lopez into `paper/advisor-guidance.md`. The pasted export contains message
times but not calendar dates, so no event dates were inferred.

Durable advisor guidance:

- Mario selected the concave-hull paper over the alternative
  curse-of-dimensionality direction as the appropriate computational-geometry
  project.
- After Sean reported an implementation and large speedups, Mario suggested
  considering publication in the same forum used by the original authors. This
  is historical support for the GRAPP → GRIVAPP target.
- For the baseline comparison, Mario directed Sean to implement the original
  algorithmic version and use the **same kNN implementation** in the baseline
  and enhanced algorithms.

Verified the last point against the current harness: `ConcaveHullConfig` permits
only `knn_backend="scipy"`, so all restart/checkpoint and naive/bucketed variants
share the same SciPy `cKDTree` backend. Updated `code/experiment-harness.md` to
record this as an advisor-directed experimental control. Added the necessary
caveat: this is a controlled reimplementation, not evidence that the unpublished
2007 Mathematica package used a KD-tree.

Also recorded, as provenance rather than advisor-approved results: Sean's
amortized-analysis plan, early 3D/n-dimensional idea, segment-tree/spatial-hash
exploration, staged paper updates, and delivery of an independent-study draft
containing runtime analysis, checkpoint trimming, spatial bucketing,
experiments, and the k-monotonicity result. Mario's messages show intent to
review the completed paper, but the archive does not establish that a detailed
review of the current draft occurred.

Unrelated recommendation-letter, GTA, course-registration, health, and other
administrative/personal conversation was intentionally not ingested. No claim
statuses or paper text changed.

## [2026-08-27] revise-scope | short-paper submission pivot + abstract

The author chose a narrower GRIVAPP submission shaped for a possible 8-page
Short Paper. Created `scitepress_paper/short_paper_draft.tex` from existing prose
without rewriting retained passages and kept the full SCITEPRESS draft intact.
The new source compiles to 7 A4 pages; before the abstract insertion it measured
approximately 20,403 rendered non-whitespace characters, safely within the
venue's 10,000--50,000 range.

Active main-body story, in order: Introduction; Background and the
Moreira--Santos Algorithm; Runtime Analysis; Spatial Bucketing; Experimental
Evaluation; k-Nonmonotonicity; Future Work; Conclusion. **Checkpoint trimming is
no longer a submission contribution** and has moved to Future Work. Its code,
experiments, claims, and concept notes remain project history rather than being
deleted.

Inserted the author-approved scope-aligned abstract into the short draft. It
claims: O(kn²) per fixed-k attempt; O(n⁴) total upper bound under linear k-growth;
termination of the original restart algorithm once all remaining points are
considered and the walk reduces to Jarvis march; measured 1.3--8x speedups from
uniform-grid spatial bucketing with identical hulls; and the proven eight-point
k-nonmonotonicity counterexample under the area-ratio measure.
After insertion, the compiled draft remains 7 pages and measures approximately
21,627 rendered non-whitespace characters / 4,221 rendered words.

Ledger reconciliation:

- **C-RT-6 → `proven`**, explicitly only as an O(n⁴) upper bound under linear
  +1 growth; no tight Θ(n⁴) claim.
- Added **C-TERM-3 (`proven`)** for termination of the original restart
  algorithm, kept distinct from the deferred/unresolved checkpoint-termination
  claim C-TERM-1. The body still needs a compact proposition matching the
  abstract.
- Marked the entire checkpoint claim family as out of scope for the active main
  body without changing the underlying implementation/experiment statuses.

Submission review recorded the remaining high-priority work: add contribution
and roadmap paragraphs; correct the Graham-scan/Jarvis-march complexity sentence;
remove the unsupported claim about Mathematica internally using a spatial index;
state the runtime proof's computational model; add the existing naive-vs-bucketed
results table plus environment/variability/reproducibility details; qualify
"more concave" as area-ratio-specific; compress orphaned checkpoint Future Work;
complete the conclusion; improve/refer to figures; and anonymize the review copy.

## [2026-08-27] revise-abstract | finalize for computational-geometry students

Finalized the active short-paper abstract after author review. The approved
version treats the abstract as a high-level map of the paper rather than
explaining the bucketing mechanism: runtime upper bounds and termination;
edge-intersection checking and reconstruction as the identified costs; uniform-
grid spatial bucketing with a measured 1.3--8x speedup and unchanged hulls; and
the eight-point k-nonmonotonicity counterexample. Language is calibrated for a
computational-geometry student audience. No claim status or paper scope changed.

## [2026-08-27] revise-introduction | replace inherited full-paper opening

Replaced the active short paper's introduction with the author-approved
three-paragraph version. The new opening is deliberately concise: use-case
motivation for concave hulls; the Moreira--Santos restart/runtime gap; and the
three retained contributions (runtime/termination, measured spatial-bucketing
speedup, and k-nonmonotonicity). Removed the separate roadmap because the
contribution paragraph already follows the paper's section order. No Background
content or claim status changed.

## [2026-08-27] revise-background | compress concave-hull definition

Removed the nested Background subsections "The Concave Hull Problem," "Convex
Hulls and Their Limitations," "Concave Hulls as Shape Descriptions," and
"Applications of Concave Hull Methods" from the active short draft. Replaced
them with the author-approved single paragraph defining convex and concave hulls,
non-uniqueness, and parameterized boundary detail. The Moreira--Santos algorithm
now begins as Section 2.1. No claims changed.
## [2026-08-27] experiment | corrected spatial-bucketing paper benchmark

Fixed the uniform-grid rasterizer's boundary/corner omission: the previous
midpoint-only traversal did not register cells touched only at endpoints or exact grid
crossings, so an intersecting edge could be absent from the query candidates. Added
direct geometry tests, exhaustive Shapely differential coverage, randomized index
comparisons, and a full lattice-hull regression. All 20 tests pass.

Created `concave_hull_experiment/paper_benchmark.py` and ran the publication-focused
restart-naive vs restart-bucketed comparison. The final run contains 120 paired trials
(240 raw observations), alternates execution order, warms lazy dependencies, enforces
containment, saves raw timings, records environment + source hash, and collects exact
predicate calls in a separate untimed pass. All paired outputs were identical and valid.

Median paired speedups range from 1.28× (world capitals) to 3.45× (coast redwood);
synthetic results range from 1.42× to 2.80×. Bucketing reduces exact intersection calls
by 6.9–188.6×. Updated C-OPT-2 with the corrected evidence and logged the artifacts in
`experiments/2026-08-27-spatial-bucketing-paper-benchmark.md`. The earlier instrumented
timing run is explicitly marked preliminary and must not be used in the paper.

## [2026-08-27] ingest | corrected bucketing evidence synchronized across the wiki

Folded the publication benchmark into [[spatial-bucketing]], [[experiment-harness]],
the GRIVAPP scope plan, and the index. The canonical paper claim is now consistent
throughout the Second Brain: corrected spatial bucketing is an exact candidate filter
with a verified 1.28–3.45× median runtime speedup and 6.9–188.6× fewer exact-predicate
calls across 120 paired trials, with identical valid hulls. Recorded the repaired
endpoint/grid-line/grid-corner supercover condition and its 20-test correctness gate.

Paper-use guardrails: make only a practical constant-factor claim, use the final
`paper_benchmark_12-21-39_*` artifacts, and omit or qualify the world-capitals result
because raw longitude/latitude retains the antimeridian limitation. No new concept page
was created because the evidence belongs to the existing [[spatial-bucketing]] node.

## [2026-08-27] revise-structure | move hull definitions into Introduction

Expanded the active Introduction's opening paragraph with the author-approved
convex/concave-hull context, including concave-hull non-uniqueness and the need
for a detail-control rule. Removed the duplicate definition paragraph from
Section 2, renamed that section "The Moreira--Santos Algorithm," removed the
redundant same-named subsection, and promoted its four subtopics to subsections.

During the edit, reconciled the abstract and Introduction with the corrected
publication benchmark already recorded in the wiki: replaced the preliminary
1.3--8x range with the canonical 1.28--3.45x median paired speedup. No other
claims changed.

## [2026-08-31] experiment | fixed-k validity is nonmonotone

Found and minimized a counterexample to the assumption required by binary search
for the smallest valid k. The six-point integer set
`{(9,9),(7,9),(0,2),(0,8),(4,7),(3,1)}` produces a valid enclosing hull at k=3,
a dead end at k=4, and a valid enclosing hull at k=5. The set has no collinear
triple and no equal-distance nearest-neighbour tie. The naive and corrected
bucketed intersection backends agree.

Added the reproducible seeded search, saved coordinates, three-panel figure, and
two regression tests under `studies/validity_monotonicity/`; both tests pass and a
1,000-trial rerun rediscovers the example at trial 629. Logged full method and
artifacts in `experiments/2026-08-31-k-validity-nonmonotone.md` and created
[[k-validity-nonmonotone]].

Ledger changes: added **C-MONO-2 (proven)** for nonmonotone validity; added
**C-KG-4 (contradicted)** for reliable minimum-valid-k binary search; superseded
the old mixed C-KG-2; and added **C-KG-3 (proven)** for the O(n³) geometric-growth
restart upper bound under the draft's existing per-run model. The author considers
the counterexample likely paper material. The scope plan now routes it into the
existing Monotonicity section, not a new section; the active TeX draft has not yet
been changed.

## [2026-08-31] revise-paper | integrate nonmonotone validity and geometric growth

Integrated the six-point validity counterexample into the active SCITEPRESS draft.
Renamed Section 6 to "Non-Monotone Effects of k," compressed but retained the
eight-point area-ratio counterexample, and added a second subsection with the exact
integer coordinates, k=3/4/5 walks, general-position and no-distance-tie checks,
three-panel figure, and true→false→true validity conclusion. The paper now rules
out ordinary binary search for the smallest valid k.

Added the C-KG-3 corollary to the restart analysis: constant-ratio geometric growth
has a geometric tested-k sum, so the existing O(kn²) per-run model yields an O(n³)
restart upper bound. Updated the abstract, Introduction contribution paragraph,
and Conclusion, and removed the stale commented binary-search Future Work paragraph.

The TeX build succeeds with no overfull boxes or undefined references. Visual
inspection of all pages confirms legible two-column text and figures; the revised
paper remains seven A4 pages.

## [2026-08-31] revise-paper | collapse runtime takeaways into transition

Removed the standalone Section 3.3 "Main Takeaways from the Runtime Analysis,"
which duplicated the final Conclusion and still emphasized the deferred checkpoint
direction. Preserved its useful function as one compact closing paragraph in
Section 3.2: per-attempt intersection checking and the cross-attempt k-growth
schedule are identified as independent optimization targets; spatial bucketing,
geometric growth, and the nonmonotone-validity constraint are linked explicitly.
Section 4 now opens directly with the per-attempt target instead of repeating the
same motivation. The rebuilt paper remains seven A4 pages with no overfull boxes
or undefined references, and all pages passed visual inspection.

## [2026-09-01] implementation | geometric-growth paper benchmark prepared

Aligned `ExponentialKGrowth` with the schedule proved in the active paper: failed
attempts now advance with `ceil(k*rate)`, guarantee at least +1 progress, and explicitly
test the `n-1` all-candidates cap instead of stopping when a multiplication overshoots
it. Added four schedule regressions covering doubling, fractional-rate ceiling, cap
termination, and success termination.

Added `concave_hull_experiment/growth_factorial_benchmark.py`, a publication-focused
2×2 experiment crossing linear/geometric growth with naive/bucketed intersections.
It uses paired inputs, balanced execution order, isolated workers, untimed predicate
instrumentation, enforced containment, within-schedule hull-equality assertions, raw
and summary CSVs, environment/source metadata, and an auto-generated LaTeX table. It
also records attempted k values, sum of k, restarts, wasted edges, final k, hull area
ratio, and whether geometric growth changed the hull.

All 30 repository tests pass under the arm64 Miniforge Python. Synthetic unit-disk and
eight-tip-star smoke runs plus a U.S.-cities smoke run completed end to end. Smoke
results are not paper evidence and were written under `/private/tmp`; no empirical
geometric-growth claim was promoted. Added C-KG-5 as `conjectured` pending the full
default benchmark and recorded the paper command and interpretation guardrails in the
GRIVAPP submission plan.

## [2026-09-01] ingest-source | uniform-grid intersection reference

Added [franklin1989] as prior art for uniform-grid intersection detection and
integrated it into the active Spatial Bucketing Improvement section. Expanded the
section with the implementation's automatic cell width, exact segment supercover,
boundary/corner handling, edge-ID deduplication, and final exact-predicate step.
The citation supports the general indexing technique; implementation exactness and
the 1.28–3.45× speedup remain supported by our tests and paired benchmark. Updated
the literature index, spatial-bucketing concept, C-OPT-2 evidence, and both BibTeX
databases. The rebuilt manuscript remains seven A4 pages with resolved references.

## [2026-09-01] experiment | geometric-growth × bucketing factorial completed

Ran the full publication benchmark with r=2: 110 paired inputs across unit disk and
eight-tip star at n=1k, 5k, 10k, and 50k plus U.S. cities, gray wolf, and coast
redwood; 10 trials per dataset/size group. The run produced 440 timed observations.
All configurations succeeded with zero points outside, and all 220 schedule-matched
naive/bucketed comparisons returned identical ordered hulls.

Geometric growth improved paired median runtime in all 11 groups: 1.36–44.57× with
naive checking and 1.21–43.52× with bucketing. It reduced attempts by 1.5–16.3× and
the sum of tested k values by 1.33–17.80×. Bucketing under linear growth gave
1.40–3.41×, while the combined configuration gave 1.89–147.94× over the original.
Geometric growth matched the linear hull in only 11/110 inputs; the other 99 had a
higher area ratio in this run. The result is therefore logged as a runtime--shape
tradeoff, not an output-preserving improvement or monotonicity claim.

Promoted C-KG-5 to `verified`, added verified C-KG-6 for the combined configuration,
and attached the factorial as corroborating evidence for C-OPT-2. Added
`experiments/2026-09-01-geometric-growth-factorial.md` with the full table, controls,
caveats, and artifact paths. Integrated the generated table and results into the
active SCITEPRESS paper. The forced TeX build succeeds at 8 A4 pages with no overfull
boxes or undefined references; visual inspection confirms the table, conclusion, and
references render cleanly.

## [2026-09-03] revise-paper | import current-draft prose and figure layout

Updated the active `scitepress_paper/short_paper_draft.tex` from the author-supplied
current draft. The revision refines the factorial experiment setup and timing prose,
expands the explanations for both k-nonmonotonicity counterexamples, and moves the
full-width results and shape-counterexample figures earlier in their sections. Kept
the results caption active because the surrounding prose cites its figure label; the
supplied commented caption would otherwise create an undefined reference.

Rebuilt the canonical PDF and the portable Overleaf bundle. The bundle now includes
`growth-factorial-results.pdf`, which was missing from the previous archive. Both the
repository source and portable `main.tex` compile successfully to 8 A4 pages with no
undefined references or LaTeX errors. A rendered review of all pages found no clipped
text, overlaps, broken figures, or unreadable labels.

## [2026-09-07] revise-paper | promote author-supplied draft and review submission readiness

Promoted the author-supplied LaTeX text to the active
`scitepress_paper/short_paper_draft.tex`, updated the portable Overleaf bundle, and
rebuilt `output/pdf/concave_hull_grivapp_draft.pdf`. Repository and portable builds
both succeed at eight A4 pages with resolved citations and references. Kept the
factorial-results caption active because the surrounding prose cites that numbered
figure.

The review found no visual defects and confirmed the reported factorial ranges and
the rounded eight-point counterexample. The current draft is not submission-ready:
the abstract claims a termination proof while the body contains a visible proof
TODO; the unqualified O(n^4) and termination claims need the input assumptions stated
in the termination discussion; the nearest-neighbour cost model attributes an
undocumented spatial index to the original Mathematica implementation; and the
review copy still identifies the authors.

## [2026-09-07] revise-paper | clarify Mathematica nearest-neighbour cost model

Checked the original Moreira--Santos paper and Wolfram's product history. The paper
describes `NearestPoints` as a helper in its Mathematica package but does not state
its data structure or selection algorithm. Wolfram documents the built-in `Nearest`
and `NearestFunction` as new in Mathematica 6.0, whereas the paper's Mathematica
reference was visited in October 2006. Removed the unsupported spatial-index claim
from the runtime section and retained `T_knn(i)=O(n)` as an explicit favorable
worst-case assumption made to give the original implementation the benefit of the
doubt.

## [2026-09-07] revise-paper | make the kNN bound robust to an indexed implementation

Clarified that `NearestPoints` is the original paper's helper name, not an identified
Wolfram built-in. The paper specifies Euclidean distance but gives no data structure
or selection algorithm for the helper. Modeled exact selection as O(n) without
charging index construction or rebuilding, and noted that even an optimistic
expected O(log n + k) indexed query leaves intersection checking dominant, so the
stated O(kn^2) per-run and O(n^4) restart bounds do not change.
