# 动力学、轨迹与控制

本文行数：30行，预期阅读时长：2分钟

本主题对应学习路线 S5。下面只规划下一层章节，正文均待编写；暂不创建空章节目录或占位链接。

## 章节目录（待编写）

1. 单关节动力学：惯性、重力、阻尼与力矩
2. 多关节动力学：动力学方程与关节耦合
3. 正动力学与逆动力学
4. 运动轨迹：插值、时间参数化与速度加速度约束
5. 反馈控制：位置、速度、力矩接口与 P / PD / PID
6. 前馈控制与重力补偿
7. 关节空间与末端轨迹跟踪
8. 离散控制：采样、饱和、噪声、延迟与扰动

## 已有材料

本主题复用已有完整仿真案例，源码只维护一份。以下材料供查阅，不表示上述章节已经编写完成。

| 查阅问题 | 已有材料 |
| --- | --- |
| PID 与关节轨迹跟踪 | [原 Lesson 7 笔记](../simulation/mujoco/examples/state_and_control/README.md) · [轨迹源码](../simulation/mujoco/examples/state_and_control/joint_space_trajectory_tracking_demo.py) |
| 末端误差与控制 | [位姿误差笔记](../kinematics/examples/model_alignment/lie_group_lie_algebra_notes.md) · [末端控制源码](../kinematics/examples/model_alignment/control_ee_with_pinocchio.py) |
| 外加关节力旧探索 | [旧脚本](../simulation/mujoco/legacy/run_sim.py) · [限制说明](../simulation/mujoco/materials.md) |

阅读时区分直接设置 qpos、执行器 ctrl 与 qfrc_applied；它们对应的验证结论不同。动态控制表现未因目录迁移得到验证。

[学习路线 S5](../../doc/learning-roadmap.md#s5) · [总目录](../README.md)
