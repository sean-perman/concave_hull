import unittest

from baseline import concavehull


class BaselineSmokeTests(unittest.TestCase):
    def test_three_points_are_returned_as_the_hull(self):
        points = [(0, 0), (1, 0), (0, 1)]

        self.assertEqual(concavehull(points, k=3), points)


if __name__ == "__main__":
    unittest.main()
