import unittest

from concave_hull_experiment.benchmark import generate_unit_disk_points
from concave_hull_experiment.paper_benchmark import (
    comparable_result,
    run_pair_in_process,
    summarize,
)


class PaperBenchmarkTests(unittest.TestCase):
    def test_paired_run_is_identical_and_counts_fewer_bucketed_checks(self):
        points = generate_unit_disk_points(250, seed=3)
        observations = run_pair_in_process(points, ("naive", "bucketed"))

        naive = observations["naive"]
        bucketed = observations["bucketed"]
        self.assertEqual(
            comparable_result(naive["result"]),
            comparable_result(bucketed["result"]),
        )
        self.assertTrue(naive["result"].success)
        self.assertEqual(naive["result"].points_outside, 0)
        self.assertLess(
            bucketed["exact_intersection_calls"],
            naive["exact_intersection_calls"],
        )

    def test_summary_uses_paired_speedups(self):
        rows = []
        for trial, naive_ms, bucketed_ms in ((0, 10.0, 5.0), (1, 9.0, 6.0)):
            for strategy, runtime in (("naive", naive_ms), ("bucketed", bucketed_ms)):
                rows.append({
                    "dataset": "sample",
                    "n": 100,
                    "trial": trial,
                    "strategy": strategy,
                    "runtime_ms": runtime,
                    "exact_intersection_calls": 100 if strategy == "naive" else 20,
                    "identical_pair": True,
                })

        result = summarize(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["trials"], 2)
        self.assertAlmostEqual(result[0]["median_paired_speedup"], 1.75)
        self.assertEqual(result[0]["median_exact_call_reduction"], 5.0)
        self.assertTrue(result[0]["all_pairs_identical"])


if __name__ == "__main__":
    unittest.main()
