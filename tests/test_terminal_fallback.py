import unittest

from concave_hull_experiment.concave_hull import ConfigurableConcaveHull
from concave_hull_experiment.config import ConcaveHullConfig


class _AlwaysFailHull(ConfigurableConcaveHull):
    def __init__(self):
        self.attempted_ks = []

    def _attempt(self, points, k, config, *, on_step=None):
        self.attempted_ks.append(k)
        return None, 2


class TerminalFallbackTests(unittest.TestCase):
    def setUp(self):
        self.points = [
            (0.0, 0.0),
            (2.0, 0.0),
            (2.0, 2.0),
            (0.0, 2.0),
            (1.0, 1.0),
            (0.5, 1.0),
            (1.5, 1.0),
            (1.0, 0.5),
            (1.0, 1.5),
            (0.75, 0.75),
        ]

    def test_every_growth_strategy_attempts_n_minus_one_once_then_falls_back(self):
        expected = {
            "linear": [3, 4, 5, 6, 7, 8, 9],
            "exponential": [3, 6, 9],
            "binary_search": [5, 9],
        }
        for strategy, attempted_ks in expected.items():
            with self.subTest(strategy=strategy):
                algorithm = _AlwaysFailHull()
                result = algorithm.run(
                    self.points,
                    ConcaveHullConfig(
                        initial_k=3,
                        k_growth_strategy=strategy,
                        failure_strategy="restart",
                        validate_final_hull="enforce",
                    ),
                )

                self.assertEqual(algorithm.attempted_ks, attempted_ks)
                self.assertTrue(result.success)
                self.assertTrue(result.used_fallback)
                self.assertEqual(result.final_k, len(self.points) - 1)
                self.assertEqual(result.points_outside, 0)
                self.assertEqual(result.hull[0], result.hull[-1])
                self.assertEqual(result.restarts, len(attempted_ks))

    def test_initial_k_above_cap_is_clamped_before_terminal_attempt(self):
        algorithm = _AlwaysFailHull()
        result = algorithm.run(
            self.points,
            ConcaveHullConfig(
                initial_k=100,
                failure_strategy="restart",
                validate_final_hull="enforce",
            ),
        )

        self.assertEqual(algorithm.attempted_ks, [len(self.points) - 1])
        self.assertTrue(result.used_fallback)

    def test_original_four_vertex_closure_rule_can_reach_fallback(self):
        # With four input points, the original rule cannot reinsert the start
        # until after four distinct vertices have already been selected.
        points = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0), (1.0, 0.5)]
        result = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(validate_final_hull="enforce"),
        )

        self.assertTrue(result.success)
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.final_k, 3)
        self.assertEqual(result.points_outside, 0)
        self.assertEqual(result.hull[0], result.hull[-1])
        self.assertEqual(set(result.hull[:-1]), {(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)})

    def test_collinear_input_terminates_without_claiming_a_polygon(self):
        points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]
        result = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(validate_final_hull="enforce"),
        )

        self.assertFalse(result.success)
        self.assertTrue(result.used_fallback)
        self.assertIn("collinear", result.failure_reason)
        self.assertEqual(result.hull, [(3.0, 0.0), (0.0, 0.0)])

    def test_three_collinear_points_are_not_accepted_as_a_polygon(self):
        points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
        result = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(validate_final_hull="enforce"),
        )

        self.assertFalse(result.success)
        self.assertTrue(result.used_fallback)
        self.assertIn("collinear", result.failure_reason)


if __name__ == "__main__":
    unittest.main()
