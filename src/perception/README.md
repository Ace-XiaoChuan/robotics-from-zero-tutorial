# S6：感知与估计

本文行数：31行，预期阅读时长：3分钟

**把图像和传感器读数转换为有坐标、时间和误差说明的任务状态。六章采用“速记要点 + 例子 + 结果与解释”，无需运行代码即可复习。**

| 章节 | 要回答的问题 |
| --- | --- |
| [01 相机成像与标定](01_camera_calibration/README.md) | 三维点怎样投影到像素，内参、畸变与图像尺寸怎样对应？ |
| [02 目标位姿与坐标转换](02_pose_transforms/README.md) | AprilTag / PnP 的位姿怎样变到基座系，抓取点与标记原点有什么关系？ |
| [03 测量噪声、偏差与有效性](03_measurement_errors/README.md) | 稳定读数为什么也会偏，缺测与异常值怎样表达？ |
| [04 误差传播与位姿评价](04_uncertainty_propagation/README.md) | 像素、深度和外参误差怎样影响空间定位？ |
| [05 滤波与 Kalman 状态估计](05_filtering_kalman/README.md) | 怎样权衡平滑与滞后，只测位置为何也能修正速度？ |
| [06 多传感器时间对齐与任务状态](06_time_alignment/README.md) | 图像、关节状态和 TF 怎样对应同一时刻，什么状态可供规划使用？ |

前两章回顾“图像 → 相机系目标 → 基座系目标”；第三、四章解释误差；第五章补充历史状态与运动模型；第六章把坐标、时间和有效性接成任务接口。可直接跳到需要复习的章节。

## 统一约定与先修

`T_A_B` 把 B 系坐标变到 A 系；长度默认 m、时间 s、角度 rad，像素为 px。相机光学系 C 为 x 向右、y 向下、z 向前；机器人基座与安装方向由实际模型定义。统计与 Kalman 例子采用固定坐标轴上的一维位置，状态扩展时顺序为 `[位置,速度]ᵀ`。

坐标变换、旋转误差和 Jacobian 可按需复习[空间数学](../foundations/spatial_math/README.md)；机器人 FK 见[运动学](../kinematics/README.md)；TF 与时钟见 [ROS 2](../ros2/README.md)。

## 案例与数值例子

- [相机、传感器与 AprilTag 案例](examples/camera_and_tags/README.md)：原 Lesson 8；[实现笔记](examples/camera_and_tags/cv_trainning/README.md)保留原实现和运行记录入口。
- [相机标定源码](examples/camera_and_tags/cv_trainning/camera_calibration.py)、[AprilTag 位姿源码](examples/camera_and_tags/cv_trainning/get_apriltag_pos.py)、[传感器读取源码](examples/camera_and_tags/cv_trainning/sensordata.py)。
- [数值核对记录](verification.md)与[检查脚本](check_examples.py)：12 项教学数值检查通过，包括投影、变换、误差传播、Kalman 更新与时间算例。
- 相机案例依赖 XML 场景与外部 viewer / PnP 模块，源码仍使用旧 `src.*` 导入；运行前按案例说明核对包名与接口。上面的 12 项检查未运行图像、PnP 或综合采集链路。

[学习路线 S6](../../doc/learning-roadmap.md#s6) · [总目录](../README.md) · [后续：规划与操作](../manipulation/README.md) · [数据采集](../data_collection/README.md)
