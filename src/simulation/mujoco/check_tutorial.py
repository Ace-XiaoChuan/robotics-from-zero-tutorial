"""核对教程中的坐标、参数、接触、传感器与机械臂闭环结果；无窗口。"""

import argparse
import json
from pathlib import Path
import platform
import unittest

import mujoco
import numpy as np

from arm_walkthrough import MODEL, GOAL, metrics, run, tip_from_angles


MODELS = Path(__file__).resolve().parent / "models"
RESULTS = {}


def load(name):
    model = mujoco.MjModel.from_xml_path(str(MODELS / name))
    return model, mujoco.MjData(model)


def contact_run(friction=0.6, collide=True):
    model, data = load("contact_box.xml")
    # 两个 geom 的滑动摩擦一起修改，避免参数合成掩盖对照条件。
    model.geom_friction[:, 0] = friction
    if friction == 0:
        model.geom_condim[:] = 1  # 无摩擦对照只保留法向约束，避免退化摩擦锥
    if not collide:
        model.geom_contype[:] = 0
        model.geom_conaffinity[:] = 0
    for _ in range(500):  # 先静置 1 s
        mujoco.mj_step(model, data)
    mujoco.mj_forward(model, data)
    rest_height = float(data.joint("box_free").qpos[2])
    normal_force = 0.0
    wrench = np.zeros(6)
    for index in range(data.ncon):
        mujoco.mj_contactForce(model, data, index, wrench)
        normal_force += wrench[0]  # 此场景全是水平地面，接触法向沿竖直方向
    contacts = int(data.ncon)
    start_x = float(data.joint("box_free").qpos[0])
    data.joint("box_free").qvel[0] = 1.0  # 世界系 +x，m/s
    for _ in range(250):  # 再观察 0.5 s
        mujoco.mj_step(model, data)
    mujoco.mj_forward(model, data)
    return {"rest_center_z_m": rest_height, "rest_contacts": contacts,
            "rest_normal_force_N": float(normal_force),
            "slide_distance_m": float(data.joint("box_free").qpos[0] - start_x),
            "final_vx_m_s": float(data.joint("box_free").qvel[0])}


class TutorialChecks(unittest.TestCase):
    def test_compilation_defaults_and_independent_data(self):
        model, a = load("arm_scene.xml")
        b = mujoco.MjData(model)
        self.assertEqual((model.nq, model.nv, model.nu), (2, 2, 2))
        np.testing.assert_allclose(model.dof_damping, [0.1, 0.1])
        self.assertEqual(model.nsensor, 5)
        self.assertEqual(model.nsensordata, 7)
        a.joint("shoulder").qpos[0] = 0.5
        self.assertEqual(b.joint("shoulder").qpos[0], 0)
        # 两份 data 独立，model 参数仍共享。
        self.assertEqual(model.opt.timestep, 0.002)

    def test_geometry_stale_then_refreshed_and_sensors(self):
        model, data = load("arm_scene.xml")
        mujoco.mj_forward(model, data)
        old = data.site("tip").xpos.copy()
        for name, q in zip(("shoulder", "elbow"), GOAL):
            data.joint(name).qpos[0] = q
        np.testing.assert_array_equal(data.site("tip").xpos, old)
        mujoco.mj_forward(model, data)
        np.testing.assert_allclose(data.site("tip").xpos, tip_from_angles(GOAL), atol=1e-12)
        np.testing.assert_allclose(data.sensor("tip_position").data, data.site("tip").xpos)
        self.assertEqual(data.sensor("shoulder_position").data[0], GOAL[0])
        self.assertEqual(data.time, 0)
        RESULTS["arm_geometry"] = {"zero_tip_world_m": old.tolist(),
                                   "goal_tip_world_m": data.site("tip").xpos.tolist()}

    def test_motor_transmission_and_two_limits(self):
        source = (MODELS / "pendulum.xml").read_text()
        model = mujoco.MjModel.from_xml_string(source.replace('gear="1"', 'gear="2"'))
        data = mujoco.MjData(model)
        data.ctrl[0] = 3
        mujoco.mj_forward(model, data)
        self.assertEqual(data.ctrl[0], 3)
        self.assertAlmostEqual(data.actuator_force[0], 2)
        self.assertAlmostEqual(data.joint("hinge").qfrc_actuator[0], 4)
        model, data = load("arm_scene.xml")
        data.actuator("shoulder_servo").ctrl[0] = 0.5
        mujoco.mj_forward(model, data)
        self.assertAlmostEqual(data.actuator("shoulder_servo").force[0], 8)
        RESULTS["actuation"] = {"gear2_raw_ctrl": 3, "clamped_actuator_force": 2,
                                "gear2_joint_torque_Nm": 4, "arm_servo_clamped_torque_Nm": 8}

    def test_mass_change_and_gravity(self):
        source = (MODELS / "pendulum.xml").read_text()
        acceleration, gravity_acceleration = [], []
        inertia = []
        for mass in (1, 2):
            model = mujoco.MjModel.from_xml_string(source.replace('mass="1"', f'mass="{mass}"'))
            data = mujoco.MjData(model)
            data.joint("hinge").qpos[0] = 0.5
            mujoco.mj_forward(model, data)
            gravity_acceleration.append(float(data.joint("hinge").qacc[0]))
            model.opt.gravity[:] = 0  # 仅比较同一输入下的惯性影响
            data.ctrl[0] = 0.2
            mujoco.mj_forward(model, data)
            acceleration.append(float(data.joint("hinge").qacc[0]))
            inertia.append(model.body("rod").inertia.copy())
            np.testing.assert_allclose(data.site("tip").xpos,
                                       [-0.5*np.sin(0.5), 0, 1-0.5*np.cos(0.5)], atol=1e-12)
        np.testing.assert_allclose(inertia[1], 2*inertia[0])
        self.assertAlmostEqual(acceleration[0], 2*acceleration[1], places=12)
        self.assertAlmostEqual(gravity_acceleration[0], gravity_acceleration[1], places=12)
        RESULTS["physical_parameters"] = {"mass_kg": [1, 2],
            "zero_gravity_motor_qacc_rad_s2": acceleration,
            "gravity_only_qacc_rad_s2": gravity_acceleration}

    def test_contact_support_and_collision_filter(self):
        supported, falling = contact_run(), contact_run(collide=False)
        self.assertGreater(supported["rest_contacts"], 0)
        self.assertAlmostEqual(supported["rest_normal_force_N"], 0.2*9.81, delta=0.01)
        self.assertAlmostEqual(supported["rest_center_z_m"], 0.05, delta=0.001)
        self.assertEqual(falling["rest_contacts"], 0)
        self.assertLess(falling["rest_center_z_m"], -4)
        RESULTS["supported_box"] = supported
        RESULTS["collision_disabled_box"] = falling

    def test_friction_changes_actual_sliding(self):
        frictionless, frictional = contact_run(friction=0), contact_run(friction=0.6)
        self.assertAlmostEqual(frictionless["rest_center_z_m"], 0.05, delta=0.001)
        self.assertGreater(frictionless["rest_contacts"], 0)
        self.assertAlmostEqual(frictionless["rest_normal_force_N"], 1.962, delta=0.01)
        self.assertAlmostEqual(frictionless["slide_distance_m"], 0.5, delta=1e-8)
        self.assertLess(frictional["slide_distance_m"], 0.2)
        self.assertLess(abs(frictional["final_vx_m_s"]), 0.01)
        RESULTS["frictionless_box"] = frictionless
        RESULTS["frictional_box"] = frictional

    def test_state_snapshot_and_keyframe(self):
        model, data = load("arm_scene.xml")
        data.ctrl[:] = GOAL
        for _ in range(50):
            mujoco.mj_step(model, data)
        saved_angles = data.qpos.copy()
        mask = mujoco.mjtState.mjSTATE_INTEGRATION
        state = np.empty(mujoco.mj_stateSize(model, mask))
        mujoco.mj_getState(model, data, state, mask)
        for _ in range(20):
            mujoco.mj_step(model, data)
        expected = np.r_[data.time, data.qpos.copy(), data.qvel.copy()]
        mujoco.mj_setState(model, data, state, mask)
        mujoco.mj_forward(model, data)
        for _ in range(20):
            mujoco.mj_step(model, data)
        np.testing.assert_allclose(np.r_[data.time, data.qpos, data.qvel], expected, atol=1e-12, rtol=0)
        self.assertFalse(np.shares_memory(saved_angles, data.qpos))
        mujoco.mj_resetDataKeyframe(model, data, model.key("home").id)
        self.assertEqual(data.time, 0)
        np.testing.assert_array_equal(data.qpos, [0, 0])
        np.testing.assert_array_equal(data.qvel, [0, 0])
        np.testing.assert_array_equal(data.ctrl, [0, 0])

    def test_arm_rollout_timing_tracking_saturation_and_repeat(self):
        model = mujoco.MjModel.from_xml_path(str(MODEL))
        data = mujoco.MjData(model)
        first, second = run(model, data), run(model, data)
        self.assertEqual(first.shape, (1500, 10))
        self.assertTrue(np.isfinite(first).all())
        np.testing.assert_allclose(first, second, atol=1e-12, rtol=0)
        self.assertAlmostEqual(first[0, 0], 0.002)
        self.assertAlmostEqual(first[-1, 0], 3)
        np.testing.assert_allclose(first[0:5, 1:3], 0, atol=0)
        np.testing.assert_allclose(first[5:10, 1:3], np.tile(first[5, 1:3], (5, 1)))
        self.assertLess(np.max(np.abs(first[-1, 3:5] - GOAL)), 1e-3)
        normal = metrics(first)
        self.assertLess(normal["max_fk_error_m"], 1e-12)
        # 同样的目标与时长，仅降低可用驱动力矩，检查实际运动差异。
        model.actuator_forcerange[:] = [-0.01, 0.01]
        weak = metrics(run(model, data))
        self.assertGreater(np.max(np.abs(weak["final_goal_error_rad"])), 0.1)
        RESULTS["arm_rollout"] = normal
        RESULTS["arm_torque_limited"] = weak
        RESULTS["repeat_max_abs_difference"] = float(np.max(np.abs(first-second)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="可选，将数值结果保存为 JSON")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TutorialChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"python": platform.python_version(), "mujoco": mujoco.__version__,
              "numpy": np.__version__, "checks": result.testsRun,
              "passed": result.wasSuccessful(), "results": RESULTS}
    if args.output and result.wasSuccessful():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
