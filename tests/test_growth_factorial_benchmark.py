import unittest

from concave_hull_experiment.benchmark import generate_unit_disk_points
from concave_hull_experiment.growth_factorial_benchmark import (
    VARIANT_KEYS,
    attempted_k_values,
    factorial_config,
    latex_table,
    order_for_trial,
    run_factorial_in_process,
    summarize,
)
from concave_hull_experiment.paper_benchmark import comparable_result


class GrowthFactorialBenchmarkTests(unittest.TestCase):
    def test_factorial_configs_vary_only_the_two_axes(self):
        configs = {key: factorial_config(key) for key in VARIANT_KEYS}
        self.assertEqual(configs["linear_naive"].k_growth_strategy, "linear")
        self.assertEqual(configs["geometric_naive"].k_growth_strategy, "exponential")
        self.assertEqual(configs["linear_bucketed"].intersection_strategy, "bucketed")
        self.assertEqual(configs["geometric_naive"].intersection_strategy, "naive")
        held = {
            (
                config.initial_k,
                config.knn_backend,
                config.failure_strategy,
                config.validate_final_hull,
            )
            for config in configs.values()
        }
        self.assertEqual(held, {(3, "scipy", "restart", "enforce")})

    def test_order_cycle_contains_every_variant(self):
        for trial in range(8):
            order = order_for_trial(trial)
            self.assertEqual(len(order), 4)
            self.assertEqual(set(order), set(VARIANT_KEYS))

    def test_factorial_run_preserves_intersection_outputs(self):
        points = generate_unit_disk_points(250, seed=3)
        observations = run_factorial_in_process(points, order_for_trial(0))

        for growth in ("linear", "geometric"):
            naive = observations[f"{growth}_naive"]
            bucketed = observations[f"{growth}_bucketed"]
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

        geometric = observations["geometric_naive"]["result"]
        values = attempted_k_values(
            geometric,
            n=len(points),
            growth_strategy="exponential",
        )
        self.assertEqual(values[-1], geometric.final_k)
        self.assertEqual(len(values), geometric.restarts + 1)

    def test_summary_and_latex_table(self):
        rows = []
        runtimes = {
            "linear_naive": (12.0, 10.0),
            "linear_bucketed": (6.0, 5.0),
            "geometric_naive": (4.0, 5.0),
            "geometric_bucketed": (2.0, 2.5),
        }
        for trial in (0, 1):
            for variant in VARIANT_KEYS:
                is_geometric = variant.startswith("geometric")
                is_bucketed = variant.endswith("bucketed")
                rows.append({
                    "dataset": "sample",
                    "n": 100,
                    "trial": trial,
                    "variant": variant,
                    "runtime_ms": runtimes[variant][trial],
                    "attempts": 3 if is_geometric else 8,
                    "sum_attempted_k": 21 if is_geometric else 52,
                    "restarts": 2 if is_geometric else 7,
                    "wasted_edges": 20 if is_geometric else 70,
                    "final_k": 12 if is_geometric else 10,
                    "area_ratio": 0.9 if is_geometric else 0.8,
                    "exact_intersection_calls": 20 if is_bucketed else 100,
                    "same_as_linear_same_intersection": not is_geometric,
                    "same_intersection_pair": True,
                    "success": True,
                    "points_outside": 0,
                })

        result = summarize(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["trials"], 2)
        self.assertEqual(result[0]["median_linear_bucketing_speedup"], 2.0)
        self.assertEqual(result[0]["median_combined_speedup_vs_original"], 5.0)
        self.assertEqual(result[0]["median_linear_exact_call_reduction"], 5.0)
        self.assertTrue(result[0]["all_intersection_pairs_identical"])
        self.assertTrue(result[0]["all_outputs_valid"])
        table = latex_table(result)
        self.assertIn(r"\begin{table*}", table)
        self.assertIn("sample", table)


if __name__ == "__main__":
    unittest.main()
