# 目录重组记录

本文行数：46行，预期阅读时长：3分钟

2026-09-21 将旧 lesson 与迁入的机器学习项目统一归入知识主题。主题目录是维护位置，旧 lesson 只保留跳转 README；原有未提交内容按工作区现状迁移，没有用 Git 版本覆盖。被忽略的本地编辑器缓存保留原位置，不属于教程迁移或版本记录。

## 路径对照

| 原位置 | 新位置 |
| --- | --- |
| `src/lesson1` | `src/ros2/examples/communication` |
| `src/lesson2` | `src/ros2/examples/composition` |
| `src/lesson3` | `src/foundations/spatial_math/examples/rigid_transforms` |
| `src/lesson4` | `src/kinematics/02_dh_conventions` |
| `src/lesson5` | `src/manipulation/03_move_group_interface` |
| `src/lesson5/draw_line_and_circle.cpp` | `src/manipulation/packages/hello_moveit/src/draw_line_and_circle.cpp` |
| `src/lesson6` | `src/manipulation/06_pick_place` |
| `src/lesson6/README.md` | `src/manipulation/06_pick_place/history.md` |
| `src/lesson6/mtc_week3_demo` | `src/manipulation/packages/mtc_week3_demo` |
| `src/lesson7` | `src/simulation/mujoco/examples/state_and_control` |
| `src/lesson8` | `src/perception/examples/camera_and_tags` |
| `src/lesson9` | `src/kinematics/examples/model_alignment` |
| `src/manipulation/packages/hello_moveit/readme.md` | `src/manipulation/03_move_group_interface/history.md` |
| `src/machine_learning/projects/week01_iris_knn` | `src/machine_learning/01_supervised_knn` |
| `src/machine_learning/projects/week02_regression` | `src/machine_learning/02_regression` |
| `src/machine_learning/projects/week03_titanic_pipeline` | `src/machine_learning/03_preprocessing_pipeline` |
| `src/machine_learning/projects/week04_digits_model_selection` | `src/machine_learning/04_model_selection` |
| `src/machine_learning/projects/week05_clustering` | `src/machine_learning/05_clustering` |
| `src/machine_learning/projects/week06_pytorch_digits` | `src/machine_learning/06_pytorch_networks` |
| `src/machine_learning/projects/week07_transfer_learning` | `src/machine_learning/07_transfer_learning` |

## 合并与保留

- Lesson 5 绘图源码与 hello_moveit 中版本逐字一致，合并为一个文件。
- Lesson 6 的 mtc_week3_demo 与其他 MTC 包是不同实现，完整保留；运行命令与视频移至抓放章节的 history.md。
- 原 hello_moveit 长篇日志移至接口章节的 history.md，包内只保留实现和构建配置。
- 机器学习七个项目去掉 projects/week 名称，改为 01～07 主题章节；项目内部 src/data/outputs 相对关系保留，历史实验数字不改写。
- 视觉采集、仿真控制及运动学控制保持完整案例，控制与数据采集主题用链接复用。

[文件迁移清单](directory-move-manifest.json) 记录每个迁移前文件的 SHA-256 与新路径；文档、源码中的路径说明按新位置更新，哈希代表迁移前快照。[外部迁入清单](source-import-manifest.json) 的目的路径同步更新，原来源路径保持不变。

## 验证边界

实际检查通过：203 个迁移条目均有目的文件；163 个源码、配置与资源文件与迁移前快照对照，仅包含预期路径说明更新；79 个 Python 文件语法通过；511 个本地文件链接目标存在；12 处 CMake 源文件引用存在，package.xml 语法通过；Markdown 元数据检查通过。不搭建环境，不以本次迁移宣称 ROS 构建、仿真、训练或控制执行已经通过。

[总目录](../src/README.md)
