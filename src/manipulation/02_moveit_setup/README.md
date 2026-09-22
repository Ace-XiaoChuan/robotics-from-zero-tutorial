# 模型与 MoveIt 配置

本文行数：19行，预期阅读时长：1分钟

## 速记要点

URDF 描述结构，SRDF 描述规划语义；运动学求解配置、关节限制、MoveIt 控制器映射和 ros2_control 配置共同提供案例运行所需的信息。

## 例子

Panda 的 `panda.urdf.xacro` 引用了 `moveit_resources_panda_description`；`panda.srdf` 保存语义配置。

## 结果与解释

这是文件依赖关系：本仓库保留小型配置，但未打包被引用的机器人模型描述包。配置文件存在不表示环境完整。

[对应源码或配置](../packages/panda_moveit_config/config)。本页依据仓库已有材料整理，未进行 ROS 构建或运行验证。

[返回 MoveIt 目录](../README.md)
