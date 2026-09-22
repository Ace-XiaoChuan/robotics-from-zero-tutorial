"""Headless S3 checks; the bundled model needs no external assets."""

from pathlib import Path
import json
import platform

import mujoco
import numpy as np


MODEL = Path(__file__).resolve().parent / "models" / "pendulum.xml"


def reset(model, data):
    mujoco.mj_resetData(model, data)
    data.joint("hinge").qpos[0] = 0.5
    mujoco.mj_forward(model, data)


def rollout(model, data):
    reset(model, data)
    rows = []
    for _ in range(100):
        data.actuator("hinge_motor").ctrl[0] = 0.2
        mujoco.mj_step(model, data)
        # Refresh derived positions at the newly integrated qpos before logging.
        mujoco.mj_forward(model, data)
        rows.append(np.concatenate(([data.time], data.qpos.copy(), data.qvel.copy())))
    return np.asarray(rows)


def main():
    model = mujoco.MjModel.from_xml_path(str(MODEL))
    data = mujoco.MjData(model)
    assert (model.nq, model.nv, model.nu) == (8, 7, 1)
    reset(model, data)
    expected = [-0.5 * np.sin(0.5), 0, 1 - 0.5 * np.cos(0.5)]
    tip_error = float(np.max(np.abs(data.site("tip").xpos - expected)))
    assert tip_error < 1e-12
    assert data.time == 0
    data.actuator("hinge_motor").ctrl[0] = 3
    mujoco.mj_forward(model, data)
    force = float(data.actuator_force[0])
    assert abs(force - 2) < 1e-12
    assert data.ctrl[0] == 3  # Clamping applies to force calculation, not this array.
    first = rollout(model, data)
    second = rollout(model, data)
    repeat_error = float(np.max(np.abs(first - second)))
    assert np.isfinite(first).all()
    assert repeat_error < 1e-12
    assert abs(data.time - 0.2) < 1e-12
    assert abs(data.joint("hinge").qpos[0] - 0.5) > 1e-5
    reset(model, data)
    assert data.time == 0 and np.all(data.qvel == 0) and np.all(data.ctrl == 0)
    changed = mujoco.MjModel.from_xml_string(
        MODEL.read_text().replace('mass="1"', 'mass="2"')
    )
    changed_data = mujoco.MjData(changed)
    reset(changed, changed_data)
    np.testing.assert_allclose(changed_data.site("tip").xpos, expected, atol=1e-12)
    assert changed.body("rod").mass[0] == 2 * model.body("rod").mass[0]
    np.testing.assert_allclose(changed.body("rod").inertia, 2 * model.body("rod").inertia)
    for kind, count in (("joint", model.njnt), ("actuator", model.nu),
                        ("body", model.nbody), ("site", model.nsite)):
        for index in range(count):
            item = getattr(model, kind)(index)
            record = {"kind": kind, "id": index, "name": item.name}
            if kind == "joint":
                record.update(qpos_adr=int(model.jnt_qposadr[index]),
                              dof_adr=int(model.jnt_dofadr[index]))
            print(json.dumps(record))
    print(json.dumps({"python": platform.python_version(), "mujoco": mujoco.__version__,
                      "numpy": np.__version__, "nq_nv_nu": [model.nq, model.nv, model.nu],
                      "tip_error_m": tip_error, "clamped_motor_force_Nm": force,
                      "repeat_max_abs_error": repeat_error,
                      "final_time_s": float(first[-1, 0]),
                      "final_hinge_rad": float(first[-1, 1]),
                      "mass_change_geometry_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
