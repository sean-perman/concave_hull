import unittest

from studies.validity_monotonicity.validity_test import (
    DEFAULT_POINTS,
    is_general_position,
    load_points,
    sweep,
    validity_reversals,
)


class ValidityMonotonicityCounterexampleTests(unittest.TestCase):
    def test_six_point_counterexample_is_non_degenerate(self):
        self.assertTrue(is_general_position(load_points(DEFAULT_POINTS)))

    def test_validity_changes_true_false_true(self):
        points = load_points(DEFAULT_POINTS)
        for intersection in ("naive", "bucketed"):
            results = sweep(points, intersection=intersection)
            self.assertEqual([result.k for result in results], [3, 4, 5])
            self.assertEqual([result.valid for result in results], [True, False, True])
            self.assertEqual(len(validity_reversals(results)), 1)


if __name__ == "__main__":
    unittest.main()
