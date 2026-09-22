"""Verify the small planar examples in the kinematics review chapters."""

import contextlib
import io
import math
from pathlib import Path
import platform
import runpy
import unittest

import numpy as np
from numpy.testing import assert_allclose


LENGTHS = np.array([0.4, 0.3])


def planar_position(q, lengths=LENGTHS):
    angles = np.cumsum(q)
    return np.array([lengths @ np.cos(angles), lengths @ np.sin(angles)])


def planar_jacobian(q, lengths=LENGTHS):
    angles = np.cumsum(q)
    return np.array([
        [-np.sum(lengths[i:] * np.sin(angles[i:])) for i in range(len(q))],
        [np.sum(lengths[i:] * np.cos(angles[i:])) for i in range(len(q))],
    ])


def rz(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rx(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def transform(rotation=None, translation=None):
    result = np.eye(4)
    if rotation is not None:
        result[:3, :3] = rotation
    if translation is not None:
        result[:3, 3] = translation
    return result


def standard_dh(a, alpha, d, theta):
    return (
        transform(rz(theta)) @ transform(translation=[0, 0, d])
        @ transform(translation=[a, 0, 0]) @ transform(rx(alpha))
    )


def planar_ik_branches(target):
    l1, l2 = LENGTHS
    c2 = (np.dot(target, target) - l1**2 - l2**2) / (2 * l1 * l2)
    if abs(c2) > 1 + 1e-12:
        return []
    c2 = np.clip(c2, -1, 1)
    solutions = []
    for sign in (1, -1):
        s2 = sign * math.sqrt(max(0.0, 1 - c2**2))
        q2 = math.atan2(s2, c2)
        q1 = math.atan2(target[1], target[0]) - math.atan2(l2 * s2, l1 + l2 * c2)
        solutions.append(np.array([q1, q2]))
    return solutions


def local_position_ik(target, seed, max_iterations=80):
    """Bounded teaching iteration for a 2R position task, without joint limits."""
    q = np.array(seed, dtype=float)
    target = np.asarray(target, dtype=float)
    radius = np.linalg.norm(target)
    if not abs(LENGTHS[0] - LENGTHS[1]) - 1e-12 <= radius <= sum(LENGTHS) + 1e-12:
        return q, "outside_workspace", 0, np.linalg.norm(target - planar_position(q))
    for iteration in range(max_iterations + 1):
        error = target - planar_position(q)
        residual = np.linalg.norm(error)
        if residual <= 1e-10:
            return q, "converged", iteration, residual
        if iteration == max_iterations:
            return q, "max_iterations", iteration, residual
        jacobian = planar_jacobian(q)
        step = np.linalg.solve(
            jacobian.T @ jacobian + 1e-6 * np.eye(2), jacobian.T @ error
        )
        if np.linalg.norm(step) <= 1e-12:
            return q, "stalled", iteration, residual
        step *= min(1.0, 0.2 / np.max(np.abs(step)))
        q += step


class KinematicsExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent / "02_dh_conventions" / "lesson4_Modified_D-H.py"
        with contextlib.redirect_stdout(io.StringIO()):
            cls.legacy = runpy.run_path(str(path))

    def test_forward_kinematics_table(self):
        for q, expected in (
            ([0, 0], [0.7, 0]),
            ([0, math.pi / 2], [0.4, 0.3]),
            ([math.pi / 2, 0], [0, 0.7]),
            (np.deg2rad([30, 45]), [0.4240558750445318, 0.48977774788672046]),
        ):
            assert_allclose(planar_position(q), expected, atol=1e-12)

    def test_relative_angle_and_periodicity(self):
        q = np.array([0.3, -0.7])
        assert_allclose(planar_position(q + [2 * math.pi, 0]), planar_position(q), atol=1e-12)
        wrong = LENGTHS @ np.array([math.cos(q[0]), math.cos(q[1])])
        self.assertGreater(abs(wrong - planar_position(q)[0]), 1e-3)

    def test_modified_dh_matches_factorization(self):
        get_mdh = self.legacy["get_dh_matrix"]
        for a, alpha, d, theta in ((0.4, 0.3, 0.2, -0.7), (-0.2, -0.5, 0.1, 1.2)):
            expected = (
                transform(rx(alpha)) @ transform(translation=[a, 0, 0])
                @ transform(rz(theta)) @ transform(translation=[0, 0, d])
            )
            assert_allclose(get_mdh(a, alpha, d, theta), expected, atol=1e-12)

    def test_dh_conventions_match_geometry(self):
        get_mdh = self.legacy["get_dh_matrix"]
        for q in ([0, math.pi / 2], [0.3, -0.7], [-1, 0.6], [0, 0]):
            standard = standard_dh(0.4, 0, 0, q[0]) @ standard_dh(0.3, 0, 0, q[1])
            modified = get_mdh(0, 0, 0, q[0]) @ get_mdh(0.4, 0, 0, q[1]) @ get_mdh(0.3, 0, 0, 0)
            expected = transform(rz(sum(q)), np.r_[planar_position(q), 0])
            assert_allclose(standard, expected, atol=1e-12)
            assert_allclose(modified, expected, atol=1e-12)

    def test_original_lesson4_numeric_result(self):
        expected = planar_position(np.deg2rad([30, 45]), np.array([10.0, 5.0]))
        assert_allclose(self.legacy["T_total"][:2, 3], expected, atol=1e-12)
        assert_allclose(expected, [9.954349263356992, 9.82962913144534], atol=1e-12)

    def test_wrong_dh_table_changes_geometry(self):
        get_mdh = self.legacy["get_dh_matrix"]
        wrong = get_mdh(0.4, 0, 0, 0) @ get_mdh(0.3, 0, 0, math.pi / 2)
        assert_allclose(wrong[:3, 3], [0.7, 0, 0], atol=1e-12)
        self.assertGreater(np.linalg.norm(wrong[:2, 3] - [0.4, 0.3]), 0.4)

    def test_joint_mapping_and_zero_offset(self):
        names, positions = ["joint2", "joint1"], [math.pi / 2, 0]
        mapping = dict(zip(names, positions))
        q = [mapping[name] for name in ["joint1", "joint2"]]
        assert_allclose(planar_position(q), [0.4, 0.3], atol=1e-12)
        assert_allclose(planar_position(positions), [0, 0.7], atol=1e-12)
        self.assertAlmostEqual(1 * (0.1 - 0.1), 0.0)

    def test_tcp_and_base_transforms(self):
        t_b_f = transform(rz(math.pi / 2), [0.4, 0.3, 0])
        t_f_tcp = transform(translation=[0.1, 0, 0])
        t_b_tcp = t_b_f @ t_f_tcp
        assert_allclose(t_b_tcp[:3, 3], [0.4, 0.4, 0], atol=1e-12)
        t_w_b = transform(rz(math.pi / 2), [1, 2, 0])
        t_w_tcp = t_w_b @ t_b_tcp
        assert_allclose(t_w_tcp[:3, 3], [0.6, 2.4, 0], atol=1e-12)
        assert_allclose(t_w_tcp[:3, :3], rz(math.pi), atol=1e-12)

    def test_jacobian_finite_differences(self):
        h = 1e-6
        errors = []
        for lengths, states in (
            (LENGTHS, ([0, 0], [0, math.pi / 2], [0.3, -0.7], [-1.1, 0.2])),
            (np.array([0.3, 0.2, 0.1]), ([0, math.pi / 2, -math.pi / 2], [0.2, -0.6, 0.4])),
        ):
            for state in states:
                q = np.array(state, dtype=float)
                numeric = np.column_stack([
                    (planar_position(q + h * axis, lengths) - planar_position(q - h * axis, lengths)) / (2 * h)
                    for axis in np.eye(len(q))
                ])
                analytic = planar_jacobian(q, lengths)
                assert_allclose(numeric, analytic, atol=1e-9, rtol=0)
                errors.append(np.max(np.abs(numeric - analytic)))
        print(f"\nMaximum Jacobian finite-difference error: {max(errors):.3e} m/rad", flush=True)

    def test_geometric_jacobian(self):
        point = np.array([0.4, 0.3, 0])
        origins = (np.zeros(3), np.array([0.4, 0, 0]))
        geometric = np.column_stack([np.cross([0, 0, 1], point - origin)[:2] for origin in origins])
        assert_allclose(geometric, planar_jacobian([0, math.pi / 2]), atol=1e-12)

    def test_joint_and_task_velocities(self):
        jacobian = planar_jacobian([0, math.pi / 2])
        qdot = np.array([0.1, -0.2])
        assert_allclose(jacobian, [[-0.3, -0.3], [0.4, 0]], atol=1e-12)
        assert_allclose(jacobian @ qdot, [0.03, 0.04], atol=1e-12)
        self.assertAlmostEqual(sum(qdot), -0.1)

    def test_offset_tcp_jacobian(self):
        q = [0, math.pi / 2]
        tcp_jacobian = planar_jacobian(q, np.array([0.4, 0.4]))
        assert_allclose(tcp_jacobian, [[-0.4, -0.4], [0.4, 0]], atol=1e-12)
        correction = np.cross([0, 0, 1], [0, 0.1, 0])[:2]
        assert_allclose(tcp_jacobian, planar_jacobian(q) + correction[:, None], atol=1e-12)

    def test_analytic_ik_branches(self):
        solutions = planar_ik_branches([0.4, 0.3])
        self.assertEqual(len(solutions), 2)
        assert_allclose(solutions[0], [0, math.pi / 2], atol=1e-12)
        assert_allclose(solutions[1], [1.2870022175865687, -math.pi / 2], atol=1e-12)
        for q in solutions:
            assert_allclose(planar_position(q), [0.4, 0.3], atol=1e-12)

    def test_analytic_ik_workspace_rejection(self):
        for target in ([0.8, 0], [0.05, 0]):
            self.assertEqual(planar_ik_branches(target), [])
        for target in ([0.7, 0], [0.1, 0]):
            for q in planar_ik_branches(target):
                assert_allclose(planar_position(q), target, atol=1e-12)

    def test_position_solution_does_not_satisfy_arbitrary_orientation(self):
        angles = [sum(q) for q in planar_ik_branches([0.4, 0.3])]
        assert_allclose(np.rad2deg(angles), [90, -16.26020470831196], atol=1e-10)
        for angle in angles:
            self.assertGreater(abs(math.atan2(math.sin(angle), math.cos(angle))), 0.2)

    def test_branch_selection_with_joint_limits(self):
        solutions = planar_ik_branches([0.4, 0.3])
        valid = [q for q in solutions if 0 <= q[1] <= math.pi]
        self.assertEqual(len(valid), 1)
        assert_allclose(valid[0], [0, math.pi / 2], atol=1e-12)

    def test_local_ik_step_has_nonlinear_residual(self):
        q = np.array([0.0, math.pi / 2])
        target = np.array([0.39, 0.31])
        error = target - planar_position(q)
        jacobian = planar_jacobian(q)
        step = np.linalg.solve(jacobian, error)
        assert_allclose(step, [0.025, 1 / 120], atol=1e-12)
        assert_allclose(jacobian @ step, error, atol=1e-12)
        residual = np.linalg.norm(target - planar_position(q + step))
        self.assertGreater(residual, 1e-5)
        self.assertLess(residual, 3e-4)
        print(f"\nOne-step nonlinear IK residual: {residual:.9f} m", flush=True)

    def test_local_ik_convergence(self):
        target = [0.4, 0.3]
        q, reason, iterations, residual = local_position_ik(target, [0.2, 1.0])
        self.assertEqual(reason, "converged")
        self.assertLessEqual(residual, 1e-10)
        self.assertLessEqual(iterations, 80)
        assert_allclose(planar_position(q), target, atol=1e-10, rtol=0)
        print(f"\nTeaching IK: {iterations} iterations, residual={residual:.3e} m", flush=True)

    def test_local_ik_failure_reasons(self):
        self.assertEqual(local_position_ik([0.8, 0], [0.2, 1.0])[1], "outside_workspace")
        self.assertEqual(local_position_ik([0.69, 0], [0, 0])[1], "stalled")
        self.assertTrue(planar_ik_branches([0.69, 0]))
        self.assertEqual(local_position_ik([0.4, 0.3], [0.2, 1.0], max_iterations=0)[1], "max_iterations")

    def test_singularity_determinant_and_rank(self):
        for q2 in (0, 0.001, math.pi / 2, math.pi):
            jacobian = planar_jacobian([0.3, q2])
            self.assertAlmostEqual(np.linalg.det(jacobian), 0.12 * math.sin(q2))
        straight = planar_jacobian([0, 0])
        self.assertEqual(np.linalg.matrix_rank(straight), 1)
        assert_allclose(straight @ [0.1, 0], [0, 0.07], atol=1e-12)

    def test_near_singular_values_and_manipulability(self):
        jacobian = planar_jacobian([0, 0.001])
        singular_values = np.linalg.svd(jacobian, compute_uv=False)
        assert_allclose(singular_values, [0.761577216, 0.000157567713], rtol=1e-8)
        self.assertAlmostEqual(np.linalg.cond(jacobian), 4833.332931992631, places=5)
        for q2 in (0, 0.001, math.pi / 2):
            j = planar_jacobian([0, q2])
            w = math.sqrt(max(0.0, np.linalg.det(j @ j.T)))
            self.assertAlmostEqual(w, abs(0.12 * math.sin(q2)), places=10)

    def test_task_relative_rank(self):
        position = planar_jacobian([0, 0])
        full_pose = np.vstack((position, [1, 1]))
        self.assertEqual(np.linalg.matrix_rank(position), 1)
        self.assertEqual(np.linalg.matrix_rank(full_pose), 2)

    def test_redundancy_depends_on_task(self):
        lengths = np.array([0.3, 0.2, 0.1])
        q = [0, math.pi / 2, -math.pi / 2]
        j = planar_jacobian(q, lengths)
        n = np.array([1, -1, -3])
        assert_allclose(planar_position(q, lengths), [0.4, 0.2], atol=1e-12)
        assert_allclose(j, [[-0.2, -0.2, 0], [0.4, 0.1, 0.1]], atol=1e-12)
        assert_allclose(j @ n, [0, 0], atol=1e-12)
        self.assertEqual(np.linalg.matrix_rank(j), 2)
        self.assertEqual(np.linalg.matrix_rank(np.vstack((j, [1, 1, 1]))), 3)
        self.assertAlmostEqual(sum(0.1 * n), -0.3)

    def test_nullspace_finite_step_drift(self):
        lengths = np.array([0.3, 0.2, 0.1])
        q = np.array([0, math.pi / 2, -math.pi / 2])
        step = 0.01 * np.array([1, -1, -3])
        actual = planar_position(q + step, lengths)
        assert_allclose(actual, [0.3999400034999025, 0.20000039998000043], atol=1e-12)
        drift = np.linalg.norm(actual - planar_position(q, lengths))
        self.assertAlmostEqual(drift, 5.999783336465323e-5)
        self.assertAlmostEqual(sum(q + step), -0.03)

    def test_exact_and_damped_nullspace_projection(self):
        j = planar_jacobian([0, math.pi / 2, -math.pi / 2], np.array([0.3, 0.2, 0.1]))
        exact_projector = np.eye(3) - np.linalg.pinv(j) @ j
        assert_allclose(j @ exact_projector, np.zeros((2, 3)), atol=1e-12)
        damped_inverse = j.T @ np.linalg.solve(j @ j.T + 0.1**2 * np.eye(2), np.eye(2))
        damped_projector = np.eye(3) - damped_inverse @ j
        self.assertGreater(np.linalg.norm(j @ damped_projector), 1e-3)

    def test_workspace_joint_limit_boundary(self):
        q2_samples = np.linspace(0, math.pi / 2, 101)
        radii = [np.linalg.norm(planar_position([0.3, q2])) for q2 in q2_samples]
        self.assertAlmostEqual(min(radii), 0.5)
        self.assertAlmostEqual(max(radii), 0.7)
        solutions = planar_ik_branches([0.2, 0])
        self.assertEqual(len(solutions), 2)
        for q in solutions:
            self.assertFalse(0 <= q[1] <= math.pi / 2)
            self.assertAlmostEqual(abs(q[1]), 2.636232143305636)
        self.assertAlmostEqual(np.linalg.det(planar_jacobian([0, math.pi / 2])), 0.12)


if __name__ == "__main__":
    print(f"Python {platform.python_version()}, NumPy {np.__version__}", flush=True)
    unittest.main(verbosity=2)
