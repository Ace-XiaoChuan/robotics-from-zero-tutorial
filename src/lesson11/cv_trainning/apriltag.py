"""
MuJoCo + pupil_apriltags 的 AprilTag 检测示例。

这个脚本做的事情很简单：
1. 启动一个自定义 MuJoCo Viewer；
2. 在 Viewer 主循环开始前创建 AprilTag 检测器；
3. 每一帧从跟踪相机获取图像；
4. 把彩色图转成灰度图；
5. 用 pupil_apriltags 检测图像中的 AprilTag；
6. 打印检测到的 tag id 和中心点像素坐标。

注意：
- 这里的 AprilTag 应该已经在 MuJoCo XML 场景中作为纹理/平面物体放好了；
- Python 代码本身不负责生成 tag，只负责从相机图像里识别它；
- 如果相机看不到 tag、tag 太小、太斜、太暗，检测结果可能为空。
"""

import cv2
import sys
from pathlib import Path


# =============================================================================
# 1. 项目路径配置
# =============================================================================
#
# 这个脚本需要导入项目里的 src.mujoco_viewer。
# 如果没有通过 pip install -e . 把整个项目安装成包，就需要手动把项目根目录
# 加入 sys.path，否则 Python 可能找不到 src 模块。
#
# 当前写法使用固定路径：
#     ~/litchi_tutorial/mujoco-learning

project_root = Path("~/litchi_tutorial/mujoco-learning").expanduser()
sys.path.append(str(project_root))

import src.mujoco_viewer as mujoco_viewer

# pupil_apriltags 是第三方 AprilTag 检测库。
# 安装包名通常是 pupil-apriltags，导入模块名是 pupil_apriltags。
# Detector 是它的核心检测器类。
from pupil_apriltags import Detector


# =============================================================================
# 2. 自定义 MuJoCo 环境
# =============================================================================


class PandaEnv(mujoco_viewer.CustomViewer):
    """
    自定义 Viewer 环境。

    这个类继承自项目里的 CustomViewer。
    CustomViewer 通常会提供：
    - MuJoCo 模型和数据对象，例如 self.model / self.data；
    - 相机图像获取方法，例如 getTrackingCameraImage；
    - Viewer 主循环，例如 run_loop；
    - 生命周期钩子，例如 runBefore / runFunc。
    """

    def __init__(self, path):
        """
        初始化 MuJoCo Viewer。

        参数：
            path:
                MuJoCo XML 场景文件路径。
                这个 XML 里应该包含用于显示 AprilTag 的物体/纹理，
                以及脚本后续要读取的相机。
        """
        # 调用父类初始化。
        # 前面的注释已经讲过了
        super().__init__(path, 3, azimuth=-45, elevation=-30)

        # 保存场景路径，方便后续调试或打印。
        self.path = path
    
    def runBefore(self):
        """
        Viewer 主循环开始前执行一次。

        这里适合做只需要初始化一次的事情，例如：
        - 读取模型初始状态；
        - 创建 AprilTag 检测器；
        - 初始化缓存变量。
        """
        # qpos0 是 MuJoCo 模型中的默认关节位置。
        # copy() 的意义是保存一份独立副本，避免后续仿真状态变化影响这个初始值。
        self.initial_pos = self.model.qpos0.copy()

        # 初始化 AprilTag 检测器。
        #
        # families:
        #   指定要检测哪一种 AprilTag 家族(AprilTag 家族就是不同规格的 AprilTag 编码集合)。
        #   "tag36h11" 是很常见的一种 tag family：
        #   - 36 表示编码位数相关规模；
        #   - h11 表示最小汉明距离相关设计；
        #   实际使用时，必须和你贴在场景里的 tag 图片家族一致。
        #
        # nthreads:
        #   检测使用的线程数。
        #   设为 1 最稳定、最容易复现；图像很大或检测很多 tag 时可以适当增大。
        #
        # quad_decimate:
        #   检测前对图像降采样的倍率。
        #   1.0 表示不降采样，精度更好但速度较慢；
        #   2.0 表示缩小后检测，速度更快但远处/小 tag 可能更容易漏检。
        #
        # refine_edges:
        #   是否在检测后细化 tag 边缘位置。
        #   设为 1 通常能让角点定位更准，对后续位姿估计有帮助。
        self.detector = Detector(
            families="tag36h11",
            nthreads=1,
            quad_decimate=1.0,
            refine_edges=1,
        )

    def runFunc(self):
        """
        Viewer 主循环中每一帧都会执行的函数。

        每一帧的调用顺序：
        1. 从 MuJoCo 跟踪相机渲染当前图像；
        2. 把彩色图转成灰度图；
        3. 调用 AprilTag 检测器；
        4. 遍历检测结果并打印 tag 信息。
        """
        # 从跟踪相机获取当前帧图像。
        #
        # fix_elevation=-90 表示在获取图像时固定相机俯仰角。
        # 具体含义取决于 CustomViewer.getTrackingCameraImage 的实现。
        #
        # 返回值通常是一个 numpy 数组，形状类似：
        #     (height, width, 3)
        #
        # 也就是：
        #     高度 x 宽度 x 颜色通道
        image = self.getFixedCameraImage(fix_elevation=-90, show=True)
        # AprilTag 检测一般只需要亮度信息，不需要 RGB/BGR 彩色信息。
        # 因此先转成灰度图，形状会从：
        #     (height, width, 3)
        # 变成：
        #     (height, width)
        #
        # 这里使用 COLOR_BGR2GRAY，表示当前代码把 image 当作 BGR 格式处理。
        # 如果你确认 getTrackingCameraImage 返回的是 RGB 图像，也可以改为 COLOR_RGB2GRAY。
        # 对灰度检测来说，两者通常都能工作，但严格来说通道顺序会影响灰度加权值。
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 执行 AprilTag 检测。
        #
        # tags 是一个列表，每个元素代表检测到的一个 tag。
        # 如果当前画面里没有 tag，或者 tag 没有被成功识别，tags 就是空列表。
        tags = self.detector.detect(gray_image)

        # 遍历所有检测结果。
        #
        # 常用字段包括：
        # - tag.tag_id：tag 编号，也就是 AprilTag 图片编码出的 id；
        # - tag.center：tag 中心点在图像中的像素坐标，格式大致是 [u, v]；
        # - tag.corners：tag 四个角点的像素坐标；
        # - tag.decision_margin：检测置信度相关指标，越大通常越可靠。
        #
        # 当前脚本只打印 id 和中心点，已经足够确认“是否检测到了正确的 tag”。
        for tag in tags:
            print(f"Detected tag ID: {tag.tag_id}, Center: {tag.center}")


# =============================================================================
# 3. 程序入口
# =============================================================================


if __name__ == "__main__":
    # 创建自定义 MuJoCo 环境。
    #
    # 这里的 XML 文件应该包含 AprilTag 场景，例如：
    # - 带有 AprilTag 纹理的平面；
    # - 可以看到该平面的相机；
    # - Franka Panda 机械臂或其他仿真物体。
    env = PandaEnv("/home/ace/litchi_tutorial/mujoco-learning/model/franka_emika_panda/scene_with_apriltag.xml")

    # 启动 Viewer 主循环。
    #
    # run_loop 通常会在内部反复调用：
    # - env.runBefore()：开始前一次；
    # - env.runFunc()：每一帧一次。
    #
    # 因此真正的图像获取和 AprilTag 检测逻辑在 runFunc 里。
    env.run_loop()
