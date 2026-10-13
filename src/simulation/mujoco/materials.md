# Panda 外加关节力脚本说明

本文行数：13行，预期阅读时长：1分钟

[run_sim.py](legacy/run_sim.py) 加载 Panda 场景，读取关节位置和速度，用 PID 形式计算控制量，加上 `qfrc_bias` 后写入 `qfrc_applied`，再调用 `mj_step` 和 Viewer 同步。

脚本依赖 MuJoCo、NumPy 和 MuJoCo Menagerie 的 `franka_emika_panda/scene.xml`，没有调用 Matplotlib。模型路径相对于启动目录，读取关节时使用数组前七项；运行前需要使路径和模型关节顺序与脚本一致。

这里通过外加广义力驱动机器人。模型也定义了 actuator，`qfrc_applied` 与 actuator 的 `ctrl` 是不同输入入口，见[控制输入](../04_control_inputs/README.md)。积分项仅裁剪输出，具体控制表现需结合轨迹误差判断。

该 Panda 脚本尚无运行验证记录。需要自包含模型和数值例子时，查看 [pendulum.xml](models/pendulum.xml) 与 [check_basics.py](check_basics.py)。

[MuJoCo 目录](README.md) · [动力学与控制](../../control/README.md)
