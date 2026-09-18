# Lesson 8：MuJoCo 视觉、AprilTag 与传感器数据采集

本文行数：245行，预期阅读时长：7分钟

本目录记录 MuJoCo 仿真中的相机、AprilTag 和传感器数据读取实践。这里的目标不是深入研究计算机视觉算法本身，而是掌握机器人任务中最常用的一条工程链路：

```text
仿真相机图像
  -> 相机内参
  -> AprilTag 检测
  -> SolvePnP 位姿估计
  -> MuJoCo 真值 / SensorData 对齐
  -> 保存成可用于控制或模仿学习的数据
```

重点是把数据拿准、坐标系想清楚、时间步对齐，而不是陷入渲染管线或真实相机标定的细枝末节。

## 目录内容

| 文件 | 作用 |
| --- | --- |
| `mujoco_get_camera_picture.py` | 使用 MuJoCo 离屏渲染，从仿真相机读取 RGB 图像并用 OpenCV 显示 / 保存。 |
| `camera_calibration.py` | 在仿真中移动棋盘格，采集角点，调用 OpenCV 完成相机标定，并与 MuJoCo `fovy` 推导出的理论内参对比。 |
| `apriltag.py` | 从 MuJoCo 相机图像中检测 AprilTag，输出 tag id 和中心点像素坐标。 |
| `get_apriltag_pos.py` | 结合 AprilTag 角点、相机内参和 `solvePnP`，估计 AprilTag 相对于相机的位姿。 |
| `sensordata.py` | 按传感器名称读取 MuJoCo `data.sensordata` 中的指定数据，并和 `qvel` 等仿真状态做对比。 |
| `demo/sim_camera_tag_pose_demo.py` | 综合 Demo：机械臂运动时同步采集 RGB、关节状态、末端位姿、物体位姿、动作和时间戳，并保存为 `.npz` episode。 |

## 运行前提

这些脚本依赖 MuJoCo、OpenCV 和项目中的自定义 viewer 工具。运行前请先确认：

- 已安装常用依赖：`mujoco`、`opencv-python`、`numpy`、`glfw`、`pynput`、`pupil-apriltags`。
- 本机存在 MuJoCo XML 场景文件，例如 `scene_withcamera.xml`、`scene_with_checkerboard.xml`、`scene_with_apriltag.xml`、`scene_pos.xml`。
- 脚本中引用的本地路径符合你的机器，例如：
  - `/home/ace/litchi_tutorial/mujoco-learning`
  - `/home/ace/mujoco_models/mujoco_menagerie/franka_emika_panda`
- `src.mujoco_viewer`、`src.key_listener`、`src.solvepnp`、`src.matplot` 等自定义模块可以被 Python 找到。

如果运行时报 `No such file or directory` 或 `ModuleNotFoundError`，优先检查 XML 路径和 `sys.path` 中的项目根目录。

## 推荐学习顺序

### 1. 先确认相机能出图

从 `mujoco_get_camera_picture.py` 开始。这个脚本展示了 MuJoCo 离屏渲染的基本流程：

1. 用 GLFW 创建 OpenGL 上下文。
2. 加载 MuJoCo XML 模型。
3. 创建 `MjvScene` 和 `MjrContext`。
4. 选择相机视角。
5. 调用 `mjr_render` 渲染画面。
6. 调用 `mjr_readPixels` 读取像素。
7. 将 MuJoCo / OpenGL 图像转成 OpenCV 可显示的格式。

需要注意两个常见坐标 /颜色格式问题：

- OpenGL 图像原点在左下角，OpenCV 图像原点在左上角，所以通常需要 `np.flipud`。
- MuJoCo 读出的图像常按 RGB 理解，OpenCV 默认按 BGR 显示，所以需要 `cv2.cvtColor`。

运行示例：

```bash
python3 src/lesson8/cv_trainning/mujoco_get_camera_picture.py
```

按 `Esc` 退出后，脚本会保存最后一帧到 `debug_output.png`。

### 2. 理解相机内参

`camera_calibration.py` 用棋盘格做 OpenCV 标定，同时打印 MuJoCo 虚拟相机由 `fovy` 计算出的理论内参。

针孔相机内参矩阵为：

$$
K =
\begin{bmatrix}
f_x & 0 & c_x \\
0 & f_y & c_y \\
0 & 0 & 1
\end{bmatrix}
$$

其中：

- `fx, fy`：像素单位下的焦距。
- `cx, cy`：主点坐标，理想情况下接近图像中心。
- MuJoCo 虚拟相机通常可以先按无畸变模型处理。

MuJoCo 相机的 `fovy` 是竖直方向视场角。对于图像高度 `H`，竖直方向焦距可由下面公式估算：

$$
f_y = \frac{0.5H}{\tan(\mathrm{rad}(fovy) / 2)}
$$

如果假设像素是正方形，可以先令 `fx = fy`，再把主点放在图像中心：

```python
K = np.array([
    [f, 0, width / 2],
    [0, f, height / 2],
    [0, 0, 1],
], dtype=np.float32)
```

脚本交互方式：

- 方向键：移动棋盘格的 `x / z` 坐标。
- `PageUp / PageDown`：移动棋盘格的 `y` 坐标。
- 空格：采集一张能检测到完整角点的标定图。
- 回车：执行相机标定。

建议至少采集 5 张不同位置和角度的棋盘格图像，再执行标定。

### 3. 检测 AprilTag

`apriltag.py` 负责验证相机画面中是否能稳定识别 AprilTag。

它的核心流程是：

1. 从固定相机读取图像。
2. 转成灰度图。
3. 使用 `pupil_apriltags.Detector` 检测 tag。
4. 打印 `tag_id` 和中心点像素坐标。

需要保证 XML 场景中已经放置了 AprilTag 纹理或带 tag 的平面，并且相机能看见它。检测失败时，优先检查：

- tag 是否在画面内。
- tag 是否太小、太斜或被遮挡。
- 检测器的 `families` 是否和 tag 图片一致，例如 `tag36h11`。
- 图像颜色转换是否和 viewer 返回的 RGB / BGR 格式匹配。

### 4. 用 SolvePnP 求 AprilTag 位姿

`get_apriltag_pos.py` 在 AprilTag 检测的基础上进一步估计位姿。

`solvePnP` 的输入可以理解成四组信息：

- AprilTag 四个角点在 tag 自身坐标系下的 3D 坐标。
- 图像中检测到的四个角点 2D 像素坐标。
- 相机内参矩阵 `K`。
- 畸变参数 `dist_coeffs`。

输出通常是：

- `rvec`：旋转向量。
- `tvec`：平移向量，即 tag 相对相机坐标系的位置。
- 进一步可转成 4x4 齐次变换矩阵，方便和机器人位姿链路对接。

这个脚本里 AprilTag 的尺寸设为 `0.1 m`，如果 XML 中实际 tag 尺寸不同，需要同步修改，否则 `tvec` 的尺度会错。

### 5. 读取 SensorData

`sensordata.py` 展示了按名称读取 MuJoCo 传感器数据的方式：

```python
sensor_id = self.model.sensor(sensor_name).id
sensor_dim = self.model.sensor(sensor_name).dim[0]
adr = self.model.sensor_adr[sensor_id]
sensor_values = self.data.sensordata[adr:adr + sensor_dim]
```

理解这个切片逻辑很重要。MuJoCo 会把 XML 中定义的所有 sensor 数据按顺序拼接到一维数组 `data.sensordata` 中，因此读取某个传感器时必须知道：

- 传感器名称。
- 传感器 id。
- 数据起始地址 `sensor_adr`。
- 数据维度 `sensor_dim`。

在模仿学习和控制任务中，低维状态通常比图像更直接、更稳定，例如：

- 关节位置 `qpos`。
- 关节速度 `qvel`。
- 末端位置 / 姿态。
- 力 / 力矩。
- 接触或触觉信号。

所以本目录里最需要牢固掌握的不是“能不能识别 tag”，而是“能不能把图像、状态、动作和时间戳可靠地对齐保存”。

## 综合 Demo：保存一段 Episode

`demo/sim_camera_tag_pose_demo.py` 是这个目录最接近数据采集闭环的脚本。它会在机械臂运动过程中同步保存：

- `rgb`：相机图像。
- `qpos`：关节位置。
- `qvel`：关节速度。
- `eef_pos`：末端位置。
- `eef_quat`：末端姿态四元数。
- `object_pos`：AprilTag / 目标物体位置。
- `object_quat`：目标物体姿态四元数。
- `action`：当前下发的关节目标。
- `timestamp`：MuJoCo 仿真时间。

退出仿真后，数据会保存为压缩 `.npz` 文件。这个文件结构更接近后续模仿学习、轨迹回放或离线分析需要的数据格式。

运行示例：

```bash
python3 src/lesson8/cv_trainning/demo/sim_camera_tag_pose_demo.py
```

## 阶段验收标准

完成本目录后，至少应能独立做到：

- 从 MuJoCo 相机稳定获取图像，并知道 RGB / BGR、上下翻转这些格式问题来自哪里。
- 根据 `fovy` 和图像尺寸推导虚拟相机内参。
- 用棋盘格标定相机，并理解 OpenCV 标定结果与 MuJoCo 理论内参为什么可能有差异。
- 在仿真图像中检测 AprilTag，读取 tag id、中心点和角点。
- 用 `solvePnP` 根据 AprilTag 角点估计相机坐标系下的相对位姿。
- 按名称从 `data.sensordata` 中读取指定 sensor 的数据。
- 同步保存图像、关节状态、末端位姿、目标物体位姿、动作和时间戳。
- 对保存的数据做基本 sanity check：时间步连续、数组长度一致、坐标系定义明确、单位统一。

## 常见问题

### 1. 图像显示出来是倒的

MuJoCo / OpenGL 和 OpenCV 的图像坐标原点不同，读取 framebuffer 后通常需要上下翻转：

```python
rgb = np.flipud(rgb)
```

### 2. 图像颜色不对

OpenCV 默认使用 BGR，而很多渲染接口更自然地按 RGB 理解。显示或保存前确认是否需要：

```python
bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
```

### 3. AprilTag 检测不到

先不要急着改算法。优先确认相机图像中 tag 是否清晰可见，然后再检查 tag family、光照、角度、尺寸和灰度转换。

### 4. SolvePnP 位置尺度明显不对

通常是 tag 真实尺寸写错了。`TAG_SIZE` 必须和 XML 场景中 AprilTag 的实际边长一致。

### 5. SensorData 读取出来和预期不一致

检查 XML 中 sensor 的定义顺序、名称、维度，以及读取时使用的 `sensor_adr`。不要手写固定下标，优先按 sensor name 查询。


