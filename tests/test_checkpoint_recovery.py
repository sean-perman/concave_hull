import random
import unittest

import numpy as np

from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull


def unit_disk_points(n: int, seed: int) -> list[tuple[float, float]]:
    rng = random.Random(seed)
    points: list[tuple[float, float]] = []
    while len(points) < n:
        x = rng.uniform(-1.0, 1.0)
        y = rng.uniform(-1.0, 1.0)
        if x * x + y * y <= 1.0:
            points.append((x, y))
    return points


def numpy_unit_disk_points(n: int, seed: int) -> list[tuple[float, float]]:
    """Match the generator used by the benchmark and interactive demo."""
    rng = np.random.default_rng(seed)
    points: list[tuple[float, float]] = []
    while len(points) < n:
        x, y = rng.uniform(-1.0, 1.0, size=2)
        if x * x + y * y <= 1.0:
            points.append((float(x), float(y)))
    return points


class CheckpointContainmentRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.points = unit_disk_points(100, seed=79)
        self.base_config = {
            "failure_strategy": "checkpoint",
            "checkpoint_strategy": "convex_hull",
            "checkpoint_k_scope": "global",
            "intersection_strategy": "naive",
        }

    def test_report_mode_preserves_closed_but_incomplete_hull(self) -> None:
        result = ConfigurableConcaveHull().run(
            self.points,
            ConcaveHullConfig(
                **self.base_config,
                validate_final_hull="report",
            ),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.final_k, 3)
        self.assertEqual(result.points_outside, 2)

    def test_enforce_mode_increases_k_until_all_points_are_enclosed(self) -> None:
        result = ConfigurableConcaveHull().run(
            self.points,
            ConcaveHullConfig(
                **self.base_config,
                validate_final_hull="enforce",
            ),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.final_k, 4)
        self.assertEqual(result.points_outside, 0)
        self.assertGreaterEqual(result.restarts, 1)
        self.assertGreater(result.total_restart_edges, 0)

    def test_early_return_to_start_triggers_containment_retry(self) -> None:
        points = numpy_unit_disk_points(250, seed=0)
        result = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(
                failure_strategy="checkpoint",
                checkpoint_strategy="convex_hull",
                checkpoint_k_scope="global",
                intersection_strategy="bucketed",
                validate_final_hull="enforce",
            ),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.final_k, 6)
        self.assertEqual(result.points_outside, 0)
        self.assertGreaterEqual(result.restarts, 1)


if __name__ == "__main__":
    unittest.main()
