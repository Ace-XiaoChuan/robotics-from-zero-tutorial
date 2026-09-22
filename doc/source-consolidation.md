# 教程与源码集中存放记录

本文行数：26行，预期阅读时长：2分钟

2026-09-21 将本机已有教程与源码迁入主仓库。仓库用于快速阅览复习，完整运行环境不是收录条件；原目录未删除，后续内容以本仓库维护为准。

| 原始来源 | 本仓库位置 | 范围 |
| --- | --- | --- |
| `/home/ace/moveit-from-zero-tutorial/src` | [MoveIt 与 MTC](../src/manipulation/README.md) | hello_moveit、mtc_tutorial、mtc_advanced_demo、panda_moveit_config、pick_and_place 五个包，后者仅骨架 |
| `/home/ace/machine_learning_project` | [机器学习](../src/machine_learning/README.md) | 七个项目的源码、笔记、历史实验记录、依赖说明和小型指标/图 |
| `/home/ace/mujoco_workspace` | [旧 MuJoCo 脚本](../src/simulation/mujoco/legacy/run_sim.py) · [旧计划](../src/simulation/mujoco/legacy/task.md) | run_sim.py 与 task.md；计划仅作历史参考 |

## 收录原则

教程和自有源码集中存放，保留解释源码所需的小型配置。排除第三方框架源码、完整模型库、虚拟环境、构建目录、数据集和训练权重。机器学习图与 JSON 指标仅收录单文件小于 500 KB 的部分，用于读懂旧结果；CSV 数据和预测表未迁入。未收录的文件不再作为有效本地链接展示。

[导入清单](source-import-manifest.json) 逐项记录原路径、目的路径及源文件 SHA-256。哈希对应导入前原文；迁入后的阅读提示、路径更新和 Markdown 元数据会改变文档哈希。源码保持原样，未宣称已消除其所有历史问题。

## 阅读与运行边界

- MoveIt 包保留 package.xml 和 CMakeLists；Panda 配置引用的模型描述包未打包。
- 机器学习 requirements.txt 是原环境依赖线索，不是已锁定、已验证的新环境。
- 旧 MuJoCo 脚本仍使用相对 Menagerie 路径和前七个关节假设，阅读时配合 [材料说明](../src/simulation/mujoco/materials.md)。未迁入模型库，也未启动该脚本。
- 原笔记中的成绩、日志和“已完成”指历史记录；本次验证仅覆盖迁入完整性、Python 语法、文档元数据和新增导航，不包含 ROS 构建、仿真或模型训练。

教程与源码现已归入主题目录，旧 lesson 仅保留跳转；具体位置见 [目录重组记录](directory-reorganization.md)。无需先搭环境才能复习，也不要求读者补做实验。
