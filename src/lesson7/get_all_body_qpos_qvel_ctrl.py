import mujoco
import numpy as np
import sys
from pathlib import Path

project_root = Path("~/litchi_tutorial/mujoco-learning").expanduser()
sys.path.append(str(project_root))

from src import mujoco_viewer


class Test(mujoco_viewer.CustomViewer):
    def __init__(self, path):
        super().__init__(path, 3, azimuth=-45, elevation=-30)
        self.path = path

    def runBefore(self):
        for joint_id in range(self.model.njnt):
            joint_name = mujoco.mj_id2name(
                self.model, mujoco.mjtObj.mjOBJ_JOINT, joint_id
            )
            qpos = self.data.joint(joint_name).qpos
            qvel = self.data.joint(joint_name).qvel
            print(f"joint:{joint_id}")
            print(qpos)
            print(qvel)
        for actuator_id in range(self.model.nu):
            actuator_name = mujoco.mj_id2name(
                self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_id
            )
            ctrl = self.data.actuator(actuator_name).ctrl
            print(f"actuator_id:{actuator_id}")
            print(ctrl)


test = Test("/home/ace/mujoco_models/mujoco_menagerie/franka_emika_panda/scene.xml")
test.run_loop()
