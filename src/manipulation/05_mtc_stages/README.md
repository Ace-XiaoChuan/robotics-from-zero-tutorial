# MTC 阶段与任务解

本文行数：19行，预期阅读时长：1分钟

## 速记要点

任务用 stage 表达阶段；属性决定规划组与末端等上下文。初始化、规划和执行是三个检查位置。

## 例子

`mtc_node.cpp` 从 CurrentState 开始添加阶段；初始化捕获 `InitStageException`，完整抓放实现还可查 `hello_moveit/src/pick_and_place.cpp`。

## 结果与解释

这是源码导读：初始化失败先查阶段属性和配置；阶段可初始化也不代表存在完整任务解。不要把各阶段孤立可行等同于整体连接可行。

[对应源码或配置](../packages/mtc_tutorial/src/mtc_node.cpp)。本页依据仓库已有材料整理，未进行 ROS 构建或运行验证。

[返回 MoveIt 目录](../README.md)
