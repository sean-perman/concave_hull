# Datasets & use cases — what the algorithm is for

**Type:** code/reference page (repo is source of truth)
**Tracks:** `datasets/*.csv` + `datasets/_extract.py`; generators in
`concave_hull_experiment/benchmark.py`
**Ingested:** 2026-06-12 (reframed around use case)

The concave hull answers "**what region is occupied by this set of points?**" So a
dataset is really a *use case*: each kind of point cloud is a different application
of that question. The five test clouds here, plus the procedural generators, span
the use cases below. This page feeds the draft's **Introduction (§1, applications)**
and **Future Work (§8)**.

## 1. Synthetic / benchmark data — *what the original paper used*

Controlled point clouds where you tune n and difficulty to study the algorithm
itself (runtime scaling, k vs smoothness, worst-case retry behavior).

- **Uniform random in a disk** — `generate_unit_disk_points` (`benchmark.py`). This
  is exactly what [moreira2007] §4.2 used for its timing graphs ("randomly generated
  within the space of a circle with unitary radius"). No concavity bias; the baseline
  for scaling curves.
- **Adversarial star** — `star_8_tips.csv` / `generate_star_points` (8 tips, deep
  inter-tip valleys, seed 42). Built to *force* dead ends and high k — the stress
  case for restart-vs-checkpoint (C-CHK-3) and the runtime worst case (C-RT-6).

*Use:* validation, runtime sweeps (to 200k pts), k/smoothness studies, worst-case probing.

## 2. GIS / geospatial footprints — *the original motivating domain*

The method was built in the LOCAL project to outline the footprint of geographic
point observations ([moreira2007] §1–2: POIs, "trees in a forest"). Two sub-uses:

- **Species range / ecology** — `gray_wolf_sightings.csv` (continental N. America),
  `coast_redwood_sightings.csv` (CA coastal strip). Sighting points → habitat / range
  polygons. Concavity matters: a convex hull badly over-claims range.
- **Settlement / human geography** — `us_mainland_cities.csv`, `world_capitals.csv`.
  City/capital points → territory or extent outlines.

*Use:* estimating occupied region from spatial observations; the canonical application.

## 3. Cluster-boundary extraction — *(prospective use case #1)*

Run any 2-D clustering first (the original paper paired it with **SNN clustering**,
[moreira2007] §2), then draw a concave hull **per cluster** to get its non-convex
boundary. This generalizes beyond maps to **any 2-D feature space** — e.g. outlining
groups in a t-SNE / UMAP embedding, defining cluster membership regions, or flagging
points outside the hull as outliers. No dataset yet; would need a clustered 2-D set
(synthetic Gaussians, or an embedding export).

## 4. Sensor & coverage footprints — *(prospective use case #2)*

The region physically **covered or occupied** by measurements: LIDAR returns →
obstacle/free-space outlines for robotics path planning; drone/satellite survey hits
→ coverage area; GPS/mobile traces → the area a vehicle, herd, or person ranged over.
Often non-convex (an L-shaped room, a coastline-following survey), so convex hulls
mislead. No dataset yet; would need a LIDAR slice or GPS-trace export.

## The five datasets at a glance

| Dataset | Use case | n | unique | dups | character |
|---------|----------|--:|-------:|-----:|-----------|
| `world_capitals.csv` | GIS / settlement | 194 | 194 | 0 | global, sparse, near-convex; antimeridian wrap |
| `us_mainland_cities.csv` | GIS / settlement | 219 | 202 | 17 | US outline, mild concavities |
| `star_8_tips.csv` | synthetic / adversarial | 300 | 300 | 0 | deep concavities — the stress case |
| `gray_wolf_sightings.csv` | GIS / species range | 1054 | 1054 | 0 | continental spread, sparse lobes |
| `coast_redwood_sightings.csv` | GIS / species range | 1190 | 1157 | 33 | tall narrow coastal strip |

Difficulty ladder (for the empirical section): capitals/cities (near-convex) →
redwood/wolf (real concave) → star (adversarial).

## Coverage assessment — is this enough? (gaps to add)

The set is strong on an easy→hard ladder of **real, single-blob** shapes, plus one
tunable adversarial synthetic. Strengths worth keeping: real duplicates (redwood,
cities) and the **parameterized** star generator (tips, inner/outer ratio = concavity
depth, jitter — a difficulty *knob*, not one fixed shape). Gaps, by priority:

1. **Non-uniform density / separated clusters — the #1 missing case.** This is the
   algorithm's *own documented hard case*: [moreira2007] §3.1 Fig. 6b (sparse + dense
   regions) and its 7-cluster artificial set (Fig. 2). Two well-separated lobes force k
   up sharply to bridge the gap (or get left out → `excluded points`). Nothing here
   tests it. Adding a bimodal/multi-cluster set directly exercises C-RT-6 (k→large),
   C-VAL-1 (excluded-points path), and echoes the original paper's methodology.
2. **An adversarial case for the checkpoint contribution itself.** Checkpoint trimming
   helps least when the convex hull has *few* vertices (huge regions, so trimming a
   region ≈ a full restart) but the interior is deeply concave — e.g. a square/triangle
   outline with a deep comb or spiral cut inward. This probes the *limits* of C-CHK-3
   honestly (where trim ≈ restart), and contrasts with a best case where concavities
   sit near convex-hull-vertex checkpoints. Needed to keep the empirical claim balanced.
3. **Degenerate geometry for robustness/termination.** Explicit collinear / lattice /
   cocircular points. Termination (C-TERM-1) is the main theoretical risk and the `n³`
   guard is a smell — pathological inputs (many angle/distance ties, long collinear
   runs) are where the trim/no-floor logic and `sortByAngle` tie-breaking break.
   (`us_mainland_cities` is partly integer-gridded, so it *accidentally* has collinear
   triples — make one on purpose.)
4. **Variable density within one shape** (dense core + sparse arms) — stresses k-growth
   (C-KG) and bucketing (C-OPT) under one hull. *(lower priority)*
5. **Annulus / ring (a hole).** The method returns a *simple* polygon and cannot
   represent holes — an annulus is a good limitation figure, not a success case.
   *(lower priority; documents a limitation)*

Methodological note: prefer **axes over instances** — sweep cluster separation and star
concavity depth as parameters (seeded), and pair each run with the metrics the harness
already records (restarts, wasted edges, final k). The real CSVs stay as qualitative
shape figures; the synthetic *families* carry the quantitative claims.

## Gotchas / limitations worth a sentence in the draft

- **Antimeridian (world_capitals):** raw lon/lat is planar, so capitals either side of
  ±180° read as ~354° apart — a limitation of treating geographic data as Euclidean,
  and a wrinkle for the "k is dimensionless" argument (draft §2.2.3): k is a count,
  but the metric it ranks is wrong on a sphere.
- **Duplicates** (redwood 33, cities 17): exercise the `cleanList` dedup that every run
  does first ([moreira2007] Alg. 1 line 2).
- **Sizes ≤1190:** qualitative/shape figures only; runtime scaling comes from the
  procedural sweep, not these.

## Provenance

`_extract.py` re-derives all five deterministically: four real sets from
`legacy/monolithic/seans_concavehull_4.py` literals, the star from
`generate_star(seed=42, 300 pts)`.
The CSV star is one fixed instance; `benchmark.py` reseeds per run.

## See also

[[experiment-harness]] (consumes these) · [[gift-wrapping-walk]] · [[claims]]
(C-CHK-3 empirical core; star is its hardest test)
