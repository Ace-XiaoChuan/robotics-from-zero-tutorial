"""Check the numerical examples in spatial math chapters 05 through 10."""

import math
import platform
import unittest

import numpy as np
from numpy.testing import assert_allclose


def rz(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def transform(rotation, translation):
    result = np.eye(4)
    result[:3, :3] = rotation
    result[:3, 3] = translation
    return result


def quaternion_rotate(q_wxyz, vector):
    w = q_wxyz[0]
    xyz = q_wxyz[1:]
    return vector + 2 * np.cross(xyz, np.cross(xyz, vector) + w * vector)


class SpatialMathExamples(unittest.TestCase):
    def test_rotation_representations(self):
        rotation = rz(math.pi / 2)
        assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(rotation), 1.0)
        q = np.array([math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5)])
        self.assertAlmostEqual(np.linalg.norm(q), 1.0)
        for vector in np.eye(3):
            assert_allclose(quaternion_rotate(q, vector), rotation @ vector, atol=1e-12)
            assert_allclose(quaternion_rotate(-q, vector), rotation @ vector, atol=1e-12)
        assert_allclose(rotation @ [1, 0, 0], [0, 1, 0], atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(np.diag([1, 1, -1])), -1.0)

    def test_rotation_order(self):
        rx = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
        vector = np.array([0.0, 1.0, 0.0])
        assert_allclose(rz(math.pi / 2) @ rx @ vector, [0, 0, 1], atol=1e-12)
        assert_allclose(rx @ rz(math.pi / 2) @ vector, [-1, 0, 0], atol=1e-12)

    def test_point_direction_and_inverse(self):
        rotation = rz(math.pi / 2)
        translation = np.array([1.0, 2.0, 3.0])
        t_a_b = transform(rotation, translation)
        assert_allclose(t_a_b @ [1, 0, 0, 1], [1, 3, 3, 1], atol=1e-12)
        assert_allclose(t_a_b @ [1, 0, 0, 0], [0, 1, 0, 0], atol=1e-12)
        t_b_a = transform(rotation.T, -rotation.T @ translation)
        assert_allclose(t_b_a[:3, 3], [-2, 1, -3], atol=1e-12)
        assert_allclose(t_b_a @ t_a_b, np.eye(4), atol=1e-12)
        assert_allclose(t_b_a @ [1, 3, 3, 1], [1, 0, 0, 1], atol=1e-12)

    def test_transform_composition(self):
        t_a_b = transform(rz(math.pi / 2), [1, 0, 0])
        t_b_c = transform(rz(math.pi / 2), [0, 2, 0])
        t_a_c = t_a_b @ t_b_c
        assert_allclose(t_a_c[:3, :3], rz(math.pi), atol=1e-12)
        assert_allclose(t_a_c[:3, 3], [-1, 0, 0], atol=1e-12)
        assert_allclose(t_b_c @ [1, 0, 0, 1], [0, 3, 0, 1], atol=1e-12)
        assert_allclose(t_a_c @ [1, 0, 0, 1], [-2, 0, 0, 1], atol=1e-12)

    def test_pose_error_frames_and_angle_wrap(self):
        current = transform(rz(math.pi / 2), [1, 0, 0])
        target = transform(rz(math.pi), [1, 1, 0])
        world_error = target[:3, 3] - current[:3, 3]
        assert_allclose(world_error, [0, 1, 0])
        assert_allclose(current[:3, :3].T @ world_error, [1, 0, 0], atol=1e-12)
        relative = np.linalg.solve(current, target)
        assert_allclose(relative[:3, :3], rz(math.pi / 2), atol=1e-12)
        assert_allclose(relative[:3, 3], [1, 0, 0], atol=1e-12)
        angle = math.acos(np.clip((np.trace(relative[:3, :3]) - 1) / 2, -1, 1))
        self.assertAlmostEqual(angle, math.pi / 2)
        raw_difference = math.radians(-179 - 179)
        wrapped = math.atan2(math.sin(raw_difference), math.cos(raw_difference))
        self.assertAlmostEqual(math.degrees(wrapped), 2.0)

    def test_pose_log_translation_reconstruction(self):
        theta = math.pi / 2
        phi_hat = np.array([[0.0, -theta, 0.0], [theta, 0.0, 0.0], [0.0, 0.0, 0.0]])
        # SE(3) exponential translation map, evaluated away from zero angle.
        v_matrix = (
            np.eye(3)
            + (1 - math.cos(theta)) / theta**2 * phi_hat
            + (theta - math.sin(theta)) / theta**3 * (phi_hat @ phi_hat)
        )
        expected_v = np.array([[2 / math.pi, -2 / math.pi, 0],
                               [2 / math.pi, 2 / math.pi, 0], [0, 0, 1]])
        assert_allclose(v_matrix, expected_v, atol=1e-12)
        rho = np.array([math.pi / 4, -math.pi / 4, 0])
        assert_allclose(v_matrix @ rho, [1, 0, 0], atol=1e-12)

    def test_local_linearization_and_error_scales(self):
        self.assertAlmostEqual(math.sin(0.1), 0.09983341664682815)
        self.assertAlmostEqual(0.1 - math.sin(0.1), 0.00016658335317185)
        self.assertAlmostEqual(math.sin(1.0), 0.8414709848078965)
        step = 1e-6
        derivative = (math.sin(step) - math.sin(-step)) / (2 * step)
        self.assertAlmostEqual(derivative, 1.0)
        assert_allclose(np.array([0.01, 0.1]) / [0.01, 0.1], [1, 1])

    def test_constant_least_squares(self):
        a_matrix = np.ones((3, 1))
        b = np.array([0.98, 1.01, 1.01])
        x, _, rank, _ = np.linalg.lstsq(a_matrix, b, rcond=None)
        self.assertEqual(rank, 1)
        assert_allclose(x, [1.0])
        residual = a_matrix @ x - b
        assert_allclose(residual, [0.02, -0.01, -0.01], atol=1e-12)
        self.assertAlmostEqual(residual @ residual, 0.0006)
        self.assertAlmostEqual(np.sqrt(np.mean(residual**2)), math.sqrt(0.0002))

    def test_linear_fit_and_identifiability(self):
        a_matrix = np.column_stack((np.ones(3), np.arange(3)))
        b = np.array([1.0, 2.0, 2.0])
        x, _, rank, _ = np.linalg.lstsq(a_matrix, b, rcond=None)
        self.assertEqual(rank, 2)
        assert_allclose(x, [7 / 6, 0.5], atol=1e-12)
        residual = a_matrix @ x - b
        assert_allclose(residual, [1 / 6, -1 / 3, 1 / 6], atol=1e-12)
        self.assertAlmostEqual(residual @ residual, 1 / 6)
        assert_allclose(a_matrix.T @ residual, [0, 0], atol=1e-12)
        all_at_zero = np.column_stack((np.ones(3), np.zeros(3)))
        self.assertEqual(np.linalg.matrix_rank(all_at_zero), 1)

    def test_weighted_least_squares(self):
        a_matrix = np.ones((2, 1))
        b = np.array([0.98, 1.02])
        sigma = np.array([0.02, 0.01])
        x = np.linalg.lstsq(a_matrix / sigma[:, None], b / sigma, rcond=None)[0]
        assert_allclose(x, [1.012])
        self.assertAlmostEqual(b.mean(), 1.0)

    def test_minimum_norm_and_nullspace(self):
        jacobian = np.array([[1.0, 1.0]])
        dq = np.linalg.pinv(jacobian) @ [0.2]
        assert_allclose(dq, [0.1, 0.1])
        self.assertAlmostEqual(dq @ dq, 0.02)
        for offset in (-0.3, 0.1, 0.5):
            alternate = dq + [offset, -offset]
            assert_allclose(jacobian @ alternate, [0.2])
            self.assertGreater(alternate @ alternate, dq @ dq)

    def test_pseudoinverse_and_damping(self):
        jacobian = np.diag([1.0, 0.01])
        dp = np.array([0.01, 0.01])
        assert_allclose(np.linalg.pinv(jacobian) @ dp, [0.01, 1.0])
        self.assertAlmostEqual(np.linalg.cond(jacobian), 100.0)
        self.assertAlmostEqual(np.linalg.cond(jacobian.T @ jacobian), 10000.0)
        damping = 0.1
        dq = np.linalg.solve(jacobian.T @ jacobian + damping**2 * np.eye(2), jacobian.T @ dp)
        assert_allclose(dq, [1 / 101, 1 / 101], atol=1e-12)
        assert_allclose(jacobian @ dq, [1 / 101, 1 / 10100], atol=1e-12)
        augmented = np.vstack((jacobian, damping * np.eye(2)))
        alternative = np.linalg.lstsq(augmented, np.r_[dp, [0, 0]], rcond=None)[0]
        assert_allclose(dq, alternative, atol=1e-12)

    def test_unreachable_linear_direction(self):
        jacobian = np.diag([1.0, 0.0])
        dp = np.array([0.01, 0.01])
        dq = np.linalg.pinv(jacobian) @ dp
        assert_allclose(dq, [0.01, 0])
        assert_allclose(dp - jacobian @ dq, [0, 0.01])

    def test_scalar_constrained_optimum(self):
        q = 0.0
        for expected in (0.4, 0.5, 0.5):
            q = np.clip(q - 0.5 * (q - 0.8), -0.3, 0.5)
            self.assertAlmostEqual(q, expected)
        self.assertAlmostEqual(0.5 * (q - 0.8)**2, 0.045)
        self.assertGreater(0.8, 0.5)

    def test_coupled_qp_optimum(self):
        desired = np.array([0.8, 0.8])
        # Solve the active-constraint KKT system, then check all constraints.
        kkt = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 0.0]])
        solution = np.linalg.solve(kkt, np.r_[desired, 1.0])
        x, multiplier = solution[:2], solution[2]
        assert_allclose(x, [0.5, 0.5])
        self.assertAlmostEqual(multiplier, 0.3)
        self.assertTrue(np.all((x >= 0) & (x <= 1)))
        self.assertLessEqual(x.sum(), 1.0)
        self.assertGreaterEqual(multiplier, 0)
        self.assertAlmostEqual(multiplier * (x.sum() - 1), 0)
        assert_allclose(x - desired + multiplier * np.ones(2), [0, 0], atol=1e-12)
        self.assertAlmostEqual(0.5 * np.sum((x - desired)**2), 0.09)
        self.assertAlmostEqual(0.5 * np.sum((np.array([1, 0]) - desired)**2), 0.34)
        self.assertGreater(np.clip(desired, 0, 1).sum(), 1)

    def test_infeasibility_and_one_step_velocity_bound(self):
        upper = np.array([1.0, 1.0])
        self.assertLess(upper.sum(), 3.0)
        q_now, q_upper, dt = 0.49, 0.50, 0.01
        velocity_bound = (q_upper - q_now) / dt
        self.assertAlmostEqual(velocity_bound, 1.0)
        self.assertAlmostEqual(q_now + velocity_bound * dt, q_upper)


if __name__ == "__main__":
    print(f"Python {platform.python_version()}, NumPy {np.__version__}", flush=True)
    unittest.main(verbosity=2)
