# 后续工作优先级

本文行数：18行，预期阅读时长：2分钟

## 第一优先：按实际需要补充（不固定先后）

- [ ] [动力学与控制](../src/control/README.md)：遇到具体疑问时补写第 07 部分“按需深入”。
- [ ] 标定与参数辨识：手眼、基座与工具 TCP、关节零位、负载与动力学参数。
- [ ] 具体真机接入与执行验证（确定设备后再补）：复用[仿真与真机控制流导读](../src/simulation/00_control_flow/README.md)中的驱动分层、ros2_control、轨迹接口、控制周期与状态反馈，以及 [MoveIt 配置](../src/manipulation/02_moveit_setup/README.md)中的接口映射。新增内容只围绕具体设备的 SDK / 驱动与通信配置、关节单位和零位核对、使能与停止（含取消、保护停止和急停的区别）、故障码与恢复条件，以及实际通信时序和轨迹跟踪记录；不重复编写通用控制链教程。
- [ ] 接触与柔顺控制：摩擦、抓取稳定性、力控制、阻抗与导纳。
- [ ] 任务执行与集成：状态机、超时与取消、失败恢复、系统记录与评估。
- [ ] 仿真可信度与迁移：模型参数、执行器与接触、延迟与噪声、仿真与真机差异。

## 第二优先：按项目需要扩展

- [ ] 数据采集与模仿学习：示教、同步与回放；学习算法与策略解释见[18 模仿学习](../src/machine_learning/18_imitation_learning/README.md)，实际实现与闭环评估按 S8/S9 推进。
- [ ] 强化学习与进阶策略：原理见[17 生成与扩散](../src/machine_learning/17_generative_models/README.md)、[18 模仿学习](../src/machine_learning/18_imitation_learning/README.md)、[19 强化学习](../src/machine_learning/19_reinforcement_learning/README.md)及[20 泛化与迁移](../src/machine_learning/20_generalization_sim2real/README.md)；实际算法比较仍需实现基线与独立评估。
- [ ] 移动机器人与 SLAM、双臂与灵巧手等：[按需选修](learning-roadmap.md#extensions)。
