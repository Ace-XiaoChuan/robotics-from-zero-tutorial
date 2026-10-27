# 09：怎样观察仿真：窗口、相机与传感器

本文行数：82行，预期阅读时长：5分钟

**物理步进、控制更新和画面刷新是三件事；没有窗口也能完成仿真计算。**

## 开发者理解：同一状态有不同的观察方式

查看窗口适合观察运动与接触，读取状态适合精确比较数字，相机与传感器输出适合构造算法的观测。三者都需要先明确使用哪份 data、哪个参考系，以及数据对应的仿真时刻。

| 观察方式 | 得到什么 | 例子 |
| --- | --- | --- |
| 读取状态与派生量 | 关节状态、site 位姿等数值 | 末端世界坐标 `(x,y,z)` |
| Viewer | 给人看的交互画面 | 转动视角检查关节轴与接触 |
| Renderer | 指定相机生成的图像数组 | 视觉算法使用的 RGB 图像 |
| sensor | 按模型定义计算的命名读数 | jointpos、jointvel、framepos |

读取模型状态可以直接拿到仿真内部信息；真实机器人上可能需要编码器、视觉或估计算法才能得到相应量。构造学习策略的观测时，要明确是否使用了这些内部信息，以及是否另外加入噪声与延迟。

## 速记

- `mj_step` 推进物理状态；Viewer 显示状态，不代替物理积分。
- `mujoco.viewer.launch_passive(model, data)` 由你的程序负责步进，`viewer.sync()` 同步显示与交互状态。
- `mujoco.Renderer` 用于生成图像；相机图像需要有效的渲染后端，无窗口数值检查则不需要。
- 仿真时间是 `data.time`；墙钟时间是电脑实际经过的时间。`sleep()` 只影响后者。

## 例子：显示为什么可以比物理计算慢

本例每个物理步为 `2 ms`，每 20 步同步画面，即每仿真秒显示约 25 次，中间还有未显示的物理状态。完整的物理、控制与显示频率关系见[第五章](../05_state_step/README.md)。

若要接近实时播放，可按墙钟计时，仅在提前完成时等待剩余时间；算得太慢时不能靠负数等待追回，也不能把“窗口流畅”当成控制周期达标的证据。

## 例子：qpos 在变，窗口却没动

**排查顺序：** 是否步进了正在显示的那份 data → 是否调用 `sync()` → 初始化改 `qpos` 后是否更新派生量 → 相机是否对准模型。

若与 Viewer 线程共同修改 model/data，按官方用法使用 `viewer.lock()` 保护共享访问；窗口交互也可能改变运行状态，因此固定条件的重复性检查应先无窗口完成。

渲染图像的典型流程是 `renderer.update_scene(data)` 后 `renderer.render()`，返回 RGB 图像数组。它不是相机位姿估计算法；相机坐标与视觉测量留到 [S6](../../../doc/learning-roadmap.md#s6)。

综合机械臂脚本按这个节拍同步画面。数值复核无窗口；渲染与 Viewer 的实际验证情况见[验证记录](../mujoco/verification.md)。

## 场景相机与观察者视角

Viewer 的自由相机用于交互观察；MJCF 中命名的 camera 可以固定在世界，也可以安装在机器人 body 上。改相机视角不会改变机器人状态。

本例 `overview` 相机固定在世界坐标 `(0.35,-1.2,1.2) m`。MuJoCo 相机局部 `-z` 指向视线前方、`+y` 朝图像上方；这与常见视觉光学系的 `+z` 向前、`+y` 向下不同。做外参或图像投影时需要显式转换约定，见[相机章节](../../perception/01_camera_calibration/README.md)。

相机的 `pos/quat` 是模型中的安装关系；body 运动后，世界相机位姿随之更新。一个安装在手腕上的相机不能直接把局部安装偏移当作世界位姿。

## 例子：从固定相机读取 RGB

以下假设已经加载机械臂场景，并更新了当前状态的派生量：

```python
with mujoco.Renderer(model, height=240, width=320) as renderer:
    renderer.update_scene(data, camera="overview")
    rgb = renderer.render().copy()
```

普通 RGB 模式输出形状为 `(240,320,3)` 的数组。这里图像内容对应 update_scene 时的数据；机器人继续运动后，旧图像不会自动变成新帧。需要保存历史图像时，在每个采样时刻重新更新并保留副本。

离屏渲染不需要弹出窗口，但仍依赖可用的图形后端。在 Linux 上，EGL 常用于无显示器渲染，OSMesa 可用于软件渲染；实际可用性取决于本机驱动与库。`MUJOCO_GL` 需在导入 MuJoCo 前选择，不能把后端错误与无窗口物理计算失败混为一谈。

## 例子：sensor 读数怎样对应模型状态

[机械臂模型](../mujoco/models/planar_arm.xml)定义两个 jointpos、两个 jointvel 和一个 tip 的 framepos。共有 5 个传感器、7 个标量输出：`1+1+1+1+3`。

```python
q = data.sensor("shoulder_position").data.copy()  # 长度 1，rad
tip_world = data.sensor("tip_position").data.copy()  # 长度 3，m
```

把关节设为 `[0.5,-0.8] rad` 并调用 forward 后，shoulder_position 为 `[0.5]`，tip_position 约为 `[0.637634,0.103114,0.3] m`，与 `data.site("tip").xpos` 一致。这是命名传感器与派生量的对应核对，不是额外运行了视觉估计。

未配置参考对象的 framepos 使用世界坐标。不同传感器的 frame、维度、物理含义和计算阶段不同，不能把所有 sensordata 都当作世界位置。force/torque 传感器与加速度计也各有定义，应按具体 sensor 查阅。

本例没有添加测量噪声、掉帧或通信延迟；sensor 名称本身不意味着已经模拟这些因素。要比较理想状态与有误差的测量，可复用[感知误差](../../perception/03_measurement_errors/README.md)和[时间对齐](../../perception/06_time_alignment/README.md)中的方法。

资料：[Python Viewer 与渲染](https://mujoco.readthedocs.io/en/3.13.0/python.html) · [sensor 定义](https://mujoco.readthedocs.io/en/3.13.0/XMLreference.html#sensor)

[上一章：接触与约束](../08_contact_constraints/README.md) · [返回目录](../README.md) · [下一章：重置与记录](../10_reset_recording/README.md)
