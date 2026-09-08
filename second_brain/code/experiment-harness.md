# Code: `concave_hull_experiment/` — the configurable experiment harness

**Type:** code page (repo is source of truth — do not edit code from here)
**Tracks:** `concave_hull_experiment/` (modular port of `seans_concavehull_4.py`)
**Ingested:** 2026-06-11

## What it is

A clean, modular re-implementation of the Moreira–Santos k-NN concave hull whose
whole point is **ablation**: every design choice is a toggle on a frozen
`ConcaveHullConfig`, so a benchmark can compare variants on the same point set.
Behavior is ported from `seans_concavehull_4.py` (docstrings cite exact line ranges)
but split into single-responsibility modules. This is the artifact the paper's
empirical section should be written from.

Module map: `config.py` (the toggles) · `concave_hull.py` (main loop, both failure
strategies) · `k_growth.py` · `checkpoints.py` · `intersections.py` · `knn.py` ·
`geometry.py` · `benchmark.py` (sweep + plots) · `demo.py` (interactive viz) ·
`run.py` (quick compare) · `paper_benchmark.py` (publication-focused paired run) ·
`growth_factorial_benchmark.py` (paper-ready growth/intersection factorial).

## The feature axes (this is the "different features" list)

Each is a field on `ConcaveHullConfig` (`config.py`), validated incl. cross-field
constraints. **These are the high-level ideas to write up.**

| Axis | Options | What it controls | Maps to |
|------|---------|------------------|---------|
| `initial_k` | int ≥ 3 | Starting k before any growth; the original's user parameter. Higher start skips small-k attempts that tend to fail (cf. [moreira2007] Fig. 9: higher k → less retry time) | [[gift-wrapping-walk]] (the parameter k), [[k-growth-strategy]] |
| `failure_strategy` | `restart` · `checkpoint` | On a dead end: discard whole hull and retry (original) vs. trim to last checkpoint and bump that region's k | C-BASE-3 / [[checkpoint-trimming]], C-CHK-1 |
| `checkpoint_strategy` | `none` · `extreme` · `convex_hull` | Checkpoint set: 4 cardinal extremes vs. all convex-hull vertices (cyclic) | **C-CHK-2** (confirms both modes exist) |
| `checkpoint_k_scope` | `per_region` · `global` | After a trim, raise only the failing region's k vs. one shared k across all regions. `global` avoids per-region re-climbing → much cheaper on many-region (convex_hull) inputs | **C-CHK-5** (new); makes C-CHK-3 viable |
| `k_growth_strategy` | `linear` · `exponential` · `binary_search` | How fast k escalates after failure | **C-KG-1/3/4** + [[k-growth-strategy]]; binary search is implemented but unsound in general after C-MONO-2 |
| `k_growth_rate` | float >1 | multiplier for `exponential` | C-KG-1 |
| `intersection_strategy` | `naive` · `bucketed` | Edge-cross test: scan all hull edges vs. spatial grid of edge cells | C-OPT-2 / [[spatial-bucketing]] |
| `intersection_bucket_size` | float (0 = auto) | grid cell size; auto ≈ extent/√n (≈1 point/cell) | C-OPT-2 |
| `knn_backend` | `scipy` | k-NN via cKDTree with tombstoned deletes + lazy rebuild | C-OPT-1 (note below) |
| `validate_final_hull` | `off` · `report` · `enforce` | Containment check: ignore vs. count leaked points vs. treat leak as failure (original correctness) | **NEW — C-VAL-1** |

### Notes / nuances worth a sentence in the paper

- **k-growth is a new analytical lever.** The runtime restart bound (draft §3.2)
  sums `C_run` over k = k₀…K. That sum *assumes linear +1 growth* (K terms). The
  harness shows two alternatives: **geometric** (implemented under the config name
  `exponential`; k ← min(max(k+1, ⌈k·rate⌉), n−1), ~O(log K) attempts but may
  overshoot to a non-minimal k and change the hull) and
  **binary_search** (implemented as bisection for the *smallest* valid k, starting
  k = n/2, ~O(log n) attempts). The binary variant is now known to be unsound:
  [[k-validity-nonmonotone]] gives V(3)=true, V(4)=false, V(5)=true, so bisection's
  false-then-true partition does not exist in general. Geometric forward growth
  remains valid when capped at the all-candidates endpoint and gives the proved
  C-KG-3 O(n³) upper bound under the draft's per-run model. See [[k-growth-strategy]].
- **k-NN ≠ grid bucketing here.** `knn.py` uses scipy `cKDTree` (immutable → deletes
  are tombstoned, rebuild past 25% dead), *not* a hand-rolled grid. So C-OPT-1
  ("grid bucketing for k-NN") is **not** what this harness does — only the
  *intersection* check is grid-bucketed (C-OPT-2). Keep these separate in the draft.
- **The shared kNN backend is an advisor-directed control.** Mario Lopez advised
  implementing the original algorithmic version and using the same kNN for both
  baseline and enhanced variants. The harness satisfies this because `scipy` is
  its only allowed `knn_backend`; all comparisons therefore vary recovery or
  intersection strategy without silently changing nearest-neighbor machinery.
  This supports a fair controlled comparison, but it does **not** establish that
  the unpublished 2007 Mathematica package internally used a KD-tree. See
  [[advisor-guidance]].
- **Bucketed intersection uses an exact supercover.** `_cells_for` rasterizes a
  segment to every grid cell it enters (via parametric grid-line crossings), so it's
  exact, not approximate. Worst case still degrades when many edges share a cell —
  matches the draft's honest "no asymptotic improvement" framing. The 2026-08-27
  repair explicitly includes endpoint-, grid-line-, and corner-touching cells; the
  previous midpoint-only traversal could miss an intersection at those boundaries.
- **`enforce` reproduces the original.** `validate_final_hull='enforce'` = the
  Moreira–Santos all-points-inside check that forces a higher-k retry; `report` just
  *measures* leakage without restarting (useful for separating "leaky" from "wrong").
  Cross-constraint: `enforce` is rejected with `checkpoint` (use `report`).
- **Out-of-order checkpoint handling** lives in `concave_hull.py:266-328`: hitting a
  checkpoint that isn't N+1 undoes the edge, bumps region N's k, and trims back — a
  second trigger beyond dead-ends (already noted on [[checkpoint-trimming]]).

## Instrumentation (the evidence the paper needs)

`HullResult` records, per run: `success`, `final_k` (worst per-region k), `restarts`
(restart attempts *or* checkpoint rollbacks), **`total_restart_edges`** (hull edges
discarded across all failures = the wasted-work measure), `points_outside`.
`benchmark.py` sweeps variants × dataset sizes × runs and plots **runtime**,
**wasted edges (cost)** vs **rollback/restart count (events)**, avg final_k, hull
length, failures. The default `VARIANTS` already compares
*restart-naive* vs *restart-bucketed* vs *checkpoint-convex_hull* — i.e. it is
**exactly the experiment that would move C-CHK-3 to `verified`** (wasted-work and
restart-count, restart vs trim). Results land in `results/<date>/benchmark_*.png`
(PNGs from 2026-05-18…21 exist but hold numeric data only as plots).

`paper_benchmark.py` is the publication-focused C-OPT-2 harness. It compares only
restart-naive and restart-bucketed on paired inputs, alternates their execution order,
warms lazy dependencies, keeps exact-predicate instrumentation outside the timed pass,
requires structural output equality, and records raw observations, environment, and a
source hash. Its final 2026-08-27 run contains 120 paired trials; all outputs were
identical and valid. See [[2026-08-27-spatial-bucketing-paper-benchmark]].

`growth_factorial_benchmark.py` implements the paper's next controlled experiment:

| growth | naive intersections | bucketed intersections |
|---|---|---|
| linear | original baseline | bucketing only |
| geometric, r=2 | geometric only | combined |

All four variants use the same paired input, restart recovery, `initial_k=3`, SciPy
`cKDTree`, and enforced containment. Execution order is rotated and reversed across
trials; exact-predicate counts are collected in separate untimed runs. The harness
records runtime, attempted-k sequence and sum, restarts, discarded edges, final k,
hull size, area ratio, containment, and exact-predicate calls. It requires naive and
bucketed outputs to be identical *within* each growth schedule, but correctly allows
linear and geometric growth to return different valid hulls. It writes raw CSV,
summary CSV, environment/source-hash metadata, and a ready-to-insert LaTeX table.

The schedule implementation was aligned with the proof before this harness was added:
it now uses `ceil(k*rate)` and explicitly tests the `n-1` all-candidates cap instead of
stopping when a geometric step overshoots it. Thirty repository tests pass, and both
synthetic and real-data smoke runs completed. The full 2026-09-01 paper run then
completed 110 paired inputs / 440 timed observations with all outputs valid and all
220 schedule-matched intersection pairs identical. See
[[2026-09-01-geometric-growth-factorial]].

## Datasets / generators

`benchmark.py`: `generate_unit_disk_points` (easy, uniform) and
`generate_star_points` (8-tip star, deep inter-tip concavities — the hard stress
case; default generator). Real data in `datasets/`: redwood & wolf sightings,
US cities, world capitals, star_8_tips. See [[datasets]] for the full use-case
breakdown and characterization.

## Open / to do (for the paper)

- C-CHK-3 stays `conjectured` until **measured numbers** from a restart-vs-checkpoint
  run are reported (experiment-log op — needs the human's results, not just the PNGs).
- Which k-growth strategy to recommend, and which checkpoint mode, are both open.

## See also

[[checkpoint-trimming]] · [[spatial-bucketing]] · [[k-growth-strategy]] ·
[[advisor-guidance]] · [[claims]]
