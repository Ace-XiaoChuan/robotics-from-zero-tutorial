"""
机械臂在 MuJoCo 中运动，同时采集一段 episode 数据。

每一帧保存的 sample 结构：
{
    "rgb": image,
    "qpos": qpos,
    "qvel": qvel,
    "eef_pos": eef_pos,
    "eef_quat": eef_quat,
    "object_pos": object_pos,
    "object_quat": object_quat,
    "action": action,
    "timestamp": t,
}
"""

import sys
from datetime import datetime
from pathlib import Path

import cv2
import mujoco
import numpy as np


PROJECT_ROOT = Path("~/litchi_tutorial/mujoco-learning").expanduser()
MODEL_DIR = PROJECT_ROOT / "model/franka_emika_panda"
DEMO_DIR = Path(__file__).resolve().parent
SHOW_CAMERA_IMAGE = True
PRINT_EVERY_N_FRAMES = 50

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.mujoco_viewer as mujoco_viewer


class SCTPD(mujoco_viewer.CustomViewer):
    """Panda 机械臂仿真环境：运动机械臂并采集相机、关节、末端和物体位姿数据。"""

    def __init__(self, path: str):
        super().__init__(path, 3, azimuth=-45, elevation=-30)
        self.path = path

    @staticmethod
    def ensure_rgb_image(image: np.ndarray) -> np.ndarray:
        """
        确保输入图像是连续内存的 RGB 三通道格式。

        如果图像带 alpha 通道，会去掉 alpha；如果通道数不是 3 或 4，会报错。
        """
        if image.ndim != 3:
            raise ValueError(f"期望输入为 H x W x C 图像，但实际 shape 为: {image.shape}")

        if image.shape[-1] == 4:
            image = image[..., :3]

        if image.shape[-1] != 3:
            raise ValueError(f"期望图像通道数为 3 或 4，但实际 shape 为: {image.shape}")

        return np.ascontiguousarray(image)

    def get_desired_position(self, t: float) -> np.ndarray:
        """根据仿真时间 t，在 q_start 和 q_goal 之间做线性插值。"""
        alpha = min(t / self.duration, 1.0)
        return (1 - alpha) * self.q_start + alpha * self.q_goal

    def runBefore(self):
        """仿真循环开始前执行一次：初始化轨迹、episode 容器和对象 id。"""
        self.q_start = self.data.qpos[:7].copy()
        self.q_goal = np.array([0.0, -0.4, 0.0, -1.8, 0.0, 1.4, 0.7])
        self.duration = 1.0
        self.start_sim_time = self.data.time

        self.action = []
        self.episode = []
        self.episode_saved = False
        self.frame_count = 0
        self.init_pos = self.model.qpos0.copy()
        self.init_vel = self.data.qvel.copy()

        # site 是附着在 body 上的参考坐标系；这里用它表示末端中心点。
        self.id_eef = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_SITE,
            "ee_center_site",
        )
        if self.id_eef == -1:
            raise ValueError("site not found: ee_center_site")

        self.id_eef_body = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            "ee_center_body",
        )
        if self.id_eef_body == -1:
            raise ValueError("body not found: ee_center_body")

        self.id_object = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            "apriltag_0",
        )
        if self.id_object == -1:
            raise ValueError("object body not found: apriltag_0")

    def runFunc(self):
        """每个仿真步采集一帧数据，并下发当前关节目标。"""
        timestamp = self.data.time
        elapsed = timestamp - self.start_sim_time
        q_des = self.get_desired_position(elapsed)

        # getFixedCameraImage 返回 BGR；episode 中统一保存 RGB。
        rgb = self.getFixedCameraImage(fix_elevation=-90, show=SHOW_CAMERA_IMAGE)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        rgb = self.ensure_rgb_image(rgb)

        qpos = self.data.qpos.copy()
        qvel = self.data.qvel.copy()

        eef_pos = self.data.site_xpos[self.id_eef].copy()
        eef_quat = np.empty(4, dtype=np.float64)
        mujoco.mju_mat2Quat(eef_quat, self.data.site_xmat[self.id_eef].reshape(-1))

        action = q_des.copy()
        self.data.ctrl[:7] = action
        self.action.append(action.copy())

        object_pos = self.data.xpos[self.id_object].copy()
        object_quat = self.data.xquat[self.id_object].copy()

        sample = {
            "rgb": rgb,
            "qpos": qpos,
            "qvel": qvel,
            "eef_pos": eef_pos,
            "eef_quat": eef_quat,
            "object_pos": object_pos,
            "object_quat": object_quat,
            "action": action,
            "timestamp": timestamp,
        }

        self.episode.append(sample)
        self.frame_count += 1

        if self.frame_count == 1 or self.frame_count % PRINT_EVERY_N_FRAMES == 0:
            print(
                f"frame={self.frame_count:04d}, "
                f"t={timestamp:.3f}, "
                f"eef_pos={np.round(eef_pos, 3)}, "
                f"object_pos={np.round(object_pos, 3)}"
            )

    def save_episode(self, output_dir=None):
        """将采集到的 episode 保存为压缩 npz 文件。"""
        if getattr(self, "episode_saved", False):
            return None

        episode = getattr(self, "episode", [])
        if not episode:
            print("episode 为空，未保存。")
            return None

        output_dir = DEMO_DIR if output_dir is None else Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"sim_camera_tag_pose_episode_{datetime.now():%Y%m%d_%H%M%S}.npz"
        save_path = output_dir / filename

        np.savez_compressed(
            save_path,
            rgb=np.stack([sample["rgb"] for sample in episode]),
            qpos=np.stack([sample["qpos"] for sample in episode]),
            qvel=np.stack([sample["qvel"] for sample in episode]),
            eef_pos=np.stack([sample["eef_pos"] for sample in episode]),
            eef_quat=np.stack([sample["eef_quat"] for sample in episode]),
            object_pos=np.stack([sample["object_pos"] for sample in episode]),
            object_quat=np.stack([sample["object_quat"] for sample in episode]),
            action=np.stack([sample["action"] for sample in episode]),
            timestamp=np.array([sample["timestamp"] for sample in episode]),
            init_pos=self.init_pos,
            init_vel=self.init_vel,
            q_start=self.q_start,
            q_goal=self.q_goal,
            duration=np.array(self.duration),
        )

        self.episode_saved = True
        print(f"episode 已保存: {save_path}，共 {len(episode)} 帧。")
        return save_path

    def runAfter(self):
        """循环结束后保存 episode。"""
        print(f"本次共采集 {len(getattr(self, 'episode', []))} 帧。")
        self.save_episode()


if __name__ == "__main__":
    sctpd = SCTPD(str(MODEL_DIR / "scene_with_apriltag.xml"))
    try:
        sctpd.run_loop()
    finally:
        sctpd.runAfter()
