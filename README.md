# Concave Hull

Research code, experiments, and paper sources for analyzing and improving the
Moreira-Santos *k*-nearest-neighbours concave-hull algorithm.

## Which implementation should I use?

| Path | Purpose | Status |
| --- | --- | --- |
| `baseline/` | Direct Python baseline for the restart-from-scratch algorithm | Preserved for comparison |
| `concave_hull_experiment/` | Sean's configurable implementation, optimizations, benchmarks, and visualizer | Current development code |
| `legacy/monolithic/` | Earlier monolithic development versions | Historical reference only |

The Moreira-Santos paper describes a Mathematica implementation. The code in
`baseline/` is the project's Python recreation of that algorithm, not source
code released by the paper's authors.

## Repository layout

- `baseline/` - preserved restart-based Python implementation
- `concave_hull_experiment/` - maintained modular implementation and benchmark tools
- `legacy/` - earlier prototypes and the old runtime comparison script
- `tests/` - automated correctness and regression tests
- `studies/` - focused monotonicity studies and counterexamples
- `datasets/` - synthetic and real point datasets used by the experiments
- `results/` - recorded benchmark results and figures
- `scitepress_paper/` - current paper source and publication figures
- `second_brain/` - research notes, claims, and literature summaries
- `references/` - source papers used by the project

## Setup

Create a Python environment and install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the test suite:

```bash
python -m unittest discover -s tests
```

Run the maintained comparison or interactive demo:

```bash
python -m concave_hull_experiment.run
python -m concave_hull_experiment.demo
```

Import the maintained implementation:

```python
from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull

config = ConcaveHullConfig(
    initial_k=3,
    failure_strategy="restart",
    intersection_strategy="bucketed",
    validate_final_hull="report",
)
result = ConfigurableConcaveHull().run(points, config)
```

Import the preserved baseline when reproducing comparisons with the original
restart rule:

```python
from baseline import concavehull

hull = concavehull(points, k=3)
```

## Reference paper

The original algorithm is described in:

> Adriano Moreira and Maribel Yasmina Santos. "Concave Hull: A k-Nearest
> Neighbours Approach for the Computation of the Region Occupied by a Set of
> Points." GRAPP 2007, pp. 61-68.

The PDF is stored at `references/moreira_santos_2007.pdf`.
