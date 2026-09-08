import random
import unittest
from itertools import combinations

from concave_hull_experiment import ConcaveHullConfig, ConfigurableConcaveHull
from concave_hull_experiment.geometry import do_intersect
from concave_hull_experiment.intersections import BucketedIntersectionIndex


class BucketedIntersectionIndexTests(unittest.TestCase):
    def assert_matches_exact(self, stored_edge, candidate_edge, *, cell_size=1.0):
        index = BucketedIntersectionIndex(cell_size)
        index.add_edge(*stored_edge)
        self.assertEqual(
            index.would_intersect(*candidate_edge),
            do_intersect(*candidate_edge, *stored_edge),
            msg=f"stored={stored_edge}, candidate={candidate_edge}",
        )

    def test_endpoint_on_grid_corner_is_not_missed(self):
        self.assert_matches_exact(
            ((-2.0, -2.0), (-1.0, -1.0)),
            ((-2.0, -1.0), (0.0, -1.0)),
        )

    def test_segment_on_grid_line_is_indexed_on_both_sides(self):
        self.assert_matches_exact(
            ((0.0, -1.0), (0.0, 1.0)),
            ((-1.0, 0.0), (1.0, 0.0)),
        )

    def test_small_lattice_matches_exact_predicate(self):
        points = [
            (float(x), float(y))
            for x in range(-1, 2)
            for y in range(-1, 2)
        ]
        segments = list(combinations(points, 2))
        for stored_edge in segments:
            index = BucketedIntersectionIndex(1.0)
            index.add_edge(*stored_edge)
            for candidate_edge in segments:
                self.assertEqual(
                    index.would_intersect(*candidate_edge),
                    do_intersect(*candidate_edge, *stored_edge),
                    msg=f"stored={stored_edge}, candidate={candidate_edge}",
                )

    def test_random_segments_match_exact_predicate(self):
        rng = random.Random(7)
        for cell_size in (0.5, 1.0, 2.0):
            for _ in range(500):
                stored_edge = tuple(
                    (rng.uniform(-5.0, 5.0), rng.uniform(-5.0, 5.0))
                    for _ in range(2)
                )
                candidate_edge = tuple(
                    (rng.uniform(-5.0, 5.0), rng.uniform(-5.0, 5.0))
                    for _ in range(2)
                )
                self.assert_matches_exact(
                    stored_edge, candidate_edge, cell_size=cell_size
                )

    def test_lattice_hull_matches_naive_backend(self):
        points = [
            (1.0, 3.0), (4.0, 1.0), (0.0, 3.0), (0.0, 4.0),
            (1.0, 0.0), (1.0, 5.0), (3.0, 0.0), (0.0, 1.0),
            (2.0, 4.0), (5.0, 1.0), (4.0, 4.0), (0.0, 2.0),
            (2.0, 1.0), (3.0, 5.0), (4.0, 0.0), (1.0, 1.0),
            (3.0, 3.0), (2.0, 5.0), (3.0, 4.0), (5.0, 4.0),
        ]
        common = dict(
            failure_strategy="restart",
            validate_final_hull="enforce",
            initial_k=3,
        )
        naive = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(**common, intersection_strategy="naive"),
        )
        bucketed = ConfigurableConcaveHull().run(
            points,
            ConcaveHullConfig(
                **common,
                intersection_strategy="bucketed",
                intersection_bucket_size=1.0,
            ),
        )

        self.assertTrue(naive.success)
        self.assertTrue(bucketed.success)
        self.assertEqual(bucketed.hull, naive.hull)
        self.assertEqual(bucketed.final_k, naive.final_k)
        self.assertEqual(bucketed.points_outside, naive.points_outside)


if __name__ == "__main__":
    unittest.main()
