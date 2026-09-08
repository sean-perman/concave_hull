import unittest
from itertools import combinations

from shapely.geometry import LineString

from concave_hull_experiment.geometry import do_intersect


Point = tuple[float, float]
Segment = tuple[Point, Point]


def shapely_expected(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Reference predicate with the hull algorithm's shared-endpoint convention."""
    if a == c or a == d or b == c or b == d:
        return False
    return LineString([a, b]).intersects(LineString([c, d]))


class SegmentIntersectionTests(unittest.TestCase):
    def assert_intersection(self, first: Segment, second: Segment, expected: bool):
        self.assertEqual(do_intersect(*first, *second), expected)
        # The predicate should not depend on segment order or direction.
        self.assertEqual(do_intersect(*second, *first), expected)
        self.assertEqual(
            do_intersect(first[1], first[0], *second), expected
        )
        self.assertEqual(
            do_intersect(*first, second[1], second[0]), expected
        )

    def test_proper_crossing(self):
        self.assert_intersection(
            ((0.0, 0.0), (2.0, 2.0)),
            ((0.0, 2.0), (2.0, 0.0)),
            True,
        )

    def test_vertical_horizontal_crossing(self):
        self.assert_intersection(
            ((1.0, -2.0), (1.0, 2.0)),
            ((-2.0, 0.0), (2.0, 0.0)),
            True,
        )

    def test_parallel_disjoint(self):
        self.assert_intersection(
            ((0.0, 0.0), (3.0, 0.0)),
            ((0.0, 1.0), (3.0, 1.0)),
            False,
        )

    def test_collinear_overlap(self):
        self.assert_intersection(
            ((0.0, 0.0), (4.0, 0.0)),
            ((1.0, 0.0), (3.0, 0.0)),
            True,
        )

    def test_collinear_disjoint(self):
        self.assert_intersection(
            ((0.0, 0.0), (1.0, 0.0)),
            ((2.0, 0.0), (3.0, 0.0)),
            False,
        )

    def test_endpoint_touching_other_segment_interior(self):
        self.assert_intersection(
            ((0.0, 0.0), (2.0, 0.0)),
            ((1.0, -1.0), (1.0, 0.0)),
            True,
        )

    def test_shared_endpoint_is_intentionally_allowed(self):
        self.assert_intersection(
            ((0.0, 0.0), (1.0, 1.0)),
            ((1.0, 1.0), (2.0, 0.0)),
            False,
        )

    def test_near_miss(self):
        self.assert_intersection(
            ((0.0, 0.0), (1.0, 1.0)),
            ((0.0, 1.000001), (1.0, 2.000001)),
            False,
        )

    def test_negative_coordinates(self):
        self.assert_intersection(
            ((-3.0, -3.0), (-1.0, -1.0)),
            ((-3.0, -1.0), (-1.0, -3.0)),
            True,
        )

    def test_exhaustive_integer_lattice_matches_shapely(self):
        points = [
            (float(x), float(y))
            for x in range(-2, 3)
            for y in range(-2, 3)
        ]
        segments = list(combinations(points, 2))
        for first in segments:
            for second in segments:
                expected = shapely_expected(*first, *second)
                self.assertEqual(
                    do_intersect(*first, *second),
                    expected,
                    msg=f"first={first}, second={second}",
                )


if __name__ == "__main__":
    unittest.main()
