# Experiment: geometric k-growth × spatial bucketing factorial

**Date run:** 2026-09-01  
**Harness:** `concave_hull_experiment/growth_factorial_benchmark.py`  
**Bears on:** [[k-growth-strategy]] · [[spatial-bucketing]] · C-KG-3 · C-KG-5 ·
C-KG-6 · C-OPT-2

## Question

Does constant-ratio geometric k-growth reduce practical restart cost and runtime
relative to the original linear schedule, and does it remain useful when combined
with spatially bucketed intersection checking?

## Correctness gate

Before the benchmark, `ExponentialKGrowth` was aligned with the schedule analyzed in
the paper. It now advances after failure by

\[
k_{j+1}=\min\{\max(k_j+1,\lceil 2k_j\rceil),n-1\},
\]

so an overshooting multiplication cannot skip the explicit all-candidates cap. Four
new schedule regressions cover doubling, fractional-rate ceiling, one-time cap
testing, and stopping after success. The complete repository suite contains 30 tests
and passes under the recorded arm64 Miniforge environment.

## Design

The run is a 2×2 factorial:

| variant | k-growth | intersection checking |
|---|---|---|
| Original | linear, +1 | naive |
| Bucketing | linear, +1 | bucketed |
| Geometric | ratio 2 | naive |
| Combined | ratio 2 | bucketed |

Held constant: restart recovery, `initial_k=3`, SciPy `cKDTree`, automatic bucket
width `extent/sqrt(n)`, and enforced final containment. Every input is shared by all
four variants. Execution order rotates and reverses across trials, dependencies are
warmed before timing, and exact-intersection calls are collected in separate untimed
runs. Naive and bucketed variants must return identical structural results within
each growth schedule; linear and geometric schedules are allowed to return different
valid hulls.

- Synthetic: unit disk and eight-tip star, n = 1k, 5k, 10k, 50k, 10 seeds each.
- Real: U.S. cities, gray wolf, and coast redwood, 10 timing trials each.
- World capitals excluded because raw longitude/latitude retains the antimeridian
  limitation.
- Total: 110 paired inputs, 440 timed observations, and 220 schedule-matched
  naive/bucketed comparisons.

Command:

```text
/Users/seanperman/miniforge3/bin/python3 \
  -m concave_hull_experiment.growth_factorial_benchmark --rate 2
```

## Results

All 440 timed runs succeeded with zero input points outside. All 220
schedule-matched naive/bucketed comparisons produced identical ordered hulls and
structural metrics.

Median values across ten trials:

| Dataset | n | Original ms | Bucketed ms | Geometric ms | Combined ms | Attempts L/G | Final k L/G | rho L/G |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Coast redwood | 1,190 | 17,954.5 | 5,246.0 | 402.1 | 121.3 | 114 / 7 | 116 / 192 | 0.359 / 0.422 |
| Gray wolf | 1,054 | 485.6 | 222.2 | 88.7 | 55.3 | 23 / 5 | 25 / 48 | 0.528 / 0.730 |
| Eight-tip star | 1,000 | 164.5 | 59.9 | 55.0 | 26.1 | 6.5 / 3 | 8.5 / 12 | 0.425 / 0.460 |
| Eight-tip star | 5,000 | 1,343.5 | 388.2 | 383.8 | 120.9 | 13 / 4 | 15 / 24 | 0.454 / 0.467 |
| Eight-tip star | 10,000 | 2,518.9 | 985.4 | 524.6 | 238.6 | 16 / 4 | 18 / 24 | 0.470 / 0.476 |
| Eight-tip star | 50,000 | 6,082.0 | 3,722.2 | 1,792.1 | 1,048.9 | 17 / 4 | 19 / 24 | 0.484 / 0.487 |
| Unit disk | 1,000 | 57.0 | 29.9 | 28.9 | 22.0 | 4 / 2 | 6 / 6 | 0.938 / 0.943 |
| Unit disk | 5,000 | 262.1 | 148.2 | 134.5 | 81.6 | 6 / 3 | 8 / 12 | 0.977 / 0.985 |
| Unit disk | 10,000 | 296.5 | 214.4 | 256.9 | 157.8 | 6 / 3 | 8 / 12 | 0.984 / 0.989 |
| Unit disk | 50,000 | 1,820.6 | 1,449.8 | 1,200.4 | 888.9 | 5.5 / 3 | 7.5 / 12 | 0.991 / 0.994 |
| U.S. cities | 219 | 9.93 | 7.08 | 7.34 | 5.14 | 3 / 2 | 5 / 6 | 0.732 / 0.748 |

Across the 11 dataset/size groups:

- Bucketing under linear growth: 1.40–3.41× paired median runtime speedup and
  6.9–188.6× fewer exact predicates.
- Geometric versus linear growth with naive checking: 1.36–44.57× speedup.
- Geometric versus linear growth with bucketed checking: 1.21–43.52× speedup.
- Combined versus original: 1.89–147.94× speedup.
- Geometric growth reduced attempts by 1.5–16.3× and the sum of tested k values by
  1.33–17.80×.

## Shape tradeoff

Geometric growth returned the same hull as linear growth in only 11 of 110 inputs.
For the other 99 inputs, the geometric result had a higher area ratio in this run;
the median dataset-level increase ranged from 0.003 to 0.202. This is an observation
about these inputs, not a monotonicity theorem: C-MONO-1 supplies a counterexample to
any general claim that increasing k must make the result smoother or less concave.

The correct empirical claim is therefore a runtime--shape tradeoff. Bucketing is an
exact, output-preserving acceleration. Geometric growth is a terminating schedule
that reduces restart work but may skip the smallest successful k and change the hull.

## Artifacts

- `results/2026-09-01/growth_factorial_18-53-01_raw.csv`
- `results/2026-09-01/growth_factorial_18-53-01_summary.csv`
- `results/2026-09-01/growth_factorial_18-53-01_metadata.json`
- `results/2026-09-01/growth_factorial_18-53-01_paper_table.tex`

The generated table is included in the active SCITEPRESS manuscript. The rebuilt
paper occupies 8 A4 pages and has no overfull boxes or undefined references.

## Claim decisions

- **C-KG-5 → verified:** geometric growth reduced paired median runtime and restart
  work in every tested dataset/size group. Scope this claim to the tested inputs and
  report the changed-hull tradeoff.
- **C-KG-6 → verified:** the combined geometric-plus-bucketed configuration was
  1.89–147.94× faster than the original baseline across the tested groups.
- **C-OPT-2 remains verified:** the new factorial corroborates the corrected
  bucketing result under both growth schedules, with identical outputs within each.
- **C-KG-3 remains proven:** the experiment illustrates the smaller tested-k sum but
  is not the proof of the O(n³) upper bound.
