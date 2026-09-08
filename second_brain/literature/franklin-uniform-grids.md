# Franklin et al. — Uniform Grids for Intersection Detection

**Type:** source-summary · **Bib key:** `[franklin1989]` · **Source:**
[author publication page](https://wrfranklin.org/nikola/pubdetails/fnkszw-ugtid-89.html)

Franklin et al. present uniform spatial grids as an indexing technique for
reducing the number of object pairs considered during intersection detection on
serial and parallel machines. Geometry is associated with grid cells, and only
objects sharing relevant cells become intersection candidates. The paper
supports the prior-art statement that uniform grids are a standard candidate
filter for intersection problems; it does not establish the runtime or
correctness of our particular concave-hull implementation.

## Bearing on this paper

- Supports the general motivation and prior-art sentence in the Spatial
  Bucketing Improvement section.
- Bears on **C-OPT-2** only as background. Our corrected-supercover tests and
  paired benchmark remain the evidence for identical hulls and the measured
  1.28–3.45× speedup.
- The paper's uniform-grid technique is folded into [[spatial-bucketing]] rather
  than creating another concept page.

## Citation

W. R. Franklin, C. Narayanaswami, M. Kankanhalli, D. Sun, M.-C. Zhou, and
P. Y. F. Wu, “Uniform Grids: A Technique for Intersection Detection on Serial
and Parallel Machines,” *Proceedings of Auto-Carto 9*, pp. 100–109, 1989.
