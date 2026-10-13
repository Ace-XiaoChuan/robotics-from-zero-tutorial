# 数据采集与回放

本文行数：11行，预期阅读时长：1分钟

[相机与位姿采集程序](../perception/examples/camera_and_tags/cv_trainning/demo/sim_camera_tag_pose_demo.py)实现压缩 NPZ 保存，包含 RGB、完整模型的广义位置与速度、末端和物体的世界系仿真真值、动作及仿真时间戳。物体位姿直接读取 MuJoCo，没有调用 AprilTag / PnP 估计。代码与[案例说明](../perception/examples/camera_and_tags/cv_trainning/README.md)一起维护。

本例 `action` 是写入 `ctrl[:7]` 的七维绝对关节位置目标（rad），按 `1 s` 线性轨迹生成。同一次回调先读取当前状态，再下发动作，没有单独保存动作后的下一观测；图像与状态的实际时间一致性仍需结合外部 Viewer 核对。NPZ 还保存默认构型、初速度、轨迹起点与终点、持续时间，字段区别见案例说明。

采集脚本仍依赖旧 `src.mujoco_viewer` 接口，当前外部包名为 `mujoco_learning`，尚未完成接口适配和端到端运行验证。完整回放与机器人行为克隆闭环案例尚待实现。数据格式和策略衔接见[学习路线 S8 / S9](../../doc/learning-roadmap.md#s8)。

[总目录](../README.md)
