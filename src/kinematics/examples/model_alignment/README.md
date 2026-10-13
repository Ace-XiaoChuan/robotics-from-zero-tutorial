# 模型对齐与末端控制案例

本文行数：15行，预期阅读时长：1分钟

本案例比较 MuJoCo、Pinocchio 与 KDL 的运动学结果，并提供末端控制和位姿误差说明。

- [FK 对齐源码](check_fk_with_mujoco.py)
- [雅可比与 qpos 笔记](qpos_jacobian_notes.md)
- [位姿误差与李群笔记](lie_group_lie_algebra_notes.md)
- [末端控制源码](control_ee_with_pinocchio.py)
- [综合检查源码](kinematics_milestone.py)

FK 对比脚本查询 `link7`；CLIK 与综合检查查询 `ee_center_body`，两种工具点不能直接混作同一个输出比较。CLIK 已实现局部位姿误差、阻尼迭代与执行器目标下发，但执行器不足时仍会直接写 `qpos`。

运行依赖外部 XML / URDF、MuJoCo、Pinocchio；FK 对比还依赖外部 `mujoco_learning` 的 Viewer 与 KDL 包装器。模型路径在脚本中配置；当前[平面模型数值记录](../../verification.md)没有覆盖这些 Panda 联合仿真与控制脚本。[运动学目录](../../README.md)。
