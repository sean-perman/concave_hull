# Legacy prototypes

This directory preserves development history that has been superseded by the
modular `concave_hull_experiment/` package.

- `monolithic/seans_concavehull.py` through `seans_concavehull_5.py` are
  successive monolithic experiments. Version 4 is the main source from which
  the maintained package was extracted.
- `runtime_comparison.py` is the older timing harness for the baseline and
  version 4.
- `grid_knn_prototype.py` is an early uniform-grid nearest-neighbour prototype.

These files are retained for provenance and are not part of the maintained test
surface. New work should target `concave_hull_experiment/` and `tests/`.
