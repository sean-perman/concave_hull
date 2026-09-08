# Index

Catalog of the wiki. You (Claude Code) read this first when answering a query,
then drill into the linked pages. Update it on every ingest, experiment, or new page.

## Literature (immutable sources)

Only `moreira-santos.md` and `franklin-uniform-grids.md` exist on disk so far; the rest are planned (catalogued
here so cross-links and bib keys are tracked). `[sean2025]`/`[sean2026]` are the
most-cited internal sources across the ledger and still have no page — priority to write.

| Page | Source | One-line |
|------|--------|----------|
| `literature/moreira-santos.md` | `[moreira2007]` | The original k-NN concave hull algorithm we improve. |
| `literature/franklin-uniform-grids.md` | `[franklin1989]` | Uniform grids as prior art for reducing candidate pairs in intersection detection. |
| `literature/galton-duckham.md` | `[galton2006]` | The 9 criteria for "region occupied by a set of points". *(page not yet written)* |
| `literature/alpha-shapes-grid.md` | `[liao2021]` | Grid-partition alpha shapes; the ~O(n²) baseline to beat. *(page not yet written)* |
| `literature/concave-graham.md` | `[yahya2015]` | Concave Graham-scan alternative for positioning. *(page not yet written; bib key not in `references.bib` and uncited in the draft)* |
| `literature/sean-2025-runtime.md` | `[sean2025]` | Author's runtime-analysis draft (O(n²) avg, O(n⁴) worst). *(page not yet written — most-cited internal source)* |
| `literature/sean-2026-plan.md` | `[sean2026]` | Author's optimization plan + 10-week timeline. *(page not yet written)* |

## Code (source of truth lives in the repo)

| Page | Tracks |
|------|--------|
| `code/baseline.md` | `baseline/concavehull.py` — recursive full-restart implementation. *(page not yet written)* |
| `code/optimized.md` | `legacy/monolithic/seans_concavehull_4.py` — bucketing + checkpoint trimming + visualizer. *(page not yet written)* |
| `code/experiment-harness.md` | `concave_hull_experiment/` — modular port with pluggable feature axes, the corrected bucketing benchmark, and a paper-ready 2×2 geometric-growth factorial harness. **The artifact the empirical section is written from.** |
| `code/datasets.md` | `datasets/*.csv` — test clouds framed by **use case**: synthetic/benchmark (original paper), GIS footprints (species-range + settlement), + prospective uses (cluster-boundary extraction, sensor/coverage). |

## Wiki

- `wiki/claims.md` — **the claims ledger** (start here for anything about what the paper asserts).
- `wiki/concepts/` — concept pages (one idea each). Created so far:
  - `gift-wrapping-walk.md` — the k-NN modified Jarvis march (the walk everything acts on).
  - `checkpoint-trimming.md` — implemented trim-to-checkpoint research direction; deferred from the 2026-08-27 short-paper scope to Future Work.
  - `spatial-bucketing.md` — exact-supercover grid index accelerating the
    edge-intersection check; documents the repaired boundary-cell bug and the corrected
    C-OPT-2 benchmark.
  - `termination-argument.md` — why the trimming variant halts (main open theoretical risk).
  - `k-growth-strategy.md` — how fast k escalates; geometric forward growth gives
    an O(n³) upper bound, while the implemented binary search is unsound after
    C-MONO-2.
  - `k-nonmonotone.md` — **C-MONO-1 (proven):** increasing k can produce a *more* concave hull; 8-point counterexample with verified computation; area ratio ρ as the concavity measure.
  - `k-validity-nonmonotone.md` — **C-MONO-2 (proven):** fixed-k validity can follow true→false→true; minimal six-point general-position integer counterexample, ruling out ordinary binary search for the smallest valid k.
  - _Planned, not yet created (source not ingested / single ref):_ `concave-hull-problem`
    + Galton-9-criteria (with `[galton2006]`), `knn-grid-query` (with `code/optimized`),
    `candidate-heuristics` (future work).

## Paper

- `../scitepress_paper/short_paper_draft.tex` — **active GRIVAPP submission
  source as of 2026-09-07.** Eight-page SCITEPRESS short-paper draft centered on
  runtime analysis, spatial bucketing, and two forms of k-nonmonotonicity;
  checkpoint trimming is Future Work. The runtime section now includes the O(n³)
  geometric-growth corollary.
- `paper/draft.md` — **the working draft** (Perman, adv. Lopez). Ingested 2026-06-11
  from `Concave_Hull_Paper (4).pdf`; retained as the full historical draft and
  superseded for the active submission by the short-paper TeX source above.
- `paper/references.bib` — bib entries for the keys the draft cites.
- `paper/grivapp-2027-submission.md` — **target venue and scope-controlled submission
  plan.** GRAPP's successor is GRIVAPP; primary Regular Paper deadline
  **2026-09-15**, fallback round **2026-10-22**. Records the limited-time rule,
  minimum viable paper, required integrity checks, Future Work deferrals, and cut
  order for the already-long draft.
- `paper/advisor-guidance.md` — durable decisions and provenance extracted from
  Sean's Slack history with Mario Lopez: concave-hull project selection,
  publication-in-the-original-forum suggestion, same-kNN fair-comparison rule,
  independent-study delivery history, and the distinction between advisor
  guidance and unconfirmed author ideas.

## Active short-paper sections

Current order in `scitepress_paper/short_paper_draft.tex` as of 2026-09-07:

1. Introduction — written with the three contributions and the measured factorial
   results; a separate roadmap paragraph remains optional if space permits.
2. Background and the Moreira--Santos Algorithm — written; needs compression and
   a correction distinguishing Graham-scan and Jarvis-march complexity.
3. Runtime Analysis of the Original Algorithm — written; O(kn²) per attempt,
   O(n⁴) under linear k-growth, and O(n³) for the modified geometric-growth
   schedule. The 2026-09-07 import adds a termination subsection but leaves its
   formal proof as a visible TODO, while the abstract still claims the proof.
4. Spatial Bucketing Improvement — now cites uniform-grid intersection-detection
   prior art and documents automatic cell sizing, exact segment supercover,
   boundary/corner handling, deduplication, and the final exact predicate.
5. Experimental Evaluation — the completed 2×2 linear/geometric × naive/bucketed
   benchmark is integrated with its full-width table and runtime--shape tradeoff.
   Across 110 paired inputs, all 440 runs were valid and all 220 schedule-matched
   intersection pairs were identical. Geometric growth improved runtime in all 11
   groups but usually changed the selected hull.
6. Non-Monotone Effects of k — written; retains the eight-point shape
   counterexample and adds the six-point valid→dead-end→valid counterexample from
   `experiments/2026-08-31-k-validity-nonmonotone.md`, ruling out ordinary binary
   search for the smallest valid k.
7. Future Work — must be compressed so checkpoint trimming is introduced as a
   deferred direction rather than assuming a removed main-body section.
8. Conclusion — written; summarizes the runtime bounds, bucketing result, geometric
   runtime--shape tradeoff, combined speedup, and both nonmonotonicity results.

## Experiments

- `experiments/2026-09-01-geometric-growth-factorial.md` — publication 2×2 run:
  110 paired inputs / 440 timed observations, all valid; geometric growth gives
  1.36–44.57× speedups and 1.5–16.3× fewer attempts, while combined gives
  1.89–147.94× over the original. C-KG-5 and C-KG-6 verified with an explicit
  runtime--shape tradeoff.
- `experiments/2026-08-31-k-validity-nonmonotone.md` — minimal six-point
  general-position integer counterexample: fixed-k validity is true at k=3, false
  at k=4, and true at k=5. Proves C-MONO-2, contradicts binary-search claim
  C-KG-4, and includes a seeded search, figure, and passing regressions.
- `experiments/2026-08-27-spatial-bucketing-paper-benchmark.md` — publication-focused
  naive-vs-corrected-bucketed comparison: 120 paired trials, all identical and valid;
  median speedups 1.28–3.45× and 6.9–188.6× fewer exact intersection predicates.
- `experiments/2026-06-12-checkpoint-vs-restart-ablation.md` — 6-variant factorial on
  2 real + 2 synthetic datasets. **C-OPT-2 verified** (bucketing 1.3–8×), new **C-CHK-4**
  (checkpoint omits excluded-points recovery → leaky hulls), C-CHK-3 contradicted *for
  per-region k* (superseded by the k-scope follow-up below). CSVs:
  `results/2026-06-12/benchmark_13-15-17.csv` (real), `…_16-27-18.csv` (synthetic).
- `experiments/2026-06-13-checkpoint-k-scope.md` — per_region vs **global** k, on 4 real +
  2 synthetic (n→50k). **`convex_hull + global` beats restart everywhere** (2–13× faster,
  ⅓–1/10 the wasted work) → **C-CHK-3 verified** (scoped to that config), new **C-CHK-5**
  (global k avoids per-region re-climbing). Leak (C-CHK-4) small but persists (~1–2/50k) —
  the last blocker. CSVs: `…/benchmark_16-03-56.csv` (real), `…_17-08-52.csv` (synthetic).
