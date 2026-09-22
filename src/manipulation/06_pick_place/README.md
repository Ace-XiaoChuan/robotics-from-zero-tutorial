# 抓放案例与源码组织

本文行数：21行，预期阅读时长：1分钟

## 速记要点

抓放过程需要同时管理机器人运动、手爪和场景中的物体关系。对照接近、闭合、附着、抬升、放置和释放的顺序阅读。

## 例子

`hello_moveit/src/pick_and_place.cpp` 中有 approach object、close hand、attach object 和 lift object 等阶段；原 Lesson 6 的桌面抓放实现也一并保留。

## 结果与解释

这里列的是阶段结构，不是本次成功率或运行结论。桌面案例与迁入案例分别保留，避免把不同实现误当成重复文件删除。

[对应源码或配置](../packages/hello_moveit/src/pick_and_place.cpp)。本页依据仓库已有材料整理，未进行 ROS 构建或运行验证。

[桌面抓放源码](../packages/mtc_week3_demo/src/desktop_pick_place.cpp) · [原运行记录与视频](history.md) · [分层应用案例](../packages/mtc_advanced_demo/src)

[返回 MoveIt 目录](../README.md)
