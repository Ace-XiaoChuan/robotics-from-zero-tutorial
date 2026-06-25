# Robotics From Zero Tutorial

这个仓库用于记录我从零开始学习机器人相关内容的过程、代码练习和阶段性总结。内容从 C++ 基础复习开始，逐步扩展到 ROS 2、机器人运动学、MoveIt、MuJoCo 仿真，以及相机、传感器和 AprilTag 等机器人视觉感知基础内容。

仓库定位是个人学习记录：代码和笔记优先服务于复习、查阅和后续扩展，不追求一次性写成完整课程。

## 学习路线

| Lesson | 主题 | 入口 |
| --- | --- | --- |
| Lesson 1 | C++ 引用 `&` 复习 | [`src/lesson1`](src/lesson1) |
| Lesson 2 | Lambda 表达式复习 | [`src/lesson2`](src/lesson2) |
| Lesson 3 | 构造函数、析构函数、独占智能指针 | [`src/lesson3`](src/lesson3) |
| Lesson 4 | ROS 2 接口与通信 Demo | [`src/lesson4/ros2_comm_demo`](src/lesson4/ros2_comm_demo) |
| Lesson 5 | ROS 2 Component / composition | [`src/lesson5/lesson5_composition`](src/lesson5/lesson5_composition) |
| Lesson 6 | 正运动学与 DH 参数表 | [`src/lesson6`](src/lesson6) |
| Lesson 7 | Modified DH 运动学实践 | [`src/lesson7`](src/lesson7) |
| Lesson 8 | MoveIt 基础绘制与规划练习 | [`src/lesson8`](src/lesson8) |
| Lesson 9 | MoveIt Task Constructor 实践 | [`src/lesson9`](src/lesson9) |
| Lesson 10 | MuJoCo / MJCF 基础与轨迹跟踪 | [`src/lesson10`](src/lesson10) |
| Lesson 11 | MuJoCo 相机、传感器与 AprilTag | [`src/lesson11`](src/lesson11) |

## 重点内容

- C++ 基础与现代 C++ 常用语法复习。
- ROS 2 节点、接口、launch、component 等基础实践。
- 机器人正运动学、DH 参数表和简单运动学链路。
- MoveIt 与 MoveIt Task Constructor 的运动规划实践。
- MuJoCo / MJCF 模型组织、仿真状态读取和关节控制。
- 仿真相机、AprilTag、SolvePnP、SensorData 与多模态数据采集。

## 当前进度

目前已经完成 C++ 基础复习、ROS 2 接口与组件实践、机器人正运动学和 DH 参数表实践，并完成了 MoveIt 基础、MTC、MuJoCo 基础控制以及 Lesson 11 中的相机 / 传感器 / AprilTag 数据采集链路整理。

后续会继续围绕 ROS 2、MoveIt、MuJoCo、机器人视觉感知和机器人开发工具链扩展，包括通信机制、参数、服务、动作、运动规划、仿真控制、视觉定位以及简单机器人综合项目。

## 后续计划

- MuJoCo 中更复杂的控制实践。
- AprilTag 检测结果与机器人控制流程结合。
- IK / FK 与控制接口学习实践。
- 路径优化与轨迹优化相关内容。
- 简单机器人项目综合实践。

## 仓库说明

- `build/`、`install/`、`log/` 是 ROS 2 / colcon 构建产物，不进入版本记录。
- `.vscode/`、`__pycache__/`、`.pyc`、调试图片和 episode 数据文件属于本地环境或运行产物，不作为学习源码保存。
- Lesson 11 中的 MuJoCo 视觉脚本依赖本机 XML 场景、模型路径和自定义 viewer 工具，运行前需要按对应 README 检查路径。

## 参考资料

学习和实践过程中主要参考了：

- ROS 2 官方文档
- MoveIt 官方文档
- MuJoCo 官方文档
- B 站 UP 主：荔枝澄

这些资料对理解相关概念、搭建开发环境以及完成实践项目提供了重要帮助。
