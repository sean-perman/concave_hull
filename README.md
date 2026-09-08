# Concave Hull

Research code, experiments, and paper sources for analyzing and improving the
Moreira–Santos *k*-nearest-neighbours concave-hull algorithm.

## Repository layout

- `concave_hull_experiment/` — configurable implementation and benchmarks
- `tests/` — automated correctness and regression tests
- `datasets/` — synthetic and real point datasets used by the experiments
- `results/` — recorded benchmark results and figures
- `scitepress_paper/` — current paper source and publication figures
- `second_brain/` — research notes, claims, and literature summaries
- `references/` — source papers used by the project

## Setup

Create a Python environment and install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the test suite:

```bash
python -m unittest discover -s tests
```

Run the quick comparison or interactive demo:

```bash
python -m concave_hull_experiment.run
python -m concave_hull_experiment.demo
```

## Reference paper

The original algorithm is described in:

> Adriano Moreira and Maribel Yasmina Santos. “Concave Hull: A k-Nearest
> Neighbours Approach for the Computation of the Region Occupied by a Set of
> Points.” GRAPP 2007, pp. 61–68.

The PDF is stored at `references/moreira_santos_2007.pdf`.
