"""Check numerical solver against independent analytic properties."""
import unittest
import numpy as np
from numpy.testing import assert_allclose
from run import fit, predict, features, sample


class SolverChecks(unittest.TestCase):
    def test_exact_cubic(self):
        x = np.linspace(-1, 1, 20)
        y = 2 + x - 3*x*x + .5*x**3
        model = fit(x, y, 3, 0)
        z = np.linspace(-.9, .9, 31)
        assert_allclose(predict(model, z), 2+z-3*z*z+.5*z**3, atol=1e-12)

    def test_one_feature_closed_form(self):
        x, y = sample(30, 4)
        model = fit(x, y, 1, .2)
        z = (x-x.mean()) / x.std()
        expected = np.mean(z*(y-y.mean())) / 1.2
        assert_allclose(model['coef'], [y.mean(), expected], atol=1e-12)

    def test_intercept_not_penalized(self):
        x = np.linspace(-1, 1, 20)
        assert_allclose(predict(fit(x, np.full(20, 7.), 12, 100), x), 7., atol=1e-12)

    def test_stationarity(self):
        x, y = sample(40, 5)
        model = fit(x, y, 8, .01)
        z = (features(x, 8)-model['mean'])/model['scale']
        residual = predict(model, x)-y
        assert_allclose(z.T@residual/len(x)+.01*model['coef'][1:], 0., atol=1e-12)
        self.assertAlmostEqual(float(residual.mean()), 0.)

    def test_regularization_tradeoff(self):
        x, y = sample(30, 6)
        models = [fit(x, y, 12, strength) for strength in (0., .001, 1.)]
        losses = [np.mean((predict(m, x)-y)**2) for m in models]
        norms = [np.linalg.norm(m['coef'][1:]) for m in models]
        self.assertTrue(np.all(np.diff(losses) >= -1e-10))
        self.assertTrue(np.all(np.diff(norms) <= 1e-10))

    def test_prediction_uses_training_statistics(self):
        x, y = sample(30, 7)
        model = fit(x, y, 3, .01)
        before = model['mean'].copy()
        assert_allclose(predict(model, [.2]), predict(model, [.2, 100])[:1])
        assert_allclose(model['mean'], before)

    def test_reproducible_independent_draws(self):
        x, y = sample(30, 8)
        a, b = sample(30, 8)
        assert_allclose(x, a)
        assert_allclose(y, b)
        self.assertFalse(np.array_equal(x, sample(30, 9)[0]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
