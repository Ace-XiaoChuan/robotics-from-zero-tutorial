"""核对 K-Means 中心求导和 PCA 四点算例；默认只用标准库。"""

from __future__ import annotations

import argparse
import math
import unittest


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def matvec(matrix, vector):
    return [dot(row, vector) for row in matrix]


def sample_mean(points):
    if not points:
        raise ValueError("非空样本才能求均值中心")
    return [sum(row[j] for row in points) / len(points)
            for j in range(len(points[0]))]


def cluster_loss(points, center):
    return sum(sum((x - mu) ** 2 for x, mu in zip(point, center))
               for point in points)


def center_gradient(points, center):
    return [2 * sum(mu - point[j] for point in points)
            for j, mu in enumerate(center)]


def finite_difference(function, point, index, h=1e-5):
    plus, minus = list(point), list(point)
    plus[index] += h
    minus[index] -= h
    return (function(plus) - function(minus)) / (2 * h)


def four_points():
    r = math.sqrt(3) / 2
    return [[2 + 3*r, 1 + 3*r], [2 - 3*r, 1 - 3*r],
            [2 + r, 1 - r], [2 - r, 1 + r]]


def centered_covariance(points):
    mean = sample_mean(points)
    centered = [[x - mu for x, mu in zip(point, mean)] for point in points]
    dimensions = len(mean)
    covariance = [[sum(row[j] * row[k] for row in centered) / (len(points) - 1)
                   for k in range(dimensions)] for j in range(dimensions)]
    return mean, centered, covariance


def directions():
    h = 1 / math.sqrt(2)
    return [[h, h], [h, -h]]


def project(centered, axes):
    return [[dot(point, axis) for axis in axes] for point in centered]


def reconstruct(scores, axes, mean):
    return [[mean[j] + sum(score[k] * axes[k][j] for k in range(len(axes)))
             for j in range(len(mean))] for score in scores]


class DerivationChecks(unittest.TestCase):
    def assert_vector_close(self, actual, expected, tolerance=1e-12):
        self.assertEqual(len(actual), len(expected))
        for value, reference in zip(actual, expected):
            self.assertAlmostEqual(value, reference, delta=tolerance)

    def test_center_gradient_matches_finite_difference(self):
        cases = [([[0., 0.], [0., 2.]], [.3, -.4]),
                 ([[1., -2., 3.], [4., 2., -1.], [-2., 3., 5.]], [.7, -.4, 2.])]
        maximum_error = 0.
        for points, center in cases:
            analytic = center_gradient(points, center)
            numerical = [finite_difference(lambda mu: cluster_loss(points, mu), center, j)
                         for j in range(len(center))]
            maximum_error = max(maximum_error, max(abs(a-b) for a,b in zip(analytic, numerical)))
            self.assert_vector_close(numerical, analytic, tolerance=2e-8)
        print(f"中心梯度最大有限差分绝对误差：{maximum_error:.3e}")

    def test_mean_minimizes_fixed_group_loss(self):
        for points in ([[0., 0.], [0., 2.]], [[8., 0.], [8., 2.]],
                       [[1., 2.], [-2., 5.], [4., -1.]]):
            mean = sample_mean(points)
            self.assert_vector_close(center_gradient(points, mean), [0., 0.])
            for offset in ([.2, -.3], [-4., 2.]):
                shifted = [mu + delta for mu, delta in zip(mean, offset)]
                difference = cluster_loss(points, shifted) - cluster_loss(points, mean)
                self.assertAlmostEqual(difference, len(points) * dot(offset, offset), delta=1e-12)
        self.assertEqual(sample_mean([[0., 0.], [0., 2.]]), [0., 1.])

    def test_empty_group_has_no_unique_mean(self):
        self.assertEqual(cluster_loss([], [1., 9.]), 0.)
        self.assertEqual(cluster_loss([], [-3., 2.]), 0.)
        self.assertEqual(center_gradient([], [1., 9.]), [0., 0.])
        with self.assertRaises(ValueError):
            sample_mean([])

    def test_covariance_and_variance_gradient(self):
        mean, centered, covariance = centered_covariance(four_points())
        self.assert_vector_close(mean, [2., 1.])
        for actual, expected in zip(covariance, [[5., 4.], [4., 5.]]):
            self.assert_vector_close(actual, expected)
        self.assert_vector_close([sum(row[j] for row in centered) for j in range(2)], [0., 0.])
        u = [.6, -.8]
        variance = lambda direction: dot(direction, matvec(covariance, direction))
        numerical = [finite_difference(variance, u, j) for j in range(2)]
        self.assert_vector_close(numerical, [2*x for x in matvec(covariance, u)], tolerance=1e-9)
        scores = [dot(point, u) for point in centered]
        self.assertAlmostEqual(sum(z*z for z in scores) / 3, variance(u), delta=1e-12)

    def test_eigenvectors_orthogonality_and_variance_maximum(self):
        covariance = [[5., 4.], [4., 5.]]
        u1, u2 = directions()
        self.assertAlmostEqual(dot(u1, u1), 1., delta=1e-12)
        self.assertAlmostEqual(dot(u2, u2), 1., delta=1e-12)
        self.assertAlmostEqual(dot(u1, u2), 0., delta=1e-12)
        for axis, value in ((u1, 9.), (u2, 1.)):
            self.assert_vector_close(matvec(covariance, axis), [value*x for x in axis])
            self.assert_vector_close([2*(s-value*x) for s,x in zip(matvec(covariance, axis), axis)], [0., 0.])
        for angle in (0., .2, math.pi/4, .9, math.pi/2, math.pi):
            unit = [math.cos(angle), math.sin(angle)]
            self.assertLessEqual(dot(unit, matvec(covariance, unit)), 9. + 1e-12)
        self.assertAlmostEqual(dot(u1, matvec(covariance, u1)), 9., delta=1e-12)

    def test_scores_full_and_truncated_reconstruction(self):
        points = four_points()
        mean, centered, _ = centered_covariance(points)
        axes = directions()
        scores = project(centered, axes)
        a, b = 3*math.sqrt(1.5), math.sqrt(1.5)
        expected = [[a, 0.], [-a, 0.], [0., b], [0., -b]]
        for actual, target in zip(scores, expected):
            self.assert_vector_close(actual, target)
        for actual, target in zip(reconstruct(scores, axes, mean), points):
            self.assert_vector_close(actual, target)
        truncated = reconstruct([[row[0]] for row in scores], axes[:1], mean)
        for actual, target in zip(truncated, [points[0], points[1], mean, mean]):
            self.assert_vector_close(actual, target)
        residual = sum(sum((x-y)**2 for x,y in zip(point, restored))
                       for point,restored in zip(points, truncated))
        self.assertAlmostEqual(residual, 3., delta=1e-12)
        self.assertAlmostEqual(9 / (9+1), .9)
        _, _, score_covariance = centered_covariance(scores)
        for actual, target in zip(score_covariance, [[9., 0.], [0., 1.]]):
            self.assert_vector_close(actual, target)

    def test_axis_sign_does_not_change_reconstruction(self):
        mean, centered, _ = centered_covariance(four_points())
        axes = directions()[:1]
        opposite = [[-x for x in axes[0]]]
        original = reconstruct(project(centered, axes), axes, mean)
        flipped = reconstruct(project(centered, opposite), opposite, mean)
        for actual, target in zip(flipped, original):
            self.assert_vector_close(actual, target)


class SklearnInterfaceChecks(DerivationChecks):
    """只加载一个接口核对方法，不重复运行继承的标准库方法。"""

    def test_pca_interface_matches_manual_projection(self):
        import numpy as np
        import sklearn
        from sklearn.decomposition import PCA

        points = np.asarray(four_points())
        axes = np.asarray(directions())
        pca = PCA(n_components=2, svd_solver="full", whiten=False)
        scores = pca.fit_transform(points)
        self.assertEqual(pca.components_.shape, (2, 2))
        np.testing.assert_allclose(pca.mean_, [2., 1.], atol=1e-12, rtol=0)
        np.testing.assert_allclose(pca.explained_variance_, [9., 1.], atol=1e-12, rtol=0)
        np.testing.assert_allclose(pca.explained_variance_ratio_, [.9, .1], atol=1e-12, rtol=0)
        for actual, target in zip(pca.components_, axes):
            self.assertAlmostEqual(abs(float(actual @ target)), 1., delta=1e-12)
        np.testing.assert_allclose(scores, (points-pca.mean_) @ pca.components_.T, atol=1e-12, rtol=0)
        np.testing.assert_allclose(pca.transform(points), scores, atol=1e-12, rtol=0)
        np.testing.assert_allclose(pca.inverse_transform(scores), points, atol=1e-12, rtol=0)
        one = PCA(n_components=1, svd_solver="full", whiten=False)
        z = one.fit_transform(points)
        restored = one.inverse_transform(z)
        expected = np.vstack((points[:2], np.tile([2., 1.], (2, 1))))
        np.testing.assert_allclose(restored, expected, atol=1e-12, rtol=0)
        self.assertAlmostEqual(float(np.sum((points-restored)**2)), 3., delta=1e-12)
        print(f"PCA 接口核对：scikit-learn {sklearn.__version__}、NumPy {np.__version__}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sklearn", action="store_true", help="加入 NumPy/scikit-learn 四点接口核对")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DerivationChecks)
    if args.sklearn:
        suite.addTest(SklearnInterfaceChecks("test_pca_interface_matches_manual_projection"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
