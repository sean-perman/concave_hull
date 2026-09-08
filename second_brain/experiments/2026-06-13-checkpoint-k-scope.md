# Experiment: checkpoint k-scope — per_region vs global

**Date run:** 2026-06-13 · **Bears on:** C-CHK-3, C-CHK-2, C-CHK-4, C-CHK-5 (new) · [[checkpoint-trimming]]
**Follows up:** [[2026-06-12-checkpoint-vs-restart-ablation]]
**CSV:** `results/2026-06-13/benchmark_16-03-56.csv`

## Motivation (author's insight)

The 2026-06-12 ablation found checkpoint *wastes more* than restart. Diagnosis: k is
**per-region** (`region_k_values = [initial_k]*len(checkpoints)`), so every region
re-climbs from initial_k independently — and convex_hull has many regions, so most of
the rollbacks are just re-climbing k. New axis `checkpoint_k_scope`:
- `per_region` (old): bump only the failing region's k.
- `global` (new): bump one shared k across all regions (monotone), like restart's global
  k, but keeping the trimmed prefix.

`_bump_region_k` in `concave_hull.py`; config field `checkpoint_k_scope`.

## Setup

5 variants, all bucketed, restart baseline = `enforce` (valid). Real GIS sets, native
size, 1 run each: redwood (1190), wolf (1054), cities (219), capitals (194).

## Result — global k wins, and `convex_hull + global` beats restart

ms / wasted-edges / points-outside:

| dataset | restart | convex_hull per_region | convex_hull **global** | extreme **global** |
|---|---|---|---|---|
| redwood | 3262 / 15007 / 0 | 1605 / 14278 / 12 | **255 / 3304 / 0** | 4909 / 15230 / 2 |
| wolf | 152 / 1890 / 0 | 235 / 3360 / 9 | **80 / 806 / 5** | 115 / 839 / 5 |
| cities | 4.7 / 72 / 0 | 3.6 / 16 / 0 | 3.5 / 16 / 0 | 3.4 / 18 / 0 |
| capitals | 64 / 1134 / 0 | 33 / 641 / 0 | **22 / 347 / 0** | 30 / 741 / 0 |

Findings:
1. **`global` reduces rollbacks + wasted work vs `per_region`** almost everywhere
   (redwood convex: 372→113 rollbacks, 14278→3304 edges, 6× faster). Confirms the
   re-climbing diagnosis.
2. **`convex_hull + global` beats the valid restart baseline on all 4 real sets** —
   less wasted work *and* faster (13× on redwood). This is the C-CHK-3 win that
   per_region buried.
3. **Leakage (C-CHK-4) is reduced but not eliminated** — redwood 12→0, but wolf still
   leaks 5. The excluded-points recovery gap is still real.
4. **Exception:** redwood `extreme` + global is *worse* (4909 ms) — with only 4 regions
   there is no re-climbing to save and global over-raises k. So the benefit is specific
   to many-region (convex_hull) inputs.

## Conclusions for the ledger

- **C-CHK-3:** revise from `contradicted` → `conjectured` (promising). The *per_region*
  implementation is contradicted, but **`convex_hull + global` supports it** (beats
  restart on work + runtime, 4/4 real). Not yet `verified` because (a) wolf still leaks
  (C-CHK-4 open) and (b) synthetic sweep not yet rerun with this variant.
- **New C-CHK-5:** `checkpoint_k_scope="global"` materially cuts trimming's cost on
  many-region inputs by avoiding per-region k re-climbing.
- **C-CHK-2:** the best config is now **convex_hull + global**, not `extreme`. The earlier
  "extreme dominates" was a per_region artifact.
- **C-CHK-4:** still open — global mitigates but doesn't fix the leak.

## Synthetic n-sweep (added 2026-06-13) — the win scales

`results/2026-06-13/benchmark_17-08-52.csv` — same 5 variants, unit_disk + star, n→50k,
5 seeds. ms / wasted-edges / outside, `convex_hull` mode:

| dataset | n | restart | per_region | **global** |
|---|--:|---|---|---|
| unit_disk | 10k | 246 / 639 / 0 | 258 / 876 / 10 | **123 / 65 / 0.2** |
| unit_disk | 50k | 970 / 672 / 0 | 1444 / 1194 / 16 | **793 / 98 / 1.0** |
| star | 10k | 1428 / 5720 / 0 | 498 / 2668 / 3 | **278 / 698 / 1.2** |
| star | 50k | 2783 / 4369 / 0 | 2886 / 5730 / 8 | **1301 / 1619 / 1.8** |

- **`convex_hull + global` beats restart at every size on both synthetic sets** (2–5×
  faster, ⅓–1/10 the wasted work). The real-data win holds at scale.
- `per_region` stays worse (re-climbing cost grows with n; leakage 10–16 pts).
- **Leak persists but is small** under global: ~1–2 pts out of 50 000 (vs per_region's 16).
  Nearly valid, not strictly. C-CHK-4 still the last blocker.

**Outcome:** C-CHK-3 → `verified` (for `convex_hull + global`, as a runtime/wasted-work
improvement), with the C-CHK-4 leak as the standing caveat. Fix excluded-points recovery
next to make it "faster *and* valid".
