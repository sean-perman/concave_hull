# Concave Hull

This repository holds the research paper I'm writing on the Moreira-Santos
*k*-nearest-neighbours concave-hull algorithm, along with all of the code,
experiments, and data behind it.

**The paper is a work in progress.** I plan to submit it to GRIVAPP 2027 in
October 2026.

**Start here:** [`scitepress_paper/short_paper_draft.pdf`](scitepress_paper/short_paper_draft.pdf)
is the current draft — read that first for the actual contributions
(runtime analysis of the original algorithm, two optimizations, and
counterexamples showing the algorithm's `k` parameter doesn't behave
monotonically). Everything below is supporting code and data.

## What's in this repository

| Path | Purpose | Status |
| --- | --- | --- |
| `scitepress_paper/` | Paper source (SCITEPRESS/LaTeX template) and the current PDF draft | In progress |
| `baseline/` | Direct Python baseline for the original restart-from-scratch algorithm | Preserved for comparison |
| `concave_hull_experiment/` | Configurable implementation, optimizations, benchmarks, and visualizer | Current development code |
| `legacy/monolithic/` | Earlier monolithic development versions | Historical reference only |
| `tests/` | Automated correctness and regression tests | |
| `studies/` | Focused monotonicity studies and counterexamples | |
| `datasets/` | Synthetic and real point datasets used by the experiments | |
| `results/` | Recorded benchmark results and figures | |
| `references/` | Source papers used by the project | |

The Moreira-Santos paper describes a Mathematica implementation. The code in
`baseline/` is this project's Python recreation of that algorithm, not source
code released by the paper's authors.

## Running the code

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

The original algorithm this work builds on:

> Adriano Moreira and Maribel Yasmina Santos. "Concave Hull: A k-Nearest
> Neighbours Approach for the Computation of the Region Occupied by a Set of
> Points." GRAPP 2007, pp. 61-68.

The PDF is stored at `references/moreira_santos_2007.pdf`.

## License

MIT - see [LICENSE](LICENSE).
