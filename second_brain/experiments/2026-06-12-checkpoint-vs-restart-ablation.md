# Experiment: checkpoint vs restart vs bucketing — feature ablation

**Date run:** 2026-06-12 · **Logged:** 2026-06-13
**Harness:** `concave_hull_experiment/benchmark.py` (6-variant factorial)
**Bears on:** [[checkpoint-trimming]], [[spatial-bucketing]] · C-CHK-3, C-OPT-2, C-CHK-2, C-VAL-1, C-TERM-1

## Setup

Factorial: `{restart, checkpoint-extreme, checkpoint-convex_hull} × {naive, bucketed}`.
Held constant: `knn_backend=scipy`, `k_growth=linear`, `initial_k=3`. Restart variants
use `validate_final_hull="enforce"` (the **faithful** Moreira–Santos baseline — keeps
raising k until all points are enclosed); checkpoint variants use `"report"` (the config
forbids `enforce` with checkpoint). Metric of record: `total_restart_edges` (wasted work),
plus restart/rollback count, runtime, final_k, and **points_outside** (hull validity).

- **Real-data run** (1 run each, native size): `results/2026-06-12/benchmark_13-15-17.csv`
  — coast_redwood (1190), gray_wolf (1054), us_cities (219), world_capitals (194).
- **Synthetic sweep** (5 seeds, n=100…50 000): `results/2026-06-12/benchmark_16-27-18.csv`
  — unit_disk (the original paper's test data) and star_8tips (deep concavities).

## Results

### Bucketing — consistent practical speedup (supports C-OPT-2)
Identical hulls, faster. Gain grows with difficulty and helps checkpoint most (it does
more intersection checks via rollbacks):
- unit_disk @50k: restart 1368→1063 ms; checkpoint-convex 4035→1385 ms (**2.9×**)
- star @50k: restart 4057→2389 ms; checkpoint-convex 8253→2773 ms (**3.0×**)
- redwood: restart 14 817→2744 ms (5.4×); checkpoint-extreme 16 006→1980 ms (8×)

Not asymptotic (worst case unchanged), but a robust constant-factor win.

### Checkpoint trimming — does NOT reduce wasted work, and returns invalid hulls
Bucketed rows (apples-to-apples), wasted edges / rollback events / points-outside:

| dataset (n) | restart | ckpt-extreme | ckpt-convex |
|---|---|---|---|
| unit_disk (50k) | 672 / 4 / **0** | 1135 / 13 / **3** | 1194 / 51 / **16** |
| star (50k) | 4369 / 20 / **0** | 4950 / 46 / **4** | 5730 / 73 / **8** |
| redwood (1190) | 15007 / 113 / **0** | 9516 / 204 / **2** | 14278 / 372 / **12** |
| wolf (1054) | 1890 / 22 / **0** | 3434 / 99 / **7** | 3360 / 105 / **9** |

Two robust findings, consistent across real and synthetic:
1. **Checkpoint wastes ≥ as much total work as restart** (more, smaller rollback events).
   Only redwood-extreme beat restart on raw edge count, and it still leaked + raised k higher.
2. **Checkpoint leaves points outside the hull** (3–16) on every set ≥1000 points — i.e.
   it returns **invalid** hulls. The `enforce` restart baseline is always valid (0).
   Runtime: checkpoint is also slower than restart at matched backend, except on the
   pathological redwood strip (where restart blows k to 116) — and even there it leaked.

### Checkpoint mode: `extreme` < `convex_hull`
`extreme` consistently has fewer rollbacks, less waste, and less leakage (3 vs 16 on
unit_disk; 2 vs 12 on redwood). If checkpoints stay, `extreme` is the better mode.

## Root cause of the leakage (code trace)

`_run_with_checkpoints` (`concave_hull.py:337-346`) returns `success=True` the instant the
walk closes (`current == first_point`). It computes `points_outside` but **never acts on
it**. Checkpoint mode implements only the *intersection* recovery (dead-end + out-of-order
checkpoint) and **omits the original algorithm's second recovery trigger** —
[moreira2007] Alg. 1 lines 39–45: after closing, if any point is outside, raise k and
continue. So a closed-but-incomplete hull is accepted as final. This is a design gap, not
random noise; it is reproducible.

Important confound for the wasted-work comparison: restart (`enforce`) is solving a
*harder* problem (full containment) than checkpoint (which quits early, leaky). Adding the
missing excluded-points recovery to checkpoint would make it enclose those points — almost
certainly *increasing* its wasted work further, not decreasing it. So fixing the bug is
unlikely to rescue C-CHK-3 as stated.

## Conclusions for the ledger

- **C-CHK-3 (trimming improves practical runtime / preserves work): contradicted** by this
  evidence as the contribution is currently implemented. Trimming costs ≥ the work of
  restart and produces invalid hulls. Re-test only after the excluded-points gap is fixed.
- **C-OPT-2 (bucketing speedup): verified** (empirical constant-factor speedup; asymptotic
  claim still unproven).
- **New — C-CHK-4:** checkpoint mode lacks excluded-points recovery, so it can return hulls
  that don't enclose all points. Verified.
- **C-CHK-2:** `extreme` mode dominates `convex_hull` on waste + leakage here.
- Touches **C-TERM-1**: "terminates with a valid hull" is too strong for checkpoint —
  it terminates, but not necessarily *validly*.

## Caveats

Real-data rows are 1 deterministic run each (not noise — fixed input). Synthetic is 5
seeds. Bucketing/naive give identical structural metrics (bucketing only changes speed),
which is the expected sanity check and holds throughout.
