"""用手算和独立的高斯覆盖概率检查最小实践。"""

import math
import unittest

import numpy as np
from numpy.testing import assert_allclose

from run_uncertainty_demo import (
    KNOWN_SIGMA_M, Z95, interval_half_widths, probability_metrics,
    repeated_coverage, summarize_measurements,
)


class UncertaintyChecks(unittest.TestCase):
    def test_sample_statistics_against_hand_calculation(self):
        row = summarize_measurements([0.48, 0.50, 0.52], 0.02)
        self.assertAlmostEqual(row["sample_mean_m"], 0.5)
        self.assertAlmostEqual(row["sample_variance_m2"], 0.0004)
        self.assertAlmostEqual(row["sample_std_m"], 0.02)

    def test_interval_scaling_and_prediction_noise_floor(self):
        ci1, pi1 = interval_half_widths(1, 0.02)
        ci100, pi100 = interval_half_widths(100, 0.02)
        self.assertAlmostEqual(ci1 / ci100, 10)
        self.assertAlmostEqual((pi1 / ci1)**2, 2)
        self.assertAlmostEqual((pi100 / Z95)**2, 0.02**2 + (ci100 / Z95)**2)
        _, pi_large = interval_half_widths(1_000_000, 0.02)
        self.assertAlmostEqual(pi_large, Z95 * 0.02, places=7)
        shifted = summarize_measurements([1.48, 1.50, 1.52], 0.02)
        original = summarize_measurements([0.48, 0.50, 0.52], 0.02)
        assert_allclose(np.array(shifted["next_reading_pi95_m"]) - 1,
                        original["next_reading_pi95_m"])

    def test_empirical_coverage_against_independent_normal_integrals(self):
        # 独立解析积分：新读数减样本均值的标准差为 sigma*sqrt(1+1/n)。
        n, repeats, shift = 25, 20000, 0.06
        row = repeated_coverage(n, repeats, seed=2026, shift_m=shift)
        cdf = lambda z: (1 + math.erf(z / math.sqrt(2))) / 2
        scale = KNOWN_SIGMA_M * math.sqrt(1 + 1 / n)
        half = Z95 * scale
        expected = {
            "mean_ci_contains_truth": 0.95,
            "prediction_pi_contains_future": 0.95,
            "wrong_mean_ci_contains_future": 2 * cdf(Z95 / math.sqrt(n + 1)) - 1,
            "old_prediction_pi_contains_shifted_future":
                cdf((half - shift) / scale) - cdf((-half - shift) / scale),
        }
        for key, p in expected.items():
            with self.subTest(key=key):
                # 留出 5 个二项标准误，检查模拟是否对应指定概率模型。
                tolerance = 5 * math.sqrt(p * (1 - p) / repeats)
                self.assertLess(abs(row["coverage"][key] - p), tolerance)

    def test_probability_metrics_against_label_enumeration(self):
        labels = np.array([[1, 1, 1, 1, 0]])
        raw = probability_metrics([0.9], labels)
        adjusted = probability_metrics([0.8], labels)
        self.assertAlmostEqual(raw["brier_score"], 0.17)
        self.assertAlmostEqual(adjusted["brier_score"], 0.16)
        self.assertEqual(raw["accuracy_at_0_5"], adjusted["accuracy_at_0_5"])
        self.assertAlmostEqual(raw["mean_nll"], -(4 * math.log(0.9) + math.log(0.1)) / 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
