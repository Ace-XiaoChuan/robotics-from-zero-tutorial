import mujoco
import numpy as np
import glfw
import cv2

# 渲染图像的分辨率，宽 640，高 480
resolution = (640, 480)

# ============================================================
# 1. 创建 OpenGL 上下文
# ============================================================
# MuJoCo 的渲染依赖 OpenGL。
# 即使你不想打开可见窗口，只做离屏渲染，也仍然需要一个 OpenGL 上下文。
glfw.init()

# 设置 GLFW 窗口不可见
# 这里创建的是隐藏窗口，用来提供 OpenGL 上下文，而不是给用户显示画面
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

# 创建一个隐藏窗口，大小和渲染分辨率一致
window = glfw.create_window(
    resolution[0],      # 窗口宽度
    resolution[1],      # 窗口高度
    "Offscreen",        # 窗口标题，因为窗口不可见，所以基本无所谓
    None,
    None
)

# 将刚创建的窗口对应的 OpenGL 上下文设为当前上下文
# 后续 MuJoCo 的渲染操作都会使用这个 OpenGL 上下文
# “上下文”指的是 OpenGL context，可以理解成：当前线程正在使用的一整套 OpenGL 渲染环境。

# 这里再讨论一下进程、线程、GLFW、OpenGL context 这几个概念。
# `python3 mujoco_get_camera_picture.py`这会启动一个 python 进程，这个 python 进程里默认有一个 主线程，我的代码基本都跑在这个主线程里。
# glfw.init();window = glfw.create_window(...);glfw.make_context_current(window)都是在 当前 Python 进程的主线程 中执行的。
# 而 GLFW 是一个被我的 Python 进程调用的库，它的函数在调用它的线程里执行。

# 这就引出了库，在此做一个概念上的强调：库就是别人写好的代码工具箱。import glfw 就是导入一个库，通过`glfw.init()`直接调用内部的函数。
# 因为没有显式的新开一个线程，所以当我调用某个库的函数的时候，其实就是当前主线程挂起现在的工作，分配给了库内部去执行库自己的函数，比如glfw.init()

# 回到这个函数：其实就是把 window 背后关联的 OpenGL context 设置为“当前线程的当前 OpenGL context”。
# 后面所有 OpenGL/MuJoCo 渲染操作，都在 window 对应的 OpenGL 渲染环境里执行。
glfw.make_context_current(window)


# ============================================================
# 2. 加载 MuJoCo 模型
# ============================================================
# 从 XML 文件中加载 MuJoCo 模型
# scene_withcamera.xml 里面应该定义了机器人、场景、相机等内容
model = mujoco.MjModel.from_xml_path(
    '/home/ace/mujoco_models/mujoco_menagerie/franka_emika_panda/scene_withcamera.xml'
)

# 创建仿真数据对象
# model 表示静态模型结构，比如关节、body、geom、camera 等
# data 表示仿真过程中的动态状态，比如 qpos、qvel、传感器数据等
data = mujoco.MjData(model)


# ============================================================
# 3. 创建渲染相关对象
# ============================================================
# MjvScene 是 MuJoCo 可视化场景对象
# 它会保存当前要渲染的几何体、灯光、相机视角等信息
# maxgeom=10000 表示最多允许场景中有 10000 个可渲染几何体
scene = mujoco.MjvScene(model, maxgeom=10000)

# MjrContext 是 MuJoCo 的渲染上下文
# 它会管理 OpenGL 资源，比如字体、纹理、缓冲区等
# mjFONTSCALE_150 表示渲染文字时使用 150% 缩放
context = mujoco.MjrContext(
    model,
    mujoco.mjtFontScale.mjFONTSCALE_150.value
)


# ============================================================
# 4. 设置相机参数
# ============================================================
# XML 文件中定义的相机名称
camera_name = "rgb_camera"

# 根据相机名称获取 MuJoCo 中的 camera id
# 如果找不到这个相机，则返回 -1
camera_id = mujoco.mj_name2id(
    model,
    mujoco.mjtObj.mjOBJ_CAMERA,
    camera_name
)

# 创建一个可视化相机对象
# 这个对象不是 XML 中的物理相机本身，而是用于渲染视角控制的相机
camera = mujoco.MjvCamera()

# ------------------------------------------------------------
# 相机类型说明：
#
# mjCAMERA_FIXED:
#   使用 XML 文件中定义好的固定相机。
#   这种模式下 camera.fixedcamid 有效。
#
# mjCAMERA_TRACKING:
#   跟踪某个 body。
#   这种模式下 camera.trackbodyid 有效，
#   camera.distance / azimuth / elevation 会决定相机相对目标 body 的位置。
#
# 当前使用的是 TRACKING 模式。
# ------------------------------------------------------------

# 设置相机为跟踪模式
camera.type = mujoco.mjtCamera.mjCAMERA_TRACKING

if camera_id != -1:
    print("camera_id", camera_id)

    # 注意：
    # fixedcamid 只有在 camera.type = mjCAMERA_FIXED 时才真正起作用。
    # 你现在使用的是 mjCAMERA_TRACKING，
    # 所以 fixedcamid 基本不会影响最终渲染视角。
    camera.fixedcamid = camera_id

    # 如果使用 TRACKING 相机，真正重要的是 trackbodyid。
    # 你在 while 循环里面设置了 trackbodyid。
    #
    # camera.trackbodyid = mujoco.mj_name2id(
    #     model,
    #     mujoco.mjtObj.mjOBJ_BODY,
    #     "ee_center_body"
    # )


# ============================================================
# 5. 设置离屏渲染缓冲区
# ============================================================
# MjrRect 用来表示渲染区域，左下角为 (0, 0)，宽高为 resolution
framebuffer = mujoco.MjrRect(
    0,
    0,
    resolution[0],
    resolution[1]
)

# 设置 MuJoCo 当前渲染目标为离屏 framebuffer(显卡/OpenGL 里的一块“画布”或“像素缓冲区”)
# 也就是说 mjr_render 的结果不会直接画到屏幕窗口上，
# 而是画到 OpenGL 的 offscreen buffer 中
mujoco.mjr_setBuffer(
    mujoco.mjtFramebuffer.mjFB_OFFSCREEN,
    context
)


# ============================================================
# 6. 主循环：仿真 + 渲染 + 显示
# ============================================================
while True:
    # 推进 MuJoCo 仿真一步
    # 这会根据当前控制量、动力学、约束等更新 data
    mujoco.mj_step(model, data)

    # 每一帧都获取需要跟踪的 body id
    tracking_body_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        "cube"
    )

    # 设置 tracking 相机跟踪这个 body
    camera.trackbodyid = tracking_body_id

    # 设置相机距离目标 body 的距离
    # 注意：MuJoCo 中 distance 通常应该是正数。
    # 你这里设置成 -0.15，可能会导致视角异常或反向。
    # 一般建议使用正数，例如 0.15、0.3、0.5。
    camera.distance = 0.5

    # 设置相机水平旋转角，单位是度
    # 0 表示默认方位
    camera.azimuth = 0

    # 设置相机俯仰角，单位是度
    # -90 通常表示从上往下看，类似俯视视角
    camera.elevation = -90

    # 定义当前帧的渲染视口(就是渲染结果要画到哪里、画多大的一块矩形区域。)
    # 这里视口大小和图像分辨率一致
    viewport = mujoco.MjrRect(
        0,
        0,
        resolution[0],
        resolution[1]
    )

    # 更新 MuJoCo 可视化场景
    # 这一步会根据当前 model、data 和 camera
    # 生成当前时刻应该被渲染出来的几何体、灯光、相机视角等信息
    mujoco.mjv_updateScene(
        model,                       # MuJoCo 模型
        data,                        # 当前仿真状态
        mujoco.MjvOption(),          # 可视化选项，比如是否显示接触点、坐标轴等
        mujoco.MjvPerturb(),         # 鼠标扰动相关对象，这里不使用
        camera,                      # 当前使用的可视化相机
        mujoco.mjtCatBit.mjCAT_ALL,  # 渲染所有类别的对象
        scene                        # 输出到 scene
    )

    # 使用 MuJoCo 渲染器把 scene 渲染到当前 framebuffer
    # 因为前面设置了 mjFB_OFFSCREEN，所以这里是离屏渲染
    mujoco.mjr_render(
        viewport,
        scene,
        context
    )

    # 创建一个空的 RGB 图像数组，用于接收 MuJoCo 渲染结果
    # 注意形状是 height x width x 3
    rgb = np.zeros(
        (resolution[1], resolution[0], 3),
        dtype=np.uint8
    )

    # 从 MuJoCo/OpenGL framebuffer 中读取像素
    # 第一个参数读取 RGB 图像
    # 第二个参数可以读取 depth，这里传 None 表示不读取深度图
    mujoco.mjr_readPixels(
        rgb,
        None,
        viewport,
        context
    )

    # OpenGL 图像坐标原点通常在左下角，
    # 而 OpenCV 图像坐标原点在左上角，
    # 所以需要 np.flipud(rgb) 上下翻转图像。
    #
    # MuJoCo 读出来的是 RGB 格式，
    # OpenCV 默认使用 BGR 格式，
    # 所以还需要从 RGB 转成 BGR。
    bgr = cv2.cvtColor(
        np.flipud(rgb),
        cv2.COLOR_RGB2BGR
    )

    # 使用 OpenCV 显示渲染画面
    cv2.imshow('MuJoCo Camera Output', bgr)

    # 等待 1 ms 检查键盘输入
    # 如果按下 ESC 键，也就是 key code 27，则退出循环
    if cv2.waitKey(1) == 27:
        break


# ============================================================
# 7. 保存最后一帧并释放资源
# ============================================================
# 保存最后一帧图像到文件
cv2.imwrite('debug_output.png', bgr)

# 关闭所有 OpenCV 窗口
cv2.destroyAllWindows()

# 终止 GLFW，释放窗口和 OpenGL 上下文相关资源
glfw.terminate()

# 删除 MuJoCo 渲染上下文和场景对象
# 这一步不是绝对必须，但显式释放资源是好习惯
del context
del scene