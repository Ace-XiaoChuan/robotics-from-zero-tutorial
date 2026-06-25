# Lesson 11：MuJoCo 视觉感知与传感器数据

本 lesson 记录 MuJoCo 仿真中相机图像、AprilTag、SolvePnP 位姿估计和 `SensorData` 读取相关实践。重点不是深入展开计算机视觉算法，而是把机器人任务中常用的数据链路跑通：

```text
仿真图像 -> 相机内参 -> AprilTag 检测 -> 位姿估计 -> 状态对齐 -> episode 保存
```

## 目录

| 路径 | 内容 |
| --- | --- |
| [`cv_trainning/`](cv_trainning/) | MuJoCo 相机、AprilTag、相机标定、传感器读取和 episode 保存脚本。 |
| [`cv_trainning/README.md`](cv_trainning/README.md) | 本 lesson 的详细学习笔记、运行前提、推荐学习顺序和常见问题。 |
| [`cv_trainning/demo/sim_camera_tag_pose_demo.py`](cv_trainning/demo/sim_camera_tag_pose_demo.py) | 同步保存 RGB、关节状态、末端位姿、目标位姿、动作和时间戳的综合 Demo。 |

> 目录名 `cv_trainning` 沿用当前仓库中的已有拼写。后续如果统一改名为 `cv_training`，需要同步更新 README 中的运行命令和脚本路径。

## 建议阅读顺序

1. 先读 [`cv_trainning/README.md`](cv_trainning/README.md)，确认依赖、路径和整体数据链路。
2. 运行 `mujoco_get_camera_picture.py`，确认 MuJoCo 相机能稳定出图。
3. 运行 `camera_calibration.py`，理解虚拟相机内参与 OpenCV 标定结果。
4. 运行 `apriltag.py` 和 `get_apriltag_pos.py`，完成 tag 检测与 `solvePnP` 位姿估计。
5. 运行 `sensordata.py`，掌握按 sensor name 读取 `data.sensordata`。
6. 最后运行综合 Demo，检查保存的 `.npz` episode 是否满足时间步连续、数组长度一致、坐标系清楚和单位统一。
