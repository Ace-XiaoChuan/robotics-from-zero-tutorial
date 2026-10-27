"""两关节机械臂：仿真时间驱动的位置目标、物理步进和步后记录。"""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import platform
import time

import mujoco
import numpy as np


MODEL = Path(__file__).resolve().parent / "models" / "arm_scene.xml"
JOINTS = ("shoulder", "elbow")
ACTUATORS = ("shoulder_servo", "elbow_servo")
GOAL = np.array([0.5, -0.8])  # rad，顺序为 shoulder、elbow
CONTROL_STRIDE = 5  # 5 × 0.002 s = 0.01 s
STEPS = 1500  # 3 s，前 1 s 改变目标，随后保持


def target(sim_time):
    """1 s 内以五次曲线从零位过渡到 GOAL，之后保持。"""
    s = np.clip(sim_time / 1.0, 0.0, 1.0)
    return (10 * s**3 - 15 * s**4 + 6 * s**5) * GOAL


def tip_from_angles(q):
    """世界系 FK，长度 m；两个关节均绕 +z，基座高 0.3 m。"""
    a, b = q
    return np.array([0.4 * np.cos(a) + 0.3 * np.cos(a + b),
                     0.4 * np.sin(a) + 0.3 * np.sin(a + b), 0.3])


def reset(model, data):
    mujoco.mj_resetDataKeyframe(model, data, model.key("home").id)
    mujoco.mj_forward(model, data)


def run(model, data, viewer=None):
    """逐物理步记录：[步后时间、刚作用的目标2、实际角2、实际速度2、tip世界坐标3]。"""
    with viewer.lock() if viewer is not None else nullcontext():
        reset(model, data)
    rows = []
    command = np.zeros(2)
    wall_start = time.monotonic()
    for step in range(STEPS):
        if viewer is not None and not viewer.is_running():
            break
        with viewer.lock() if viewer is not None else nullcontext():
            if step % CONTROL_STRIDE == 0:
                command = target(data.time)
                for name, value in zip(ACTUATORS, command):
                    data.actuator(name).ctrl[0] = value
            mujoco.mj_step(model, data)
            # 对齐新构型的 site 与传感器；这次 forward 不推进时间。
            mujoco.mj_forward(model, data)
            q = [data.joint(name).qpos[0] for name in JOINTS]
            v = [data.joint(name).qvel[0] for name in JOINTS]
            rows.append(np.r_[data.time, command, q, v, data.site("tip").xpos.copy()])
        if viewer is not None:
            if (step + 1) % 20 == 0:
                viewer.sync()
            time.sleep(max(0.0, wall_start + float(data.time) - time.monotonic()))
    return np.asarray(rows, dtype=float).reshape(-1, 10)


def metrics(rows):
    if len(rows) == 0:
        return {"recorded_steps": 0, "completed": False}
    final = rows[-1]
    return {"python": platform.python_version(), "mujoco": mujoco.__version__,
            "numpy": np.__version__, "recorded_steps": len(rows),
            "completed": len(rows) == STEPS,
            "time_s": float(final[0]), "joint_order": list(JOINTS),
            "final_command_rad": final[1:3].tolist(),
            "final_q_rad": final[3:5].tolist(),
            "final_qvel_rad_s": final[5:7].tolist(),
            "final_goal_error_rad": (GOAL - final[3:5]).tolist(),
            "final_tip_world_m": final[7:10].tolist(),
            "target_tip_world_m": tip_from_angles(GOAL).tolist(),
            "peak_tracking_error_rad": np.max(np.abs(rows[:, 1:3] - rows[:, 3:5]), axis=0).tolist(),
            "max_fk_error_m": float(np.max(np.abs(
                np.array([tip_from_angles(q) for q in rows[:, 3:5]]) - rows[:, 7:10])))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--viewer", action="store_true", help="打开窗口，以接近实时的速度运行")
    parser.add_argument("--output", type=Path, help="可选 CSV 路径，建议放在 /tmp 或仓库外")
    args = parser.parse_args()
    model = mujoco.MjModel.from_xml_path(str(MODEL))
    data = mujoco.MjData(model)
    if args.viewer:
        from mujoco import viewer as mj_viewer

        with mj_viewer.launch_passive(model, data) as viewer:
            with viewer.lock():
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
                viewer.cam.fixedcamid = model.camera("overview").id
            rows = run(model, data, viewer)
    else:
        rows = run(model, data)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(args.output, rows, delimiter=",", comments="",
                   header="time_s,command_shoulder_rad,command_elbow_rad,shoulder_rad,elbow_rad,shoulder_rad_s,elbow_rad_s,tip_x_m,tip_y_m,tip_z_m")
    print(json.dumps(metrics(rows), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
