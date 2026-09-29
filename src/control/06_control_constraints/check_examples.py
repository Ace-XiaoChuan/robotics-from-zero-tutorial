"""第六章核对：默认仅标准库；--mujoco 加入实际闭环仿真。"""

import argparse
from dataclasses import replace
import math
import unittest

from run_examples import Case, Controller, GRAVITY, cases, peaks, preflight, quintic, run_case


class ConceptChecks(unittest.TestCase):
    def test_quintic_boundary_and_derivatives(self):
        self.assertEqual(quintic(0), (0, 0, 0))
        self.assertEqual(quintic(2), (.5, 0, 0))
        self.assertEqual(quintic(3), (.5, 0, 0))
        h = 1e-5
        for t in (.2, .7, 1.0, 1.8):
            q, v, a = quintic(t)
            before, after = quintic(t-h), quintic(t+h)
            self.assertAlmostEqual((after[0]-before[0])/(2*h), v, places=8)
            self.assertAlmostEqual((after[1]-before[1])/(2*h), a, places=8)

    def test_reference_peaks_and_time_scaling(self):
        vmax, amax = peaks(2, .5)
        self.assertAlmostEqual(vmax, .46875)
        self.assertAlmostEqual(amax, .7216878364870322)
        self.assertAlmostEqual(quintic(1)[1], vmax)
        self.assertAlmostEqual(quintic(2*(3-math.sqrt(3))/6)[2], amax)
        fast_v, fast_a = peaks(1, .5)
        self.assertAlmostEqual(fast_v, 2*vmax)
        self.assertAlmostEqual(fast_a, 4*amax)

    def test_static_pd_balance(self):
        low, high = 0., .5
        for _ in range(60):
            q = (low+high)/2
            if 12*(.5-q) > GRAVITY*math.sin(q):
                low = q
            else:
                high = q
        self.assertAlmostEqual(q, .337555470904, places=10)
        tau, _ = Controller(Case('pd', controller='pd')).command((.5, 0, 0), q, 0)
        self.assertAlmostEqual(tau, GRAVITY*math.sin(q))

    def test_feedforward_at_perfect_tracking(self):
        ref = quintic(.7)
        raw, applied = Controller(Case('ff')).command(ref, ref[0], ref[1])
        self.assertAlmostEqual(raw, .24*ref[2]+.2*ref[1]+5.886*math.sin(ref[0]))
        self.assertAlmostEqual(raw, applied)
        raw, _ = Controller(Case('g', controller='pd_g')).command((.5, 0, 0), .5, 0)
        self.assertAlmostEqual(raw, 5.886*math.sin(.5))

    def test_integral_freezes_and_unwinds(self):
        c = Controller(Case('pid', controller='pid'))
        for _ in range(100):
            raw, applied = c.command((1.2, 0, 0), 0, 0)
        self.assertEqual(c.integral, 0)
        self.assertEqual(applied, 4)
        c.integral = 1.
        raw, _ = c.command((0, 0, 0), .1, 0)
        self.assertGreater(raw, 4)
        self.assertLess(c.integral, 1)  # 反向误差仍能释放已经积累的积分。

    def test_target_checks_and_invalid_config(self):
        expected = {'reject_horizontal': 'rejected_joint_target',
                    'reject_torque': 'rejected_static_torque',
                    'reject_fast': 'rejected_reference_rate'}
        for c in cases():
            self.assertEqual(preflight(c), expected.get(c.name))
        for overrides in ({'physics_dt': 0}, {'goal': float('nan')},
                          {'control_dt': .003}, {'delay_samples': 1.5}):
            with self.assertRaises(ValueError):
                preflight(replace(Case('invalid'), **overrides))

    def test_endpoint_error_is_not_joint_error(self):
        def fk(q1, q2):
            return (.6*math.sin(q1)+.6*math.sin(q1+q2),
                    -.6*math.cos(q1)-.6*math.cos(q1+q2))
        desired, actual = fk(.3, -.2), fk(.29, -.19)
        distance = math.dist(desired, actual)
        self.assertAlmostEqual(distance, .00599997500003)
        self.assertAlmostEqual(.3-.2, .29-.19)  # 姿态角相同，位置仍不同。


class SimulationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {c.name: run_case(c) for c in cases()}

    def test_time_and_actual_actuator_limits(self):
        for name, (m, rows) in self.results.items():
            if name.startswith('reject_'):
                self.assertEqual(m['steps'], 0)
                self.assertEqual(rows, [])
                continue
            self.assertEqual(m['status'], 'completed')
            self.assertEqual(m['steps'], 3000)
            self.assertAlmostEqual(m['end_time_s'], 6.)
            self.assertLessEqual(m['max_abs_tau_nm'], 4.+1e-12)
            self.assertTrue(all(math.isfinite(r[k]) for r in rows for k in ('q','v','tau')))

    def test_pd_static_error_and_gravity_compensation(self):
        pd = self.results['step_pd'][0]
        self.assertAlmostEqual(pd['final_error_rad'], .162444529096, places=8)
        self.assertFalse(pd['terminal_criterion_met'])
        self.assertTrue(self.results['step_pd_g'][0]['terminal_criterion_met'])
        self.assertFalse(self.results['step_pid'][0]['terminal_criterion_met'])

    def test_smooth_feedforward_and_disturbance_recovery(self):
        base = self.results['smooth_ff_pd'][0]
        disturbed = self.results['disturbed_ff_pd'][0]
        self.assertLess(base['rmse_rad'], .001)
        self.assertGreater(disturbed['rmse_rad'], base['rmse_rad']*10)
        self.assertTrue(base['terminal_criterion_met'])
        self.assertTrue(disturbed['terminal_criterion_met'])
        disturbance_rows = [r for r in self.results['disturbed_ff_pd'][1] if r['external'] != 0]
        self.assertEqual(len(disturbance_rows), 500)

    def test_anti_windup_improves_recovery(self):
        naive, conditional = [self.results[n][0] for n in ('windup_naive', 'windup_conditional')]
        self.assertGreater(naive['max_abs_raw_nm'], 4)
        self.assertLess(conditional['max_abs_integral_rad_s'], naive['max_abs_integral_rad_s']/5)
        self.assertLess(conditional['last_second_rmse_rad'], naive['last_second_rmse_rad']/10)
        self.assertFalse(naive['terminal_criterion_met'])
        self.assertTrue(conditional['terminal_criterion_met'])

    def test_delay_and_noise(self):
        base, delayed, noisy = [self.results[n][0] for n in ('smooth_ff_pd','delayed_ff_pd','noisy_ff_pd')]
        self.assertGreater(delayed['rmse_rad'], base['rmse_rad']*10)
        self.assertFalse(delayed['terminal_criterion_met'])
        self.assertGreater(abs(delayed['final_speed_rad_s']), .02)
        self.assertGreater(noisy['rmse_rad'], base['rmse_rad'])
        self.assertTrue(noisy['terminal_criterion_met'])

    def test_fixed_seed_reproducibility(self):
        m, rows = run_case(Case('noisy_ff_pd', noise_q=.001, noise_v=.01))
        previous, previous_rows = self.results['noisy_ff_pd']
        self.assertEqual(m, previous)
        self.assertEqual(rows, previous_rows)

    def test_smaller_physics_step_same_control_period(self):
        finer, _ = run_case(Case('fine', physics_dt=.001))
        original = self.results['smooth_ff_pd'][0]
        self.assertTrue(finer['terminal_criterion_met'])
        self.assertLess(abs(finer['rmse_rad']-original['rmse_rad']), .0002)
        print('\n步长核对：dt=0.002 RMSE=', original['rmse_rad'],
              'dt=0.001 RMSE=', finer['rmse_rad'], '控制周期均为 0.01 s')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mujoco', action='store_true')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConceptChecks)
    if args.mujoco:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(SimulationChecks))
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not outcome.wasSuccessful())
