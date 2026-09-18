# Robotics From Zero Tutorial

本文行数：79行，预期阅读时长：4分钟

这个仓库用于沉淀个人机器人工程学习笔记、代码实验与阶段总结。当前主线是机械臂的建模、感知、规划、控制与仿真，后续扩展到数据采集和模仿学习。

仓库定位是个人学习记录：笔记以快速复习为主，用例子、结果和解释帮助找回印象；代码供需要实现或复现时参考。

## 从哪里开始

- **按顺序学习**：[学习路线](doc/learning-roadmap.md)，按能力与先修关系推进，不限定周数。
- **按问题查阅**：[知识索引](doc/README.md)，直接进入需要的专题。
- **查看总体架构与代码位置**：[总体目录与案例索引](src/README.md)，查看机器人、MuJoCo、MoveIt、机器学习的章节安排及已有材料归属。
- **整理新的笔记**：[文档样板](doc/lesson-template.md)，参考 [Lesson 1](src/lesson1/README.md) 的完整示例。
- **快速回忆工程基础**：[S0 · 单元 01：终端、路径与环境](src/foundations/engineering/01_shell_paths/README.md)。

## 学习主线

工程基础 → 空间数学 → ROS 2 与模型仿真 → 正逆运动学 → 动力学与控制 → 感知与状态估计 → 规划与操作 → 数据采集 → 模仿学习。

详细路线区分必修、可交替学习的内容和选修分支。阶段里程碑是：

1. 环境、坐标和通信可复现。
2. 机械臂通过执行器控制到达目标，并记录误差。
3. 从感知到规划、控制和抓放形成完整任务。
4. 按需要继续完成示教、行为克隆和策略评估。

## 已有案例

Lesson 编号是历史案例标识，下面的表格用于查找，不代表推荐学习顺序。同一 lesson 可能对应多个阶段。

| Lesson | 主题 | 入口 |
| --- | --- | --- |
| Lesson 1 | ROS 2 接口与通信 Demo | [课程入口与运行说明](src/lesson1/README.md) · [详细知识笔记](src/lesson1/ros2_interfaces_notes.md) |
| Lesson 2 | ROS 2 Component / composition | [`src/lesson2/lesson2_composition`](src/lesson2/lesson2_composition) |
| Lesson 3 | 旋转矩阵、齐次变换与点变换 | [`src/lesson3`](src/lesson3) |
| Lesson 4 | Modified DH 运动学实践 | [`src/lesson4`](src/lesson4) |
| Lesson 5 | MoveIt 基础绘制与规划练习 | [`src/lesson5`](src/lesson5) |
| Lesson 6 | MoveIt Task Constructor 实践 | [`src/lesson6`](src/lesson6) |
| Lesson 7 | MuJoCo / MJCF 基础与轨迹跟踪 | [`src/lesson7`](src/lesson7) |
| Lesson 8 | MuJoCo 相机、传感器与 AprilTag | [`src/lesson8`](src/lesson8) |
| Lesson 9 | MuJoCo / Pinocchio / KDL 正逆运动学与末端控制 | [`src/lesson9`](src/lesson9) |

## 文档

| 文档 | 内容 |
| --- | --- |
| [知识索引](doc/README.md) | 按主题查阅已整理的 lesson 知识点。 |
| [Lesson 文档样板](doc/lesson-template.md) | 课程入口、专题笔记模板和写作约定；以 Lesson 1 为完整示例。 |
| [学习路线](doc/learning-roadmap.md) | 10 个能力阶段、先修关系、实验验收、近期顺序与选修方向。 |
| [总体目录与案例索引](src/README.md) | 机器人、MuJoCo、MoveIt、机器学习的目标目录、现有位置与整理规则。 |
| [协作约定](AGENTS.md) | 用户授权、学习笔记定位与代码验证规则。 |

## 当前进度

已有通信、空间变换、运动学、规划、控制、视觉和数据保存相关代码。Lesson 1 已完成详细文档整理；Lesson 7、8 有较长说明，Lesson 9 有运动学专题笔记。

S0 单元 01～06 已提供工程、Git、Python 数值、C++ 构建、调试和实验复现的直接阅读材料。MuJoCo 的部分探索保留在 `~/mujoco_workspace`，已建立[材料索引](src/simulation/mujoco/README.md)，具体教程待补；MoveIt / MTC 的完整工作区保留在 `~/moveit-from-zero-tutorial`；KNN、决策树、聚类、PyTorch 和迁移学习资料保留在 `~/machine_learning_project`，主仓库通过 [案例索引](src/README.md) 和 [学习路线](doc/learning-roadmap.md) 维护它们与机器人主线的关系。

代码存在、程序可运行、实验通过与原理掌握分别记录。当前 Lesson 1 的自定义接口依赖和通信问题已列明；其他案例的环境、外部资源与结果仍需逐课核对。具体状态和近期处理顺序见 [路线中的当前材料与建议](doc/learning-roadmap.md#next)。

## 仓库说明

- `build/`、`install/`、`log/` 是 ROS 2 / colcon 构建产物，不进入版本记录。
- `.vscode/`、`__pycache__/`、`.pyc`、调试图片和 episode 数据文件属于本地环境或运行产物，不作为学习源码保存。
- Lesson 8 中的 MuJoCo 视觉脚本依赖本机 XML 场景、模型路径和自定义 viewer 工具，运行前需要按对应 README 检查路径。
- 已有 lesson 在逐课整理时按需要拆分或迁移；新增案例优先采用主题目录和描述性实验名，具体规则见 [案例索引](src/README.md)。

## 参考资料

学习和实践过程中主要参考了：

- ROS 2 官方文档
- Modern Robotics 教材与配套资料
- MoveIt 官方文档
- MuJoCo 官方文档
- B 站 UP 主：荔枝澄

学习路线和专题笔记在相关位置附有具体资料链接。视频用于辅助理解，接口和公式按实际版本与原始资料核对。
