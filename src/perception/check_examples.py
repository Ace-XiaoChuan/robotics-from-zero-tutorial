"""核对六章教学算例；不依赖相机、ROS 或仿真模型。"""
import math
import unittest

import numpy as np
from numpy.testing import assert_allclose


class PerceptionExamples(unittest.TestCase):
    def test_projection_and_depth_ambiguity(self):
        points = np.array([[0.1, 0.05, 1], [0.2, 0.1, 2], [0.1, 0.05, 2]])
        pixels = 400 * points[:, :2] / points[:, 2, None] + [320, 240]
        assert_allclose(pixels, [[360, 260], [360, 260], [340, 250]])

    def test_intrinsics_image_mapping(self):
        intrinsic = np.array([[400, 0, 320], [0, 400, 240], [0, 0, 1]])
        mapping = np.diag([0.5, 0.5, 1])
        p = np.array([0.1, 0.05, 1])
        assert_allclose(mapping @ intrinsic @ p, [180, 130, 1])
        self.assertAlmostEqual(480 / (2 * math.tan(math.pi / 6)), 415.69219381653056)

    def test_scale_and_reprojection(self):
        self.assertAlmostEqual(400 * 0.1 / 40, 1)
        self.assertAlmostEqual(400 * 0.2 / 40, 2)
        residuals = np.array([[1, 0], [0, 1]])
        self.assertAlmostEqual(np.sqrt(np.mean(np.sum(residuals ** 2, axis=1))), 1)
        self.assertAlmostEqual(np.sqrt(np.mean(residuals ** 2)), 1 / math.sqrt(2))

    def test_rotated_transform_round_trip(self):
        rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        translation = np.array([0.4, 0, 0.5])
        target_camera = np.array([0.1, 0, 0.3])
        target_base = rotation @ target_camera + translation
        assert_allclose(target_base, [0.4, 0.1, 0.8])
        assert_allclose(rotation.T @ (target_base - translation), target_camera, atol=1e-15)
        self.assertFalse(np.allclose(target_base, translation + target_camera))

    def test_statistics_bias_and_outlier(self):
        readings = np.array([0.49, 0.5, 0.51])
        variance = readings.var(ddof=1)
        bias = readings.mean() - 0.47
        mse = np.mean((readings - 0.47) ** 2)
        self.assertAlmostEqual(readings.mean(), 0.5)
        self.assertAlmostEqual(math.sqrt(variance), 0.01)
        self.assertAlmostEqual(math.sqrt(mse), 0.0310912635103)
        self.assertAlmostEqual(mse, bias ** 2 + 2 * variance / 3)
        self.assertAlmostEqual(np.mean([*readings, 1.5]), 0.75)
        self.assertAlmostEqual(np.median([*readings, 1.5]), 0.505)

    def test_uncertainty_jacobian_finite_difference(self):
        # 输入顺序 [u / px, Z / m]；两列导数单位不同。
        x = np.array([360., 1.])
        def unproject_x(value):
            return (value[0] - 320) * value[1] / 400
        analytic = np.array([1 / 400, 40 / 400])
        numerical = []
        for i, h in enumerate([1e-3, 1e-5]):
            delta = np.zeros(2)
            delta[i] = h
            numerical.append((unproject_x(x + delta) - unproject_x(x - delta)) / (2 * h))
        assert_allclose(numerical, analytic, atol=1e-11, rtol=0)
        sigma_x = np.diag([2 ** 2, 0.02 ** 2])
        self.assertAlmostEqual(float(analytic @ sigma_x @ analytic.T), 0.000029)
        self.assertAlmostEqual(math.sqrt(0.000029), 0.00538516480713)

    def test_covariance_rotation(self):
        rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        sigma = np.diag([0.0001, 0.0004, 0.0009])
        transformed = rotation @ sigma @ rotation.T
        assert_allclose(transformed, np.diag([0.0004, 0.0001, 0.0009]))
        assert_allclose(np.linalg.eigvalsh(transformed), np.linalg.eigvalsh(sigma))

    def test_orientation_lever_arm_and_pose_errors(self):
        angle = math.radians(1)
        rotated = np.array([math.cos(angle), math.sin(angle), 0])
        exact = np.linalg.norm(rotated - [1, 0, 0])
        self.assertAlmostEqual(exact, 2 * math.sin(angle / 2))
        self.assertLess(abs(exact - angle), 3e-7)
        self.assertAlmostEqual(np.linalg.norm([0.003, 0.004, 0]), 0.005)
        a = math.radians(10)
        rotation = np.array([[math.cos(a), -math.sin(a), 0],
                             [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        self.assertAlmostEqual(math.acos(np.clip((np.trace(rotation)-1)/2, -1, 1)), a)

    def test_smoothing_lag(self):
        readings = np.arange(5) * 0.01
        self.assertAlmostEqual(readings.mean(), 0.02)
        self.assertAlmostEqual((readings[-1] - readings.mean()) / 0.1, 0.2)
        self.assertAlmostEqual(0.2 * 0.1 + 0.8 * 0, 0.02)

    def test_scalar_kalman_update(self):
        for measurement_variance, expected_gain, expected_state in [(0.01, 0.8, 0.48), (0.16, 0.2, 0.42)]:
            gain = 0.04 / (0.04 + measurement_variance)
            self.assertAlmostEqual(gain, expected_gain)
            self.assertAlmostEqual(0.4 + gain * (0.5 - 0.4), expected_state)
            # 信息形式是此例独立高斯信息融合的另一种计算方式。
            posterior_variance = 1 / (1 / 0.04 + 1 / measurement_variance)
            self.assertAlmostEqual((1 - gain) * 0.04, posterior_variance)
        self.assertAlmostEqual((1 - 0.8) * 0.04, 0.008)

    def test_position_velocity_kalman_update(self):
        transition = np.array([[1., 1.], [0., 1.]])
        observation = np.array([[1., 0.]])
        state = transition @ np.array([0., 1.])
        prior = transition @ np.diag([0.04, 0.01]) @ transition.T
        assert_allclose(prior, [[0.05, 0.01], [0.01, 0.01]])
        innovation_variance = (observation @ prior @ observation.T).item() + 0.01
        gain = prior @ observation.T / innovation_variance
        posterior_state = state + gain[:, 0] * (1.2 - (observation @ state).item())
        assert_allclose(posterior_state, [7 / 6, 31 / 30], atol=1e-12)
        residual_map = np.eye(2) - gain @ observation
        posterior = residual_map @ prior @ residual_map.T + gain @ gain.T * 0.01
        assert_allclose(posterior, [[1/120, 1/600], [1/600, 1/120]], atol=1e-12)
        assert_allclose(posterior, residual_map @ prior, atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(posterior).min(), 0)
        # 下一步缺测时只预测：仍保留运动，位置不确定性增大。
        predicted = transition @ posterior_state
        predicted_cov = transition @ posterior @ transition.T
        self.assertAlmostEqual(predicted[0], 2.2)
        self.assertGreater(predicted_cov[0, 0], posterior[0, 0])

    def test_time_alignment(self):
        delay = 1.2 - 1.0
        self.assertAlmostEqual(0.1 * delay, 0.02)
        interpolation_weight = (1.04 - 1.0) / (1.1 - 1.0)
        self.assertAlmostEqual((1-interpolation_weight)*0.4 + interpolation_weight*0.42, 0.408)
        self.assertGreater((1.2 - 1.0) / (1.1 - 1.0), 1)  # 属于外推。
        self.assertGreater(delay, 0.1)  # 超过正文的示意年龄阈值。


if __name__ == '__main__':
    unittest.main(verbosity=2)
