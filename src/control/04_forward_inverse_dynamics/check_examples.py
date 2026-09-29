"""第四章解析与可选 MuJoCo 瞬时核对；--mujoco 启用实际 API 检查。"""

import argparse
import math
from pathlib import Path
import platform
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
# 复用已核对的教学模型，不复制公式；__main__ 入口不会被执行。
Rod = runpy.run_path(str(HERE.parent / '02_single_joint_dynamics/check_examples.py'))['Rod']
TWO = runpy.run_path(str(HERE.parent / '03_multi_joint_dynamics/check_examples.py'))


class AnalyticChecks(unittest.TestCase):
    def test_single_forward_inverse(self):
        rod = Rod()
        torque = rod.required_motor(math.pi / 6, 1, 2)
        self.assertAlmostEqual(torque, 3.623)
        self.assertAlmostEqual(rod.acceleration(math.pi / 6, 1, torque), 2)

    def test_two_joint_forward_inverse(self):
        q, velocity = [0, math.pi / 2], [1, 2]
        torque = TWO['required_motor'](q, velocity, [1, 0])
        for actual, expected in zip(torque, [4.406, 6.886]):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(TWO['forward'](q, velocity, torque), [1, 0]):
            self.assertAlmostEqual(actual, expected)

    def test_payload_mismatch(self):
        torque = Rod().required_motor(math.pi / 6, 1, 2)
        self.assertAlmostEqual(Rod(payload=1).acceleration(math.pi / 6, 1, torque), -4.105)

    def test_external_force_allocation(self):
        rod = Rod()
        motor = rod.required_motor(math.pi / 6, 1, 2, .48)
        self.assertAlmostEqual(motor, 3.143)
        self.assertAlmostEqual(rod.acceleration(math.pi / 6, 1, motor, .48), 2)
        self.assertAlmostEqual(rod.acceleration(math.pi / 6, 1, 3.623, .48), 4)

    def test_velocity_mismatch(self):
        self.assertAlmostEqual(Rod().acceleration(math.pi / 6, -1, 3.623), 11 / 3)

    def test_joint_order_mismatch(self):
        result = TWO['forward']([0, math.pi / 2], [1, 2], [6.886, 4.406])
        self.assertGreater(max(abs(a - b) for a, b in zip(result, [1, 0])), 1)


class MujocoChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mujoco
        cls.mj = mujoco
        print(f'API environment: Python {platform.python_version()}, MuJoCo {mujoco.__version__}', flush=True)

    def setUp(self):
        self.model = self.mj.MjModel.from_xml_path(str(HERE / 'single_rod.xml'))
        self.assertEqual((self.model.nq, self.model.nv, self.model.nu), (1, 1, 1))

    def state(self, q=math.pi / 6, velocity=1.0):
        data = self.mj.MjData(self.model)
        data.joint('hinge').qpos[0] = q
        data.joint('hinge').qvel[0] = velocity
        return data

    def assertClose(self, actual, expected):
        self.assertAlmostEqual(float(actual), expected, delta=1e-9)

    def test_inverse_forward_without_advancing_time(self):
        inverse_data = self.state()
        inverse_data.joint('hinge').qacc[0] = 2
        snapshot = (inverse_data.qpos.copy(), inverse_data.qvel.copy(), inverse_data.time)
        self.mj.mj_inverse(self.model, inverse_data)
        required = inverse_data.qfrc_inverse.copy()
        self.assertClose(required[0], 3.623)
        forward_data = self.state()
        forward_data.actuator('motor').ctrl[0] = required[0]
        self.mj.mj_forward(self.model, forward_data)
        self.assertClose(forward_data.qacc[0], 2)
        for data in [inverse_data, forward_data]:
            self.assertClose(data.time, snapshot[2])
            self.assertClose(data.qpos[0], snapshot[0][0])
            self.assertClose(data.qvel[0], snapshot[1][0])
            self.assertEqual(data.nefc, 0)
        print(f'round trip: inverse={required.tolist()}, forward={forward_data.qacc.tolist()}, time={forward_data.time}', flush=True)

    def test_passive_damping_and_bias_are_already_included(self):
        data = self.state()
        data.qacc[0] = 2
        self.mj.mj_inverse(self.model, data)
        self.assertClose(data.qfrc_bias[0], 2.943)
        self.assertClose(data.qfrc_passive[0], -.2)
        self.assertClose(data.qfrc_inverse[0], .24 * 2 + 2.943 - (-.2))

    def test_external_force_is_part_of_total_required_force(self):
        data = self.state()
        data.qacc[0] = 2
        data.qfrc_applied[0] = .48
        self.mj.mj_inverse(self.model, data)
        self.assertClose(data.qfrc_inverse[0], 3.623)  # 不是已减去外力的电机需求。
        for motor, expected_acc in [(3.143, 2), (3.623, 4)]:
            forward_data = self.state()
            forward_data.qfrc_applied[0] = .48
            forward_data.actuator('motor').ctrl[0] = motor
            self.mj.mj_forward(self.model, forward_data)
            self.assertClose(forward_data.qacc[0], expected_acc)

    def test_inverse_does_not_enforce_actuator_limit(self):
        inverse_data = self.state(math.pi / 2, 0)
        inverse_data.qacc[0] = 0
        self.mj.mj_inverse(self.model, inverse_data)
        self.assertClose(inverse_data.qfrc_inverse[0], 5.886)
        data = self.state(math.pi / 2, 0)
        data.actuator('motor').ctrl[0] = inverse_data.qfrc_inverse[0]
        self.mj.mj_forward(self.model, data)
        self.assertClose(data.qfrc_actuator[0], 4)
        self.assertClose(data.qacc[0], -7.858333333333333)
        print(f'limit: required={inverse_data.qfrc_inverse.tolist()}, actual={data.qfrc_actuator.tolist()}, acceleration={data.qacc.tolist()}', flush=True)

    def test_gear_requires_command_mapping(self):
        xml = (HERE / 'single_rod.xml').read_text()
        assert xml.count('gear="1"') == 1
        self.model = self.mj.MjModel.from_xml_string(xml.replace('gear="1"', 'gear="2"'))
        data = self.state()
        data.qacc[0] = 2
        self.mj.mj_inverse(self.model, data)
        self.assertClose(data.qfrc_inverse[0], 3.623)
        forward_data = self.state()
        forward_data.actuator('motor').ctrl[0] = data.qfrc_inverse[0] / 2
        self.mj.mj_forward(self.model, forward_data)
        self.assertClose(forward_data.ctrl[0], 1.8115)
        self.assertClose(forward_data.qfrc_actuator[0], 3.623)
        self.assertClose(forward_data.qacc[0], 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mujoco', action='store_true', help='额外核对实际 MuJoCo API；需要已安装 mujoco')
    args = parser.parse_args()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AnalyticChecks)
    if args.mujoco:
        suite.addTests(loader.loadTestsFromTestCase(MujocoChecks))
    else:
        print('仅运行解析核对；添加 --mujoco 可核对实际 API。', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
