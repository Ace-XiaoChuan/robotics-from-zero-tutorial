# MuJoCo 已有材料与主题归属

本文行数：35行，预期阅读时长：2分钟

2026-09-18 按本地文件与源码清点；本次未启动仿真，也未验证控制效果。当前是部分探索材料，后续逐章整理。

## 本地工作区

位置：`/home/ace/mujoco_workspace/`。路径仅用于本机查找，完整复现所需的依赖、模型版本与配置后续补齐。

| 已有位置 | 实际内容与处理方式 |
| --- | --- |
| `run_sim.py` | 加载 Panda 场景，建立模型与数据；读取前 7 个关节位置和速度，计算 PID 形式的控制量并加入 `qfrc_bias`，写入 `qfrc_applied`；调用 `mj_step` 与 Viewer 同步 |
| `mujoco_menagerie/franka_emika_panda/scene.xml` | 脚本实际引用的场景，通过 `panda.xml` 引入机器人模型 |
| `mujoco_menagerie/` | 模型库；不能将库内所有模型视为已经学习或验证 |
| `mj_env/` | 本地 Python 虚拟环境，配置记录 Python 3.10.12；不复制到教程仓库 |
| `task.md` | 旧的八周跨主题计划，涉及 MoveIt、其他仿真器与模仿学习；保留作历史参考，当前顺序以本仓库学习路线为准 |
| `MUJOCO_LOG.TXT`、`.vscode/` | 本地日志与编辑器配置，不作为教程章节迁入 |

## 与其他主题的边界

| 内容 | 后续主要归属 |
| --- | --- |
| MJCF、模型加载、状态、步进、控制输入接口与 Viewer | `simulation/mujoco/` |
| PID 原理、偏置力补偿与跟踪误差 | `control/`；引用 MuJoCo 接口说明 |
| 仿真与解析 FK 的对齐 | `kinematics/` |
| 相机成像、标定与目标位姿 | `perception/`；渲染接口回链 MuJoCo |
| observation / action、episode 与回放 | `data_collection/` |
| 策略在仿真中的闭环评估 | `robot_learning/` |

源码中的模型路径相对于启动目录，关节读取依赖前 7 项的排列。积分项仅对输出做裁剪；模型自身还定义了 actuator，脚本则通过外加关节力控制。后续整理控制章节时需一起核对这些行为，不能直接把该脚本标为已验证的执行器力矩控制案例。

原脚本、模型库和环境保留在原工作区；本次只建立材料索引与目录关系，不补写教程或改动控制实现。

[返回 MuJoCo 目录](README.md) · [学习路线](../../../doc/learning-roadmap.md#s3)
