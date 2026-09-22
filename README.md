# Robotics From Zero Tutorial

本文行数：83行，预期阅读时长：5分钟

这个仓库集中保存个人机器人工程教程、复习笔记与源码，包括 MoveIt、MuJoCo 和机器学习。主要用于快速阅览已学内容：先看要点、例子和结果解释，需要时再查实现；不要求配齐运行环境或重做实验。当前主线是机械臂的建模、感知、规划、控制与仿真，后续扩展到数据采集和模仿学习。

仓库定位是个人学习记录：笔记以快速复习为主，用例子、结果和解释帮助找回印象；代码供需要实现或复现时参考。

## 从哪里开始

- **按顺序学习**：[学习路线](doc/learning-roadmap.md)，按能力与先修关系推进，不限定周数。
- **按问题查阅**：[知识索引](doc/README.md)，直接进入需要的专题。
- **查看总体架构与代码位置**：[总体目录与案例索引](src/README.md)，查看按主题整理后的实际目录与源码位置。
- **整理新的笔记**：[文档样板](doc/lesson-template.md)，参考 [Lesson 1](src/ros2/examples/communication/README.md) 的完整示例。
- **复习 MoveIt**：[六章目录](src/manipulation/README.md)。
- **复习机器学习**：[七章目录](src/machine_learning/README.md)。
- **复习 ROS 2**：[章节目录](src/ros2/README.md)，按节点接口、启动配置、通信执行、TF 与记录排错查阅。
- **复习模型与仿真 S3**：[七章目录](src/simulation/README.md)，从仿真与真机的控制流、带时间的轨迹，到机器人结构与 MuJoCo 状态、输入、步进和重置。
- **快速回忆工程基础**：[S0 · 单元 01：终端、路径与环境](src/foundations/engineering/01_shell_paths/README.md)。

## 学习主线

工程基础 → [空间数学与数值方法](src/foundations/spatial_math/README.md) → ROS 2 与模型仿真 → [运动学八章](src/kinematics/README.md) → [动力学、轨迹与控制](src/control/README.md) → 感知与状态估计 → 规划与操作 → 数据采集 → 模仿学习。

详细路线区分必修、可交替学习的内容和选修分支。阶段里程碑是：

1. 环境、坐标和通信可复现。
2. 机械臂通过执行器控制到达目标，并记录误差。
3. 从感知到规划、控制和抓放形成完整任务。
4. 按需要继续完成示教、行为克隆和策略评估。

## 历史案例对照

日常从 [主题目录](src/README.md) 查阅。下面保留 Lesson 编号与实际位置的对照，不代表推荐学习顺序。

| Lesson | 主题 | 入口 |
| --- | --- | --- |
| Lesson 1 | ROS 2 接口与通信 Demo | [课程入口与运行说明](src/ros2/examples/communication/README.md) · [详细知识笔记](src/ros2/examples/communication/ros2_interfaces_notes.md) |
| Lesson 2 | ROS 2 Component / composition | [`src/ros2/examples/composition/lesson2_composition`](src/ros2/examples/composition/lesson2_composition) |
| Lesson 3 | 旋转矩阵、齐次变换与点变换 | [`src/foundations/spatial_math/examples/rigid_transforms`](src/foundations/spatial_math/examples/rigid_transforms) |
| Lesson 4 | Modified DH 运动学实践 | [`src/kinematics/02_dh_conventions`](src/kinematics/02_dh_conventions) |
| Lesson 5 | MoveIt 基础绘制与规划练习 | [`src/manipulation/03_move_group_interface`](src/manipulation/03_move_group_interface) |
| Lesson 6 | MoveIt Task Constructor 实践 | [`src/manipulation/06_pick_place`](src/manipulation/06_pick_place) |
| Lesson 7 | MuJoCo / MJCF 基础与轨迹跟踪 | [`src/simulation/mujoco/examples/state_and_control`](src/simulation/mujoco/examples/state_and_control) |
| Lesson 8 | MuJoCo 相机、传感器与 AprilTag | [`src/perception/examples/camera_and_tags`](src/perception/examples/camera_and_tags) |
| Lesson 9 | MuJoCo / Pinocchio / KDL 正逆运动学与末端控制 | [`src/kinematics/examples/model_alignment`](src/kinematics/examples/model_alignment) |

## 文档

| 文档 | 内容 |
| --- | --- |
| [知识索引](doc/README.md) | 按主题查阅已整理的 lesson 知识点。 |
| [Lesson 文档样板](doc/lesson-template.md) | 课程入口、专题笔记模板和写作约定；以 Lesson 1 为完整示例。 |
| [学习路线](doc/learning-roadmap.md) | 10 个能力阶段、先修关系、实验验收、近期顺序与选修方向。 |
| [总体目录与案例索引](src/README.md) | 按主题整理的实际目录、源码位置与维护规则。 |
| [协作约定](AGENTS.md) | 用户授权、学习笔记定位与代码验证规则。 |

## 当前进度

已有通信、空间变换、运动学、规划、控制、视觉和数据保存相关代码。Lesson 1 已完成详细文档整理；Lesson 7、8 有较长说明，Lesson 9 有运动学专题笔记。

S0 单元 01～06 已提供工程、Git、Python 数值、C++ 构建、调试和实验复现的直接阅读材料。S3 已整理[模型与仿真七章](src/simulation/README.md)，首章解释控制流与轨迹时间；自带小模型此前通过无窗口数值检查，验证范围见[记录](src/simulation/mujoco/verification.md)。MoveIt / MTC 教程与包已收录到 [规划与操作](src/manipulation/README.md)，七组机器学习教程与源码见 [机器学习](src/machine_learning/README.md)，旧 MuJoCo 脚本也已迁入。环境、完整模型库、数据集和权重不打包，详情见 [迁入记录](doc/source-consolidation.md)。

代码存在、程序可运行、实验通过与原理掌握分别记录。当前 Lesson 1 的自定义接口依赖和通信问题已列明；其他案例的环境、外部资源与结果仍需逐课核对。具体状态和近期处理顺序见 [路线中的当前材料与建议](doc/learning-roadmap.md#next)。

## 仓库说明

- `build/`、`install/`、`log/` 是 ROS 2 / colcon 构建产物，不进入版本记录。
- `.vscode/`、`__pycache__/`、`.pyc`、调试图片和 episode 数据文件属于本地环境或运行产物，不作为学习源码保存。
- Lesson 8 中的 MuJoCo 视觉脚本依赖本机 XML 场景、模型路径和自定义 viewer 工具，运行前需要按对应 README 检查路径。
- 旧 lesson 只保留历史编号跳转；教程与源码已归入主题目录，新增案例采用主题目录和描述性实验名，具体规则见 [案例索引](src/README.md)。

## 参考资料

学习和实践过程中主要参考了：

- ROS 2 官方文档
- Modern Robotics 教材与配套资料
- MoveIt 官方文档
- MuJoCo 官方文档
- B 站 UP 主：荔枝澄

学习路线和专题笔记在相关位置附有具体资料链接。视频用于辅助理解，接口和公式按实际版本与原始资料核对。
