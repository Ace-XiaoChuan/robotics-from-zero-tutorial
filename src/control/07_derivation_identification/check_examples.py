"""第七章检查：默认标准库推导核对，--identify 加入 NumPy 辨识检查。"""

import argparse
import math
from pathlib import Path
import runpy
import unittest

from run_examples import BASE, TRUTH, fit, identification, motion, regressor

HERE = Path(__file__).resolve().parent
PAIR = runpy.run_path(str(HERE.parent/'03_multi_joint_dynamics/check_examples.py'))


def partial(function, point, index, h=1e-5):
    plus, minus = list(point), list(point)
    plus[index] += h
    minus[index] -= h
    return (function(plus)-function(minus))/(2*h)


def lagrange_torque(q, velocity, acceleration):
    """从各刚体动能与质心势能做数值偏导，独立核对第三章解析动力学。"""
    h = 1e-4
    def lagrangian(position, speed):
        return PAIR['kinetic_from_bodies'](position,speed)-PAIR['potential'](position)
    qplus = [q[i]+velocity[i]*h+.5*acceleration[i]*h*h for i in range(2)]
    qminus = [q[i]-velocity[i]*h+.5*acceleration[i]*h*h for i in range(2)]
    vplus = [velocity[i]+acceleration[i]*h for i in range(2)]
    vminus = [velocity[i]-acceleration[i]*h for i in range(2)]
    torques = []
    for i in range(2):
        momentum_plus = partial(lambda v: lagrangian(qplus,v),vplus,i)
        momentum_minus = partial(lambda v: lagrangian(qminus,v),vminus,i)
        position_gradient = partial(lambda p: lagrangian(p,velocity),q,i)
        torques.append((momentum_plus-momentum_minus)/(2*h)-position_gradient+.2*velocity[i])
    return torques


class DerivationChecks(unittest.TestCase):
    def test_single_rod_energy_and_gravity(self):
        self.assertAlmostEqual(.06+2*.3**2,.24)
        potential = lambda q: 5.886*(1-math.cos(q[0]))
        for q in (-.8,0,.4,1.2):
            self.assertAlmostEqual(partial(potential,[q],0),5.886*math.sin(q),delta=1e-8)
        self.assertAlmostEqual(.24*2+.2*1+5.886*.5,3.623)

    def test_energy_power_balance(self):
        # E(q,v) 的方向导数应等于驱动和外力做功减去阻尼耗散。
        for q,v,motor,external in ((.3,1,2,.4),(-.6,-2,-1,.2),(0,0,1,0)):
            a = (motor+external-.2*v-5.886*math.sin(q))/.24
            energy = lambda z: .5*.24*z[1]**2+5.886*(1-math.cos(z[0]))
            derivative = partial(energy,[q,v],0)*v+partial(energy,[q,v],1)*a
            self.assertAlmostEqual(derivative,(motor+external)*v-.2*v*v,delta=1e-8)

    def test_two_link_lagrange_against_analytic(self):
        for q,v,a in (([.3,-.7],[1,-2],[-3,1]),([0,math.pi/2],[1,2],[1,0]),
                      ([-.9,.4],[-2,1],[2,-1])):
            numeric = lagrange_torque(q,v,a)
            expected = PAIR['required_motor'](q,v,a)
            for n,e in zip(numeric,expected):
                self.assertAlmostEqual(n,e,delta=2e-5)

    def test_three_snapshot_identification(self):
        # 三个独立瞬时状态的合成精确力矩，不是连续实验步骤。
        inertia = .84/2
        damping = .2/1
        coefficient = 4.4145/math.sin(math.pi/6)
        for found, true in zip((inertia,damping,coefficient),TRUTH):
            self.assertAlmostEqual(found,true)

    def test_payload_from_two_independent_changes(self):
        from_inertia = (TRUTH[0]-BASE[0])/.6**2
        from_gravity = (TRUTH[2]-BASE[2])/(9.81*.6)
        self.assertAlmostEqual(from_inertia,.5)
        self.assertAlmostEqual(from_gravity,.5)
        # 三参数只包含组合量：不同 m、lc、Ic 可给出同一 I、k。
        for m,lc,ic in ((2,.3,.06),(3,.2,.12)):
            self.assertAlmostEqual(ic+m*lc*lc,BASE[0])
            self.assertAlmostEqual(m*9.81*lc,BASE[2])


class IdentificationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        cls.np = np
        cls.report, cls.traces = identification()
        cls.cases = cls.report['cases']

    def test_exact_recovery(self):
        m = self.cases['noiseless']
        self.np.testing.assert_allclose(m['theta'],TRUTH,atol=1e-12,rtol=0)
        self.assertLess(m['validation_torque_rmse_nm'],1e-12)

    def test_noise_and_held_out_prediction(self):
        m = self.cases['torque_noise']
        self.np.testing.assert_allclose(m['theta'],TRUTH,atol=.005,rtol=0)
        self.assertLess(m['validation_torque_rmse_nm'],.003)
        self.assertGreater(m['base_validation_torque_rmse_nm'],.7)
        self.assertGreater(m['train_torque_rmse_nm'],.02)

    def test_static_data_cannot_identify_three_parameters(self):
        m = self.cases['static_only']
        self.assertEqual(m['rank'],1)
        self.assertEqual(m['status'],'rejected_rank')
        self.assertIsNone(m['theta'])

    def test_weak_excitation_rejected_even_with_full_rank(self):
        m = self.cases['weak_excitation']
        self.assertEqual(m['rank'],3)
        self.assertGreater(m['scaled_condition'],1e4)
        self.assertEqual(m['status'],'rejected_condition')

    def test_missing_friction_bias(self):
        m = self.cases['missing_friction']
        self.assertEqual(m['status'],'fitted')
        self.assertGreater(m['theta'][1],2*TRUTH[1])
        self.assertGreater(m['validation_torque_rmse_nm'],.05)

    def test_invalid_and_nonphysical_data(self):
        self.assertEqual(self.cases['negative_inertia']['status'],'rejected_physical_sign')
        with self.assertRaises(ValueError):
            fit([[1,2]], [1])
        with self.assertRaises(ValueError):
            fit([[1,2,3]]*3,[1,float('nan'),2])

    def test_analytic_motion_derivatives(self):
        np = self.np
        t = np.array([.2,1.7,3.4])
        h = 1e-5
        for validation in (False,True):
            q,v,a = motion(t,validation)
            before, after = motion(t-h,validation),motion(t+h,validation)
            np.testing.assert_allclose((after[0]-before[0])/(2*h),v,atol=1e-9,rtol=0)
            np.testing.assert_allclose((after[1]-before[1])/(2*h),a,atol=1e-9,rtol=0)
            np.testing.assert_allclose(regressor(q,v,a)@TRUTH,
                                       TRUTH[0]*a+TRUTH[1]*v+TRUTH[2]*np.sin(q),atol=1e-14)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identify',action='store_true')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DerivationChecks)
    if args.identify:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IdentificationChecks))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
