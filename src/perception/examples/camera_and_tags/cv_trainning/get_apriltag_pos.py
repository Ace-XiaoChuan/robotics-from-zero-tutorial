import mujoco
import math
import numpy as np
from pynput import keyboard
import sys
from pathlib import Path

# 项目根目录。这里用 expanduser() 将 "~" 展开成用户主目录。
project_root = Path("~/litchi_tutorial/mujoco-learning").expanduser()

# 将项目根目录加入 Python 模块搜索路径，方便后续 import src 下的自定义模块。
sys.path.append(str(project_root))

import src.mujoco_viewer as mujoco_viewer
import src.key_listener as key_listener

# 自定义 AprilTag / PnP 位姿求解模块
import src.solvepnp as solvepnp


# 保存键盘按键状态的字典。
# True 表示当前按键被按下，False 表示当前按键未按下。
key_states = {
    keyboard.Key.up: False,         # 上方向键：控制 AprilTag 沿 z 轴上移
    keyboard.Key.down: False,       # 下方向键：控制 AprilTag 沿 z 轴下移
    keyboard.Key.left: False,       # 左方向键：控制 AprilTag 沿 x 轴负方向移动
    keyboard.Key.right: False,      # 右方向键：控制 AprilTag 沿 x 轴正方向移动
    keyboard.Key.page_up: False,    # PageUp：控制 AprilTag 沿 y 轴正方向移动
    keyboard.Key.page_down: False,  # PageDown：控制 AprilTag 沿 y 轴负方向移动
}


class PandaEnv(mujoco_viewer.CustomViewer):
    """
    Panda 机械臂仿真环境。

    该类继承自自定义的 CustomViewer，主要功能包括：
    1. 加载 MuJoCo 场景；
    2. 启动键盘监听；
    3. 在仿真过程中通过键盘移动 AprilTag；
    4. 从固定相机获取图像；
    5. 使用 SolvePnP 根据图像中的 AprilTag 估计其位姿。
    """

    def __init__(self, path):
        """
        初始化仿真环境。

        参数：
            path: MuJoCo XML 场景文件路径。
        """

        # 调用父类 CustomViewer 的初始化函数。
        # 参数含义取决于你的 CustomViewer 实现：
        # path: XML 场景文件路径
        # 3: 可能表示相机、渲染模式或窗口配置参数
        # azimuth / elevation: 初始观察视角的方位角和俯仰角
        super().__init__(path, 3, azimuth=-45, elevation=-30)

        # 保存场景文件路径
        self.path = path

        # 创建键盘监听器。
        # key_states 会被监听器实时更新，用于在 runFunc() 中判断哪些键正在被按下。
        self.key_listener = key_listener.KeyListener(key_states)

        # 启动键盘监听线程
        self.key_listener.start()

    def runBefore(self):
        """
        仿真循环开始前执行一次的初始化函数。

        通常用于：
        1. 记录初始关节状态；
        2. 初始化相机内参；
        3. 初始化畸变参数；
        4. 初始化 SolvePnP；
        5. 设置 AprilTag 的初始位置。
        """

        # 记录模型的初始关节位置 qpos0。
        # self.model 是 MuJoCo 的 mjModel 对象。
        self.initial_pos = self.model.qpos0.copy()

        # AprilTag 的实际物理尺寸，单位通常为米。
        # SolvePnP 需要知道标记的真实边长，才能估计出正确尺度的 3D 位姿。
        TAG_SIZE = 0.1

        # 根据相机名称获取 MuJoCo 中相机的 ID。
        # "rgb_camera" 必须与 XML 文件中的 camera name 保持一致。
        camera_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_CAMERA,
            "rgb_camera"
        )

        # 获取 MuJoCo 相机的竖直方向视场角，单位是度。
        fovy = self.model.cam_fovy[camera_id]

        # 渲染图像的宽和高。
        # 这里假设 getFixedCameraImage() 返回的是 640x480 图像。
        width = 640
        height = 480

        # 根据竖直视场角 fovy 计算理想针孔相机焦距。
        # 公式：
        #   f = 0.5 * image_height / tan(fovy / 2)
        # 因为 fovy 是角度，所以需要转换为弧度。
        f = 0.5 * height / math.tan(fovy * math.pi / 360)

        # 下面这一行是根据 MuJoCo 相机 fovy 理论计算得到的相机内参矩阵。
        # 如果没有真实标定参数，可以使用这种方式近似构造 CAMERA_MATRIX。
        #
        # CAMERA_MATRIX = np.array((
        #     (f, 0, width / 2),
        #     (0, f, height / 2),
        #     (0, 0, 1)
        # ))

        # 相机内参矩阵，格式为：
        #   [[fx,  0, cx],
        #    [ 0, fy, cy],
        #    [ 0,  0,  1]]
        #
        # fx, fy: x / y 方向焦距，单位是像素
        # cx, cy: 主点坐标，通常接近图像中心
        #
        # 这里使用的是相机标定得到的内参，而不是上面根据 fovy 估算的值。
        CAMERA_MATRIX = np.array([
            [414.42263304, 0.0, 318.91934938],
            [0.0, 414.314660431, 239.2895262],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        # 相机畸变参数。
        # OpenCV 常用格式为：
        #   [k1, k2, p1, p2, k3]
        #
        # k1, k2, k3: 径向畸变参数
        # p1, p2: 切向畸变参数
        DIST_COEFFS = np.array([
            0.005498773,
            -0.00174292,
            -0.0002786,
            -0.00070906,
            -0.00284597
        ], dtype=np.float32)

        # 如果想忽略镜头畸变，可以使用全 0 畸变参数。
        # DIST_COEFFS = np.array(
        #     [0.0, 0.0, 0.0, 0.0, 0.0],
        #     dtype=np.float32
        # )

        # 创建 SolvePnP 求解器。
        # 输入参数包括：
        #   TAG_SIZE: AprilTag 实际尺寸
        #   CAMERA_MATRIX: 相机内参矩阵
        #   DIST_COEFFS: 相机畸变参数
        self.spnp = solvepnp.SolvePnp(TAG_SIZE, CAMERA_MATRIX, DIST_COEFFS)

        # AprilTag mocap body 的初始位置。
        # 这里假设 XML 中存在名为 "apriltag_0" 的 mocap 物体。
        self.apriltag_pos_x = 0.5
        self.apriltag_pos_y = 0
        self.apriltag_pos_z = 0.05

    def runFunc(self):
        """
        每个仿真循环都会调用的函数。

        主要执行流程：
        1. 根据键盘输入更新 AprilTag 的位置；
        2. 将更新后的位置写入 MuJoCo mocap body；
        3. 从固定相机获取图像；
        4. 使用 SolvePnP 识别图像中的 AprilTag 并计算位姿；
        5. 显示检测结果并打印位姿矩阵。
        """

        # 如果按下上方向键，让 AprilTag 沿 z 轴正方向移动。
        if key_states[keyboard.Key.up]:
            self.apriltag_pos_z += 0.01

        # 如果按下下方向键，让 AprilTag 沿 z 轴负方向移动。
        if key_states[keyboard.Key.down]:
            self.apriltag_pos_z -= 0.01

        # 如果按下左方向键，让 AprilTag 沿 x 轴负方向移动。
        if key_states[keyboard.Key.left]:
            self.apriltag_pos_x -= 0.01

        # 如果按下右方向键，让 AprilTag 沿 x 轴正方向移动。
        if key_states[keyboard.Key.right]:
            self.apriltag_pos_x += 0.01

        # 如果按下 PageUp，让 AprilTag 沿 y 轴正方向移动。
        if key_states[keyboard.Key.page_up]:
            self.apriltag_pos_y += 0.01

            # 打印当前 y 坐标，便于调试。
            print(self.apriltag_pos_y)

        # 如果按下 PageDown，让 AprilTag 沿 y 轴负方向移动。
        if key_states[keyboard.Key.page_down]:
            self.apriltag_pos_y -= 0.01

        # 将计算得到的 AprilTag 位置设置到 MuJoCo 中的 mocap body。
        # "apriltag_0" 必须与 XML 中对应 mocap body 的名称一致。
        self.setMocapPosition(
            "apriltag_0",
            [
                self.apriltag_pos_x,
                self.apriltag_pos_y,
                self.apriltag_pos_z
            ]
        )

        # 从固定相机获取图像。
        # fix_elevation=-90 表示以固定俯视角或某种指定视角获取图像，
        # 具体含义取决于 CustomViewer.getFixedCameraImage() 的实现。
        image = self.getFixedCameraImage(fix_elevation=-90)

        # 打印 MuJoCo 相机的 interpupillary distance 参数。
        # 对普通单目相机通常不是核心参数，这里主要用于调试。
        print(self.model.cam_ipd)

        # 如果没有成功获取图像，则跳过本轮图像处理。
        if image is None:
            pass
        else:
            # 使用 SolvePnP 处理图像。
            # compute(image, 0) 表示：
            #   image: 当前相机图像
            #   0: 要检测或使用的 AprilTag ID
            #
            # 返回值的具体含义取决于 solvepnp.SolvePnp.compute() 的实现。
            # 这里仅使用最后一个返回值 transform，通常表示相机到标签、
            # 或标签到相机的 4x4 齐次变换矩阵。
            _, _, _, transform = self.spnp.compute(image, 0)

            # 显示 AprilTag 检测结果，例如角点、坐标轴或调试图像。
            self.spnp.show()

            # 打印 SolvePnP 计算得到的位姿变换矩阵。
            print(transform)


if __name__ == "__main__":
    # 创建 PandaEnv 仿真环境。
    # 这里传入 MuJoCo XML 场景文件路径。
    env = PandaEnv(
        "/home/ace/litchi_tutorial/mujoco-learning/model/franka_emika_panda/scene_with_apriltag.xml"
    )

    # 启动仿真主循环。
    # run_loop() 通常会不断调用 runBefore() 和 runFunc()。
    env.run_loop()