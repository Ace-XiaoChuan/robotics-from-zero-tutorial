"""
MuJoCo + OpenCV 棋盘格相机标定示例

主要功能：
1. 在 MuJoCo 场景中移动一个用于标定的棋盘格；
2. 从固定相机获取图像；
3. 按空格键采集棋盘格角点；
4. 按回车键执行 OpenCV 相机标定；
5. 标定成功后，额外打印由 MuJoCo 相机 fovy 直接计算得到的理论内参矩阵。

"""

import sys
import math
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import mujoco
import numpy as np
from pynput import keyboard


# =============================================================================
# 1. 项目路径配置
# =============================================================================
#
# 原始代码中直接写死：
#     ~/litchi_tutorial/mujoco-learning
#
# 这样在你自己的电脑上可以运行，但如果脚本位置变了，或者项目路径换了，
# 就容易导入失败。因此这里先尝试从“当前脚本所在位置”附近寻找 src 目录，
# 找不到时再回退到原来的固定路径。
#
# 如果你的项目已经通过 pip install -e . 安装成了包，理论上就不需要手动修改 sys.path。
# 但为了尽量兼容你当前的项目结构，这里仍然保留自动添加项目根目录的逻辑。


def find_project_root() -> Path:
    """
    尝试寻找 mujoco-learning 项目根目录。

    判断标准：目录下存在 src/ 子目录。

    返回：
        Path: 推断出的项目根目录。
    """
    current_file = Path(__file__).resolve()

    # 常见情况：
    # 1. 这个脚本就放在项目根目录；
    # 2. 这个脚本放在项目根目录的某个子目录里；
    # 3. 使用原始写死路径作为兜底。
    candidate_roots = [
        current_file.parent,
        current_file.parent.parent,
        Path("~/litchi_tutorial/mujoco-learning").expanduser(),
    ]

    for root in candidate_roots:
        if (root / "src").is_dir():
            return root

    # 如果没找到 src 目录，仍然返回原始路径。
    # 后续 import 如果失败，说明需要检查项目路径或运行位置。
    return Path("~/litchi_tutorial/mujoco-learning").expanduser()


PROJECT_ROOT = find_project_root()

# 将项目根目录加入 Python 模块搜索路径，方便 from src import ...
# 用 insert(0, ...) 而不是 append(...)，可以让当前项目里的 src 优先被搜索到。
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src import mujoco_viewer  # noqa: E402  # 依赖上面的 PROJECT_ROOT / sys.path 配置
import src.key_listener as key_listener  # noqa: E402


# =============================================================================
# 2. 标定棋盘格参数
# =============================================================================

# OpenCV 的棋盘格标定使用的是“内角点”数量，而不是方格数量。
# 例如 CALIB_BOARD_SIZE = (8, 5) 表示：
#   - 横向有 8 个内角点；
#   - 纵向有 5 个内角点；
#   - 总角点数为 8 * 5 = 40。
#
# 如果你的真实棋盘格是 9 列方格、6 行方格，那么内角点数量通常就是 8 x 5。
CALIB_BOARD_SIZE: Tuple[int, int] = (8, 5) # 全大写暗示这是常量、`:Tuple` 是 type annotation / 类型注解，但二者都不是强制的

# 每个棋盘格方格的真实物理尺寸，单位是米。
# 这里 0.02 表示每个小方格边长 2 cm。
CALIB_SQUARE_SIZE: float = 0.02

# 每次按方向键移动棋盘格的距离，单位是米。
CHECKERBOARD_MOVE_STEP: float = 0.01

# 建议至少采集 5 张以上不同视角/不同位置的图像再标定。
# 实际真实相机标定中，通常建议采集更多张，例如 10~20 张，结果会更稳定。
MIN_CALIB_IMAGES: int = 5

# OpenCV 显示窗口名称。
CALIB_WINDOW_NAME: str = "Calibration Image"


# =============================================================================
# 3. 生成棋盘格角点的世界坐标
# =============================================================================


def create_calib_object_points(
    board_size: Tuple[int, int],
    square_size: float,
) -> np.ndarray:
    """
    生成棋盘格内角点在棋盘格自身坐标系下的三维坐标。

    对于相机标定，OpenCV 需要两类点：

    1. object points：
       角点在真实世界/棋盘格坐标系中的三维坐标，例如：
           [0.00, 0.00, 0.00]
           [0.02, 0.00, 0.00]
           [0.04, 0.00, 0.00]
           ...

    2. image points：
       同一批角点在图像像素坐标系中的二维坐标，例如：
           [312.5, 240.1]
           [330.7, 240.4]
           ...

    棋盘格本身是一张平面，所以所有角点的 z 坐标都是 0。

    参数：
        board_size:
            棋盘格内角点数量，格式为 (宽方向角点数, 高方向角点数)。
        square_size:
            每个方格的实际边长，单位通常用米。

    返回：
        np.ndarray:
            shape 为 (角点总数, 3) 的数组。
            每一行表示一个角点的 [x, y, z] 坐标。
    """
    board_width, board_height = board_size

    # np.prod(board_size) = board_width * board_height
    # 对于 (8, 5)，结果是 40。
    point_count = int(np.prod(board_size))

    # 先创建一个全 0 数组：
    #   行数 = 角点数量；
    #   列数 = 3，对应 x, y, z。
    # 因为棋盘格是平面，所以 z 这一列保持为 0。
    object_points = np.zeros((point_count, 3), np.float32)

    # np.mgrid[0:board_width, 0:board_height] 会生成二维网格坐标。
    # .T.reshape(-1, 2) 会把它整理成：
    #   [0, 0]
    #   [1, 0]
    #   [2, 0]
    #   ...
    #   [7, 4]
    # 这种“每一行一个点”的形式。
    object_points[:, :2] = np.mgrid[0:board_width, 0:board_height].T.reshape(-1, 2)

    # 上一步得到的坐标单位是“格子数”：0、1、2、3...
    # 乘以真实方格尺寸后，单位变成米。
    object_points *= square_size

    return object_points


# 全局模板：一张棋盘格的所有三维角点坐标。
# 每采集成功一张图像，就把这份模板 copy 一份放入 calib_object_points。
CALIB_OBJECT_POINTS = create_calib_object_points(CALIB_BOARD_SIZE, CALIB_SQUARE_SIZE)


# =============================================================================
# 4. PandaEnv 主类
# =============================================================================


class PandaEnv(mujoco_viewer.CustomViewer):
    """
    自定义 MuJoCo Viewer 环境。

    这个类负责：
    - 启动键盘监听；
    - 移动标定棋盘格；
    - 从 MuJoCo 固定相机获取图像；
    - 采集棋盘格角点；
    - 执行 OpenCV 相机标定；
    - 计算并打印 MuJoCo 虚拟相机理论内参。
    """

    def __init__(self, path: str):
        """
        初始化环境。

        参数：
            path:
                MuJoCo XML 场景文件路径。
        """
        # 调用父类初始化。
        # 参数 3、azimuth、elevation 是原始代码中的 viewer 视角设置。
        super().__init__(path, 3, azimuth=-45, elevation=-30)

        self.path = path

        # ---------------------------------------------------------------------
        # 按键状态
        # ---------------------------------------------------------------------
        # 原始代码中 key_states 是全局变量。
        # 这里将它变成实例变量 self.key_states，这样更安全：
        # 如果以后创建多个 PandaEnv 对象，它们不会共享同一份按键状态。
        self.key_states = self.create_default_key_states()

        # 启动键盘监听线程。
        # key_listener 会在按键按下/松开时修改 self.key_states 中对应键的 True/False 状态。
        self.key_listener = key_listener.KeyListener(self.key_states)
        self.key_listener.start()

        # ---------------------------------------------------------------------
        # 标定相关数据
        # ---------------------------------------------------------------------
        # calib_object_points：
        #   每张成功采集的图像，对应一份棋盘格三维角点坐标。
        #   对于固定棋盘格模板，每次内容相同，但需要按 OpenCV 要求组织成 list。
        self.calib_object_points: List[np.ndarray] = []

        # calib_image_points：
        #   每张成功采集的图像中，检测到的棋盘格二维像素角点。
        self.calib_image_points: List[np.ndarray] = []

        # image_size：
        #   OpenCV calibrateCamera 需要图像尺寸，格式是 (width, height)。
        #   这里只保存尺寸，减少内存占用。
        self.image_size: Optional[Tuple[int, int]] = None

        # camera_matrix：
        #   OpenCV 标定得到的相机内参矩阵，通常形式为：
        #       [[fx,  0, cx],
        #        [ 0, fy, cy],
        #        [ 0,  0,  1]]
        self.camera_matrix: Optional[np.ndarray] = None

        # dist_coeffs：
        #   OpenCV 标定得到的镜头畸变参数。
        #   对真实相机通常很重要；对于 MuJoCo 虚拟相机，理论上一般可以认为畸变为 0。
        self.dist_coeffs: Optional[np.ndarray] = None

        # 标定是否完成的标志位。
        self.calib_done: bool = False

    # @staticmethod 是 Python 里的静态方法装饰器。
    # 它表示：这个方法属于类的命名空间，但不需要访问实例对象 self，也不需要访问类对象 cls。
    @staticmethod
    def create_default_key_states() -> dict:
        """
        创建默认按键状态字典。

        False 表示：当前没有按下/没有触发这个键。
        True 表示：当前按下了这个键，或者这个键对应的动作需要被执行。

        返回：
            dict: 按键状态表。
        """
        return {
            keyboard.Key.up: False,
            keyboard.Key.down: False,
            keyboard.Key.left: False,
            keyboard.Key.right: False,
            keyboard.Key.page_up: False,
            keyboard.Key.page_down: False,
            keyboard.Key.space: False,  # 空格键：采集一张标定图像
            keyboard.Key.enter: False,  # 回车键：执行相机标定
        }

    def runBefore(self):
        """
        Viewer 主循环开始前执行一次。

        这里初始化棋盘格的位置。
        后续 runFunc 每一帧都会根据键盘输入更新这些坐标。
        """
        self.initial_pos = self.model.qpos0.copy()

        # 标定棋盘格的初始位置。
        # 具体坐标含义取决于你的 MuJoCo 场景文件。
        self.checker_board_x = 0.5
        self.checker_board_y = 0.0
        self.checker_board_z = 0.4

    def update_checkerboard_position_from_keyboard(self) -> None:
        """
        根据当前按键状态更新棋盘格位置。

        方向键控制 x / z，PageUp / PageDown 控制 y。

        注意：
        - 方向键通常适合“按住连续移动”；
        - 空格和回车适合“一次性触发”，所以它们会在执行后手动改回 False。
        """
        if self.key_states[keyboard.Key.up]:
            self.checker_board_z += CHECKERBOARD_MOVE_STEP
        if self.key_states[keyboard.Key.down]:
            self.checker_board_z -= CHECKERBOARD_MOVE_STEP
        if self.key_states[keyboard.Key.left]:
            self.checker_board_x -= CHECKERBOARD_MOVE_STEP
        if self.key_states[keyboard.Key.right]:
            self.checker_board_x += CHECKERBOARD_MOVE_STEP
        if self.key_states[keyboard.Key.page_up]:
            self.checker_board_y += CHECKERBOARD_MOVE_STEP
        if self.key_states[keyboard.Key.page_down]:
            self.checker_board_y -= CHECKERBOARD_MOVE_STEP

    @staticmethod
    def ensure_rgb_image(image: np.ndarray) -> np.ndarray:
        """
        确保 MuJoCo 返回的图像是 RGB 三通道格式。

        MuJoCo / viewer 有时可能返回 RGBA 图像，也就是最后一维有 4 个通道。
        OpenCV 标定只需要 RGB/BGR 中的颜色信息，不需要 alpha 通道，所以这里去掉 alpha。

        参数：
            image:
                MuJoCo 相机图像。

        返回：
            np.ndarray:
                shape 为 (height, width, 3) 的 RGB 图像。
        """
        if image.ndim != 3:
            raise ValueError(f"期望输入为 H x W x C 图像，但实际 shape 为: {image.shape}")

        if image.shape[-1] == 4:
            image = image[..., :3]

        if image.shape[-1] != 3:
            raise ValueError(f"期望图像通道数为 3 或 4，但实际 shape 为: {image.shape}")

        # ascontiguousarray 可以避免某些 OpenCV 函数因为内存不连续而报错。
        return np.ascontiguousarray(image)

    def collect_calib_image(self, image: np.ndarray) -> bool:
        """
        从当前相机图像中检测棋盘格角点，并保存成功检测到的数据。

        参数：
            image:
                当前固定相机获取到的 RGB 图像。

        返回：
            bool:
                True  表示成功检测并保存了一张标定图像；
                False 表示没有检测到完整棋盘格角点。
        """
        image = self.ensure_rgb_image(image)

        # OpenCV 的角点检测使用灰度图即可。
        # 注意：原始代码先做了 Canny 边缘检测，然后把边缘图传给 findChessboardCorners。
        # 这在某些情况下会损失灰度信息，反而不利于 cornerSubPix 做亚像素优化。
        # 因此这里改为：
        #   - 检测角点时使用轻微高斯模糊后的灰度图；
        #   - 亚像素优化时使用原始灰度图。
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # 棋盘格检测参数：
        # CALIB_CB_ADAPTIVE_THRESH：自适应阈值，适应不同亮度；
        # CALIB_CB_NORMALIZE_IMAGE：图像归一化，增强对比度。
        #
        # 原始代码使用了 CALIB_CB_FAST_CHECK，它速度更快，但容易在视角不好时漏检。
        # 这里先去掉 FAST_CHECK，优先保证检测稳定性。
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

        ret, corners = cv2.findChessboardCorners(
            gray_blur,
            CALIB_BOARD_SIZE,
            flags,
        )

        if not ret:
            # 没检测到角点时，显示当前灰度图，方便你观察棋盘格是否太远、太斜、太小、被挡住等。
            cv2.imshow(CALIB_WINDOW_NAME, gray_blur)
            cv2.waitKey(100)
            print("未检测到角点，请调整棋盘格位置/视角")
            return False

        # 亚像素角点优化：
        # findChessboardCorners 返回的是初步角点位置；
        # cornerSubPix 会在角点附近进一步细化坐标，提高标定精度。
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,     # 最大迭代次数
            0.001,  # 收敛阈值，越小越精细，但耗时可能略增
        )
        corners_refined = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria,
        )

        # 保存图像尺寸。
        # calibrateCamera 的 imageSize 参数格式是 (width, height)，不是 (height, width)。
        height, width = gray.shape[:2]
        current_image_size = (width, height)

        if self.image_size is None:
            self.image_size = current_image_size
        elif self.image_size != current_image_size:
            # 标定时所有图像尺寸应该一致。
            # 如果尺寸变化，直接跳过这一张，避免 calibrateCamera 输入不一致。
            print(
                f"当前图像尺寸 {current_image_size} 与之前尺寸 {self.image_size} 不一致，已跳过。"
            )
            return False

        # OpenCV calibrateCamera 要求：
        #   object_points 是一个 list，每个元素对应一张图像中的三维角点；
        #   image_points 也是一个 list，每个元素对应一张图像中的二维角点。
        #
        # CALIB_OBJECT_POINTS 是模板数组，这里使用 copy()，避免后续误修改模板时影响已保存数据。
        self.calib_object_points.append(CALIB_OBJECT_POINTS.copy())
        self.calib_image_points.append(corners_refined)

        # 可视化检测结果。
        img_with_corners = cv2.drawChessboardCorners(
            image.copy(),
            CALIB_BOARD_SIZE,
            corners_refined,
            ret,
        )

        # cv2.imshow 默认按 BGR 显示彩色图像；
        # MuJoCo 返回的是 RGB，所以这里转成 BGR，避免颜色显示颠倒。
        img_with_corners_bgr = cv2.cvtColor(img_with_corners, cv2.COLOR_RGB2BGR)
        cv2.imshow(CALIB_WINDOW_NAME, img_with_corners_bgr)
        cv2.waitKey(300)

        print(f"成功采集第 {len(self.calib_image_points)} 张标定图像")
        return True

    def calibrate_camera(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        使用已经采集到的棋盘格角点执行 OpenCV 相机标定。

        返回：
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
                标定成功时返回 (相机内参矩阵, 畸变系数)；
                标定失败时返回 (None, None)。
        """
        image_count = len(self.calib_image_points)

        if image_count < MIN_CALIB_IMAGES:
            print(
                f"标定图像数量不足：当前 {image_count} 张，建议至少 {MIN_CALIB_IMAGES} 张。"
            )
            return None, None

        if self.image_size is None:
            print("缺少图像尺寸信息，无法标定。请先成功采集至少一张标定图像。")
            return None, None

        print("\n开始相机标定...")

        # calibrateCamera 返回值说明：
        #   rms_error：整体 RMS 重投影误差，越小越好；
        #   camera_matrix：内参矩阵；
        #   dist_coeffs：畸变系数；
        #   rvecs / tvecs：每张标定图像对应的外参。
        rms_error, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.calib_object_points,
            self.calib_image_points,
            self.image_size,
            None,
            None,
        )

        # getOptimalNewCameraMatrix 会根据畸变参数生成一个优化后的相机矩阵。
        # alpha = 1 表示尽量保留所有像素，可能留下黑边；
        # alpha = 0 表示裁剪掉黑边，保留有效区域。
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            camera_matrix,
            dist_coeffs,
            self.image_size,
            1,
            self.image_size,
        )

        # 手动计算平均重投影误差，便于直观看标定质量。
        # 思路：
        #   1. 用标定得到的内参/外参，把三维角点重新投影回图像；
        #   2. 和实际检测到的二维角点比较距离；
        #   3. 误差越小，说明标定越好。
        total_error = 0.0
        for i in range(image_count):
            projected_points, _ = cv2.projectPoints(
                self.calib_object_points[i],
                rvecs[i],
                tvecs[i],
                camera_matrix,
                dist_coeffs,
            )

            error = cv2.norm(
                self.calib_image_points[i],
                projected_points,
                cv2.NORM_L2,
            ) / len(projected_points)

            total_error += error

        mean_error = total_error / image_count

        print("\n标定完成")
        print(f"OpenCV calibrateCamera RMS 误差: {rms_error:.6f}")
        print(f"平均重投影误差: {mean_error:.6f}，越小越好")
        print(f"原始相机内参矩阵:\n{camera_matrix}")
        print(f"畸变系数:\n{dist_coeffs}")
        print(f"优化后相机矩阵:\n{new_camera_matrix}")
        print(f"有效 ROI 区域: {roi}")

        # 保存标定结果，供后续程序使用。
        self.camera_matrix = new_camera_matrix
        self.dist_coeffs = dist_coeffs
        self.calib_done = True

        return new_camera_matrix, dist_coeffs

    def get_mujoco_camera_matrix(
        self,
        camera_name: str,
        image_shape: Tuple[int, ...],
    ) -> np.ndarray:
        """
        根据 MuJoCo 虚拟相机的 fovy 直接计算理论相机内参矩阵。

        对于 MuJoCo 虚拟相机，如果没有额外设置镜头畸变，通常可以认为畸变为 0。
        因此理论内参可以直接从相机视场角 fovy 和图像尺寸计算得到。

        参数：
            camera_name:
                MuJoCo XML 中定义的 camera 名称，例如 "rgb_camera"。
            image_shape:
                当前相机图像的 shape，通常是 (height, width, channels)。

        返回：
            np.ndarray:
                3x3 相机内参矩阵。
        """
        camera_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_CAMERA,
            camera_name,
        )

        if camera_id == -1:
            raise ValueError(f"在 MuJoCo 模型中找不到相机: {camera_name}")

        height, width = image_shape[:2]

        # MuJoCo cam_fovy 是竖直方向视场角，单位是度。
        fovy_degrees = self.model.cam_fovy[camera_id]

        # 针孔相机模型中，竖直方向焦距 fy 与 fovy 的关系：
        #   fy = 0.5 * image_height / tan(fovy / 2)
        #
        # math.radians(fovy_degrees) 把角度转成弧度。
        focal_length = 0.5 * height / math.tan(math.radians(fovy_degrees) / 2.0)

        # 假设像素是正方形，所以 fx = fy。
        # 主点 cx, cy 默认放在图像中心。
        camera_matrix = np.array(
            [
                [focal_length, 0.0, width / 2.0],
                [0.0, focal_length, height / 2.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float32,
        )

        return camera_matrix

    def print_mujoco_camera_intrinsics(
        self,
        image: np.ndarray,
        camera_name: str = "rgb_camera",
    ) -> None:
        """
        打印 MuJoCo 虚拟相机由 fovy 计算得到的理论内参和畸变参数。

        参数：
            image:
                当前相机图像，用于读取实际 width / height。
            camera_name:
                MuJoCo XML 中的相机名称。
        """
        mujoco_camera_matrix = self.get_mujoco_camera_matrix(camera_name, image.shape)

        # MuJoCo 默认虚拟相机没有真实镜头畸变，因此这里设为 0。
        # OpenCV 常用 5 个畸变参数：[k1, k2, p1, p2, k3]。
        mujoco_dist_coeffs = np.zeros(5, dtype=np.float32)

        print("\nMuJoCo fovy 直接计算的理论内参矩阵:")
        print(mujoco_camera_matrix)
        print("MuJoCo 虚拟相机理论畸变系数:")
        print(mujoco_dist_coeffs)

    def runFunc(self):
        """
        Viewer 主循环中每一帧都会调用的函数。

        每一帧主要做：
        1. 根据键盘输入更新棋盘格位置；
        2. 把棋盘格 mocap body 移动到新位置；
        3. 从固定相机获取图像；
        4. 如果按下空格，采集标定图像；
        5. 如果按下回车，执行相机标定。
        """
        # 1. 根据方向键更新棋盘格坐标。
        self.update_checkerboard_position_from_keyboard()

        # 2. 将 MuJoCo 中名为 calib_checkerboard 的 mocap body 移动到当前坐标。
        #    这里的名字必须和 XML 文件里的 mocap body 名称一致。
        self.setMocapPosition(
            "calib_checkerboard",
            [self.checker_board_x, self.checker_board_y, self.checker_board_z],
        )

        # 3. 获取固定相机图像。
        #    fix_elevation=-90 和 show=True 保持你原始代码里的设置。
        image = self.getFixedCameraImage(fix_elevation=-90, show=True)

        # 如果当前没有拿到图像，直接结束这一帧。
        if image is None:
            return

        image = self.ensure_rgb_image(image)

        # 4. 空格键：采集一张标定图像。
        #
        # 空格键是“一次性动作”，所以执行完后要手动设回 False，
        # 避免按一下空格却在多个帧里连续采集很多张。
        if self.key_states[keyboard.Key.space]:
            self.collect_calib_image(image)
            self.key_states[keyboard.Key.space] = False

        # 5. 回车键：执行相机标定。
        #
        # 回车键同样是“一次性动作”，执行完后也要手动设回 False。
        if self.key_states[keyboard.Key.enter]:
            camera_matrix, dist_coeffs = self.calibrate_camera()
            self.key_states[keyboard.Key.enter] = False

            # 如果标定失败，例如采集图像数量不足，就不继续做后面的对比输出。
            if camera_matrix is None or dist_coeffs is None:
                print("标定未成功，暂不输出 OpenCV 标定结果与 MuJoCo 理论内参的对比。")
                return

            # 标定成功后，打印 MuJoCo 虚拟相机由 fovy 直接计算的理论内参。
            # 这可以和 OpenCV 标定结果进行对比。
            self.print_mujoco_camera_intrinsics(image, camera_name="rgb_camera")


# =============================================================================
# 5. 程序入口
# =============================================================================


if __name__ == "__main__":
    # 创建 OpenCV 显示窗口，用于显示角点检测结果或调试图像。
    cv2.namedWindow(CALIB_WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(CALIB_WINDOW_NAME, 640, 480)

    # 创建环境对象。
    # 注意：这个 XML 路径是相对于你运行 python 命令时的当前工作目录。
    # 如果运行时报找不到文件，可以改成绝对路径，或者确认你是在项目根目录下运行。
    env = PandaEnv("/home/ace/litchi_tutorial/mujoco-learning/model/franka_emika_panda/scene_with_checkerboard.xml")

    try:
        # 启动 viewer 主循环。
        env.run_loop()
    finally:
        # 无论程序正常结束还是报错退出，都尽量释放窗口和键盘监听资源。
        cv2.destroyAllWindows()
        env.key_listener.stop()
