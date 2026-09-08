# Baseline implementation

`concavehull.py` is the project's direct Python recreation of the
Moreira-Santos restart-from-scratch algorithm. It is retained as a stable
comparison point for benchmarks and behavioral checks.

The 2007 paper describes a Mathematica implementation, so this file should not
be presented as code released by Moreira and Santos.

Use the maintained `concave_hull_experiment/` package for current development.
Import this baseline only when reproducing the original recovery strategy:

```python
from baseline import concavehull

hull = concavehull(points, k=3)
```
