# MoveGroupInterface 与笛卡尔路径

本文行数：21行，预期阅读时长：1分钟

## 速记要点

先指定规划组，再设置目标，检查规划结果，最后请求执行。位姿的位置单位为米，姿态使用四元数；必须确认目标所用参考坐标系。

## 例子

`hello_moveit.cpp` 使用 `panda_arm`；目标位置为 (0.1, 0.4, 0.4) m，四元数按 (x,y,z,w) 为 (0,0.8,0,0.6)。

## 结果与解释

这些数值取自源码，四元数模长为 1。Pose 本身没有 frame_id，阅读目标时还要核对接口的参考坐标系，不能仅凭数值判断世界位置。

[对应源码或配置](../packages/hello_moveit/src/hello_moveit.cpp)。本页依据仓库已有材料整理，未进行 ROS 构建或运行验证。

[原始日志与详细笔记](history.md) · [直线与圆形源码](../packages/hello_moveit/src/draw_line_and_circle.cpp)

[返回 MoveIt 目录](../README.md)
