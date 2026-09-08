# Experiment: corrected spatial bucketing — paper benchmark

**Date run:** 2026-08-27  
**Harness:** `concave_hull_experiment/paper_benchmark.py`  
**Bears on:** [[spatial-bucketing]] · C-OPT-2

## Correctness gate

Before timing, the bucket rasterizer was corrected to include cells touched only at
segment endpoints, grid lines, and grid corners. The previous midpoint-only
rasterization could omit those cells and miss an intersection. Regression coverage now
includes direct geometry cases, an exhaustive 90,000-pair integer-lattice comparison
against Shapely, randomized segment comparisons, and full naive/bucketed hull equality
on lattice inputs. All 20 repository tests pass.

## Setup

The benchmark varies exactly one feature: `intersection_strategy = naive | bucketed`.
Held constant: original `restart` recovery, `initial_k=3`, linear k growth, SciPy
`cKDTree`, automatic bucket size `extent/sqrt(n)`, and final containment enforcement.

Each paired trial uses the same point set. Naive/bucketed order alternates, lazy
dependencies are warmed before timing, every raw observation is saved, and paired
results must agree on success, ordered hull, final k, containment, restart count, and
wasted edges. Exact-predicate calls are collected in a separate untimed pass so the
counter cannot bias runtime.

- Synthetic: unit disk + eight-tip star, n = 1k, 5k, 10k, 50k, 10 seeds each.
- Real: U.S. cities, gray wolf, coast redwood, world capitals, 10 timed repetitions.
- Total: 120 paired trials / 240 raw observations.
- Environment and source hash are recorded in the metadata artifact.

## Results

Median values across the 10 paired trials:

| Dataset | n | Naive ms | Bucketed ms | Paired speedup | Exact-call reduction |
|---|---:|---:|---:|---:|---:|
| U.S. cities | 219 | 9.73 | 6.71 | 1.46x | 8.1x |
| Gray wolf | 1,054 | 469.43 | 214.36 | 2.22x | 6.9x |
| Coast redwood | 1,190 | 17,408.79 | 5,060.92 | 3.45x | 9.7x |
| World capitals | 194 | 115.96 | 90.99 | 1.28x | 8.1x |
| Unit disk | 1,000 | 52.57 | 27.81 | 1.76x | 37.8x |
| Unit disk | 5,000 | 254.05 | 135.01 | 1.74x | 67.8x |
| Unit disk | 10,000 | 305.60 | 201.45 | 1.50x | 90.4x |
| Unit disk | 50,000 | 1,766.41 | 1,414.68 | 1.42x | 188.6x |
| Eight-tip star | 1,000 | 160.24 | 55.73 | 2.68x | 42.0x |
| Eight-tip star | 5,000 | 1,251.41 | 367.94 | 2.80x | 114.7x |
| Eight-tip star | 10,000 | 2,410.85 | 950.89 | 2.39x | 159.2x |
| Eight-tip star | 50,000 | 5,641.75 | 3,414.63 | 1.61x | 147.9x |

All 120 paired outputs were identical, all runs succeeded, and every final hull had zero
points outside. The run-order split was balanced (60 pairs each); mean paired speedup was
2.04x in both order groups, with medians 1.78x and 1.85x.

## Artifacts

- `results/2026-08-27/paper_benchmark_12-21-39_raw.csv`
- `results/2026-08-27/paper_benchmark_12-21-39_summary.csv`
- `results/2026-08-27/paper_benchmark_12-21-39_metadata.json`

The earlier `paper_benchmark_12-02-50_*` run counted exact predicates inside the timed
region and is marked preliminary in its metadata. Do not use its timings in the paper.

## Conclusion and limits

C-OPT-2 remains **verified** with stronger, corrected evidence: spatial bucketing reduced
runtime on every paired trial while preserving the exact output on all tested inputs. It
also reduced calls to the exact intersection predicate by 6.9x--188.6x, directly
confirming the mechanism. This remains an empirical constant-factor result; the worst
case is unchanged. World-capital coordinates are raw longitude/latitude and retain the
known antimeridian limitation, so that row should be omitted or clearly qualified in the
paper.
