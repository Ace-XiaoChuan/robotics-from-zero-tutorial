# MuJoCo

本文行数：22行，预期阅读时长：1分钟

- [本地工作区与已有材料](materials.md)
- [已有模型、状态与控制笔记](../../lesson7/README.md)
- [已有相机与传感器笔记](../../lesson8/cv_trainning/README.md)
- [已有 FK 对齐代码](../../lesson9/check_fk_with_mujoco.py)

## 后续章节安排

以下仅是目录规划，具体教程稍后编写，不创建空章节。

| 计划目录 | 内容 | 材料情况 |
| --- | --- | --- |
| `01_model_loading/` | Menagerie、MJCF、模型路径与加载 | 本地脚本与 Panda 模型已有 |
| `02_state_step/` | 模型与数据、状态索引、步长与步进 | 本地脚本已有基础用法；Lesson 7 有补充 |
| `03_control_inputs/` | actuator、`ctrl` 与外加关节力的区别 | 本地脚本使用 `qfrc_applied`；输入语义需进一步整理 |
| `04_viewer_rendering/` | 交互 Viewer、相机与渲染 | 本地脚本有 Viewer；相机材料在 Lesson 8 |
| `05_reset_recording/` | 初始化、重置、状态记录与可重复运行 | 待补；本地脚本尚未形成完整接口 |

[返回仿真目录](../README.md) · [总体目录](../../README.md)
