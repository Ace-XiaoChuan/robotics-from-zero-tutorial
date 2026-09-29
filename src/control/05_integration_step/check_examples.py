"""第五章数值积分核对。默认标准库；--mujoco 增加真实步进检查；--plot 导出图。"""

import argparse
import math
from pathlib import Path
import platform
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
Rod = runpy.run_path(str(HERE.parent / '02_single_joint_dynamics/check_examples.py'))['Rod']
ROD = Rod()
MODEL = HERE.parent / '04_forward_inverse_dynamics/single_rod.xml'


def euler_step(q, velocity, acceleration, h, semi_implicit=False):
    """只用于本章标量关节教学；acceleration 是步首重新计算的瞬时值。"""
    new_velocity = velocity + h * acceleration
    new_q = q + h * (new_velocity if semi_implicit else velocity)
    return new_q, new_velocity


def rk4_step(q, velocity, h):
    """标准四阶 Runge-Kutta，仅作本章无输入单杆的数值参照。"""
    def derivative(state):
        return state[1], ROD.acceleration(state[0], state[1], 0)
    def shift(state, k, factor):
        return tuple(x + factor * dx for x, dx in zip(state, k))
    state = q, velocity
    k1 = derivative(state)
    k2 = derivative(shift(state, k1, h / 2))
    k3 = derivative(shift(state, k2, h / 2))
    k4 = derivative(shift(state, k3, h))
    return tuple(state[i] + h * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) / 6 for i in range(2))


def pendulum_run(h, duration=.2, method='rk4'):
    steps = round(duration / h)
    if not math.isclose(steps * h, duration, abs_tol=1e-12):
        raise ValueError('本章比较要求步数乘步长等于相同仿真时长')
    q, velocity = math.pi / 6, 0.0
    for _ in range(steps):
        if method == 'rk4':
            q, velocity = rk4_step(q, velocity, h)
        elif method in ('explicit', 'semi'):
            acceleration = ROD.acceleration(q, velocity, 0)
            q, velocity = euler_step(q, velocity, acceleration, h, method == 'semi')
        else:
            raise ValueError(method)
    return q, velocity


def constant_acceleration(h, duration=1.0, semi=False):
    """q0=v0=0、a=2 rad/s²；独立算例，非默认重力单杆。"""
    q = velocity = 0.0
    history = [(0.0, q, velocity)]
    for k in range(round(duration / h)):
        q, velocity = euler_step(q, velocity, 2.0, h, semi)
        history.append(((k + 1) * h, q, velocity))
    return history


def make_plot():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    times = [i / 100 for i in range(101)]
    fig, ax = plt.subplots(figsize=(7.2, 4.1), layout='constrained')
    ax.plot(times, [t*t for t in times], color='#202f3e', label='Exact: q = t^2', linewidth=2)
    for semi, color, label in [(False, '#3579b1', 'Explicit Euler'), (True, '#c4662a', 'Semi-implicit Euler')]:
        rows = constant_acceleration(.1, semi=semi)
        ax.plot([r[0] for r in rows], [r[1] for r in rows], 'o--', color=color,
                label=label, markersize=4, linewidth=1.4)
    ax.set(xlabel='Simulation time (s)', ylabel='Joint angle q (rad)',
           title='Same acceleration, different integration approximations\na = 2 rad/s², q(0) = v(0) = 0, step = 0.1 s')
    ax.grid(alpha=.2)
    ax.legend()
    return fig


class NumericalChecks(unittest.TestCase):
    def test_constant_acceleration_refinement(self):
        for h, expected_explicit, expected_semi in [(.1, .9, 1.1), (.05, .95, 1.05), (.01, .99, 1.01)]:
            for semi, expected in [(False, expected_explicit), (True, expected_semi)]:
                _, q, velocity = constant_acceleration(h, semi=semi)[-1]
                self.assertAlmostEqual(q, expected)
                self.assertAlmostEqual(velocity, 2)
                self.assertAlmostEqual(abs(q - 1), h)

    def test_update_order_and_fresh_acceleration(self):
        self.assertEqual(euler_step(0, 0, 2, .1), (0, .2))
        semi_q, semi_v = euler_step(0, 0, 2, .1, True)
        self.assertAlmostEqual(semi_q, .02)
        self.assertAlmostEqual(semi_v, .2)
        q, v = math.pi/6, 0
        a0 = ROD.acceleration(q, v, 0)
        q, v = euler_step(q, v, a0, .01, True)
        self.assertAlmostEqual(a0, -12.2625)
        self.assertAlmostEqual(q, math.pi/6 - .00122625)
        self.assertGreater(abs(ROD.acceleration(q, v, 0) - a0), .01)

    def test_pure_damping_stability_and_accuracy(self):
        # I=.24、b=24，g=0、无驱动，dv/dt=-100v，v0=1。
        factor = 1 - 100 * .03
        self.assertEqual(factor, -2)
        self.assertEqual([factor**i for i in range(4)], [1, -2, 4, -8])
        exact = math.exp(-3)
        implicit = 1 / (1 + 100 * .03)
        self.assertAlmostEqual(exact, .049787068367863944)
        self.assertEqual(implicit, .25)
        self.assertLess(abs(implicit - exact), abs(factor - exact))
        self.assertGreater(abs(implicit - exact), .1)  # 稳定不等于足够精确。

    def test_reference_convergence(self):
        coarse, fine = pendulum_run(.0001), pendulum_run(.00005)
        for a, b in zip(coarse, fine):
            self.assertAlmostEqual(a, b, delta=1e-10)

    def test_single_rod_step_refinement(self):
        reference = pendulum_run(.00005)
        for method in ('explicit', 'semi'):
            errors = [abs(pendulum_run(h, method=method)[0] - reference[0]) for h in (.02, .01, .002)]
            self.assertGreater(errors[0], errors[1])
            self.assertGreater(errors[1], errors[2])


class MujocoChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mujoco
        cls.mj = mujoco
        print(f'Environment: Python {platform.python_version()}, MuJoCo {mujoco.__version__}', flush=True)

    def setup_model(self, h=.002):
        model = self.mj.MjModel.from_xml_path(str(MODEL))
        model.opt.timestep = h
        model.opt.integrator = self.mj.mjtIntegrator.mjINT_EULER
        data = self.mj.MjData(model)
        data.joint('hinge').qpos[0] = math.pi/6
        data.actuator('motor').ctrl[0] = 0
        return model, data

    def test_forward_does_not_step_but_step_does(self):
        model, data = self.setup_model()
        initial = data.qpos.copy(), data.qvel.copy()
        for _ in range(3):
            self.mj.mj_forward(model, data)
        self.assertEqual(data.time, 0)
        self.assertEqual(data.qpos.tolist(), initial[0].tolist())
        self.assertEqual(data.qvel.tolist(), initial[1].tolist())
        self.mj.mj_step(model, data)
        self.assertAlmostEqual(data.time, .002)
        self.assertLess(data.qpos[0], initial[0][0])
        self.assertLess(data.qvel[0], 0)

    def test_euler_joint_damping_update(self):
        model, data = self.setup_model()
        self.mj.mj_step(model, data)
        # MuJoCo Euler 对关节阻尼作隐式处理，重力取步首值。
        expected_velocity = (-.002 * 2.943) / (.24 + .002 * .2)
        expected_q = math.pi/6 + .002 * expected_velocity
        self.assertAlmostEqual(data.qvel[0], expected_velocity, delta=1e-12)
        self.assertAlmostEqual(data.qpos[0], expected_q, delta=1e-12)
        print(f'one step: t={data.time:.6f}, q={data.qpos[0]:.12f}, v={data.qvel[0]:.12f}', flush=True)

    def test_post_step_derived_values_and_logging(self):
        model, data = self.setup_model()
        self.mj.mj_step(model, data)
        before = data.qpos.copy(), data.qvel.copy(), data.time
        self.assertAlmostEqual(data.qacc[0], -12.2625)
        self.mj.mj_forward(model, data)
        self.assertEqual(data.qpos.tolist(), before[0].tolist())
        self.assertEqual(data.qvel.tolist(), before[1].tolist())
        self.assertEqual(data.time, before[2])
        self.assertAlmostEqual(data.qacc[0], ROD.acceleration(data.qpos[0], data.qvel[0], 0), delta=1e-10)
        quaternion = data.body('rod').xquat
        self.assertAlmostEqual(quaternion[0], math.cos(data.qpos[0]/2), delta=1e-12)
        self.assertAlmostEqual(quaternion[3], math.sin(data.qpos[0]/2), delta=1e-12)
        record = data.qpos.copy()
        self.mj.mj_step(model, data)
        self.assertEqual(record.tolist(), before[0].tolist())
        self.assertNotEqual(data.qpos.tolist(), record.tolist())

    def test_mujoco_refinement_over_same_duration(self):
        reference = pendulum_run(.00005)
        errors = []
        for h in (.02, .01, .002):
            model, data = self.setup_model(h)
            for _ in range(round(.2/h)):
                self.mj.mj_step(model, data)
            self.assertAlmostEqual(data.time, .2, delta=1e-12)
            error = abs(data.qpos[0] - reference[0])
            errors.append(error)
            print(f'h={h:.3f}, q={data.qpos[0]:.12f}, v={data.qvel[0]:.12f}, q_error={error:.12f}', flush=True)
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        # 同一 .002 s 设置再从干净初态跑一遍，结果可重复。
        model, repeat = self.setup_model()
        for _ in range(100):
            self.mj.mj_step(model, repeat)
        self.assertAlmostEqual(repeat.qpos[0], data.qpos[0], delta=1e-12)

    def test_implicit_joint_damping_is_not_explicit_euler(self):
        model, data = self.setup_model(.03)
        model.opt.gravity[:] = 0
        model.dof_damping[0] = 24
        data.qpos[0] = 0
        data.qvel[0] = 1
        self.mj.mj_step(model, data)
        self.assertAlmostEqual(data.qvel[0], .25, delta=1e-12)
        self.assertAlmostEqual(data.qpos[0], .0075, delta=1e-12)
        self.assertGreater(data.qvel[0], 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mujoco', action='store_true')
    parser.add_argument('--plot', action='store_true', help='需要 matplotlib；生成正文引用的积分对比图')
    args = parser.parse_args()
    print('RK4 reference (.00005 s):', pendulum_run(.00005), flush=True)
    suite = unittest.TestLoader().loadTestsFromTestCase(NumericalChecks)
    if args.mujoco:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MujocoChecks))
    else:
        print('仅检查教学积分；未运行 MuJoCo API。', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful() and args.plot:
        make_plot().savefig(HERE / 'integration_comparison.svg')
    sys.exit(0 if result.wasSuccessful() else 1)
