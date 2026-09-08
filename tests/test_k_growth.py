import unittest

from concave_hull_experiment.k_growth import ExponentialKGrowth


def failure_sequence(*, n: int, initial_k: int = 3, rate: float = 2.0) -> list[int]:
    growth = ExponentialKGrowth(rate=rate)
    k = growth.initial_k(n, initial_k)
    values = []
    while k is not None and k < n:
        values.append(k)
        k = growth.next_k(k, succeeded=False, n=n)
    return values


class ExponentialKGrowthTests(unittest.TestCase):
    def test_doubling_tests_all_candidates_cap(self):
        self.assertEqual(failure_sequence(n=10), [3, 6, 9])
        self.assertEqual(failure_sequence(n=6), [3, 5])

    def test_fractional_rate_uses_ceiling(self):
        self.assertEqual(
            failure_sequence(n=20, rate=1.5),
            [3, 5, 8, 12, 18, 19],
        )

    def test_cap_is_not_repeated(self):
        growth = ExponentialKGrowth(rate=2.0)
        self.assertIsNone(growth.next_k(9, succeeded=False, n=10))

    def test_success_stops_the_schedule(self):
        growth = ExponentialKGrowth(rate=2.0)
        self.assertIsNone(growth.next_k(6, succeeded=True, n=10))


if __name__ == "__main__":
    unittest.main()
