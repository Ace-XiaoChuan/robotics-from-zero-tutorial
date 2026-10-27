# 机器人模型与 MoveIt 配置

本文行数：250行，预期阅读时长：14分钟

**MoveIt 配置把“机器人是什么、允许怎样运动、用哪个算法求解、把结果发给谁”连接起来。文件中的关节名、规划组、坐标系和接口必须相互对应，文件齐全不代表系统已经能运行。**

解释模型、规划组、末端、IK、关节限制和控制器配置之间的关系，以仓库的 Panda 文件为例。URDF 建模基础见[机器人模型](../../simulation/02_scene_objects/README.md)，运动请求与返回值归[第三章](../03_move_group_interface/README.md)，运行中的场景管理归[第四章](../04_planning_scene/README.md)。

## 速记要点

- **URDF 描述结构，SRDF 描述规划语义。** 前者定义连杆、关节和几何；后者指定规划组、命名姿态、末端和忽略哪些自碰撞对。
- **规划组、末端组、目标 link 和工具中心点是不同对象。** `panda_arm` 是手臂组，`hand` 是本例的手爪组及末端名称，`panda_hand` 是 link 名称。
- **模型、初始值、当前状态分开看。** URDF 是结构，SRDF 的 `ready` 是可选目标，mock 初始值是启动状态来源之一，当前运动状态需要反馈。
- **IK 与路径规划分工不同。** `kinematics.yaml` 选择位姿到关节解的求解器；它不负责完整避障路径搜索。
- **两份控制器 YAML 服务于不同层。** MoveIt 配置说明“找哪个接口”，ros2_control 配置说明“加载什么控制器、使用什么关节接口”。
- **mock 运动只能说明接口行为。** 本地控制 Xacro 使用 `mock_components/GenericSystem`，不能据此证明真实动力学、接触或抓取效果。

本章主要依据本地文件静态阅读；数值例子直接给出解释，无需启动 ROS。配置中的疑点单独列出，不把它们当作正确范本。

## 1. 一张表看清配置分别管什么

配置目录：[panda_moveit_config/config](../packages/panda_moveit_config/config/)。

| 文件 | 主要作用 | 读配置时先看什么 |
| --- | --- | --- |
| [panda.urdf.xacro](../packages/panda_moveit_config/config/panda.urdf.xacro) | 引入机器人 URDF，并加入 ros2_control 描述 | 外部模型包、包含关系、Xacro 参数 |
| [panda.srdf](../packages/panda_moveit_config/config/panda.srdf) | 规划组、命名状态、末端、虚拟关节和自碰撞排除 | 组名、link / joint 名称是否与 URDF 对应 |
| [kinematics.yaml](../packages/panda_moveit_config/config/kinematics.yaml) | 按规划组选择 IK 插件和相关参数 | 组名、插件名、求解时间预算 |
| [joint_limits.yaml](../packages/panda_moveit_config/config/joint_limits.yaml) | 补充或覆盖规划使用的关节运动限制 | 限制是否启用、数值单位、缩放因子 |
| [moveit_controllers.yaml](../packages/panda_moveit_config/config/moveit_controllers.yaml) | MoveIt 到执行接口的映射 | 控制器名、Action 类型、命名空间、关节列表 |
| [ros2_controllers.yaml](../packages/panda_moveit_config/config/ros2_controllers.yaml) | ros2_control 控制器及其参数 | 插件类型、命令和状态接口、更新频率 |
| [panda.ros2_control.xacro](../packages/panda_moveit_config/config/panda.ros2_control.xacro) | 硬件插件与可用关节接口 | 使用 mock、仿真还是实际硬件插件 |
| [initial_positions.yaml](../packages/panda_moveit_config/config/initial_positions.yaml) | 本例 mock 位置状态接口的启动初始值 | 初值是否在限位内，是否与预期起点一致 |
| [pilz_cartesian_limits.yaml](../packages/panda_moveit_config/config/pilz_cartesian_limits.yaml) | Pilz 规划器相关的笛卡尔运动限制 | 只有被对应流程加载和使用时才生效 |

这些文件经 launch 和配置工具组织成节点参数；不是把文件放进 `config/` 就自动对所有节点生效。ROS 2 参数属于各个节点，使用模型的节点需要获得一致的机器人描述。参数加载机制参见 [MoveIt Humble 模型加载说明](https://moveit.picknik.ai/humble/doc/examples/urdf_srdf/urdf_srdf_tutorial.html#loading-the-urdf-and-srdf)。

## 2. URDF 与 SRDF：结构和用途怎样对应？

### URDF：机器人本体的结构

URDF 的 joint 把 parent link 和 child link 连接起来，关节原点、轴向、类型和变量共同决定正运动学。长度使用 m，转动关节角使用 rad；模型零位和轴向如果错了，后续 IK 和碰撞计算都会围绕错误的机器人工作。

同一 link 的 `visual` 与 `collision` 可以使用不同几何。前者服务于显示，后者服务于碰撞计算；外观显示正常不能证明碰撞形状或碰撞结果正确。质量与惯性则主要服务于动力学，不能从“几何规划成功”反推其正确性。

本地 [panda.urdf.xacro](../packages/panda_moveit_config/config/panda.urdf.xacro) 并未写出完整连杆树，而是引入：

```xml
<xacro:include filename="$(find moveit_resources_panda_description)/urdf/panda.urdf" />
<xacro:include filename="panda.ros2_control.xacro" />
```

**结果与解释：** 具体连杆尺寸、关节类型、手指 mimic 关系和位置上下限要到外部描述包的实际版本中查看。本仓库保留了引用及控制配置，没有打包这个第三方模型；本地 wrapper 存在不等于 URDF 已成功展开，也不等于网格资源可以找到。

### SRDF：这台机器人怎样参与规划

| 本地 SRDF 项 | 本例值 | 含义 |
| --- | --- | --- |
| 手臂规划组 | `panda_arm` | 一次手臂规划所使用的关节与连杆集合 |
| 手爪规划组 | `hand` | 由 `panda_hand`、左右手指 link 定义的组 |
| 命名状态 | 手臂 `ready`；手爪 `open`、`close` | 给特定组的一组关节值起名字 |
| 虚拟关节 | `world → panda_link0`，类型 `fixed` | 把模型根链接与外部世界参考系关联 |
| 自碰撞排除 | 多个 `disable_collisions` 条目 | 对指定 link 对跳过碰撞检查 |

`panda_arm` 在 SRDF 中列出了 `virtual_joint` 和 `panda_joint1…panda_joint8`，**条目数量不等于独立可动自由度数量**：虚拟关节在本文件中明确为 fixed，其余 joint 类型还要结合展开后的 URDF 判断。手臂控制器列出的是 `panda_joint1…panda_joint7`，不能把 SRDF 所有条目原样当作控制命令数组。

`disable_collisions` 是排除检查的配置，`Adjacent`、`Never`、`Default` 是记录原因的标签，不是当前场景的运行证明。机器人几何、工具或安装关系变化后，这些排除项需要重新审视；不要靠大范围禁用碰撞来“修复”规划失败。相关模型语义见 [Humble URDF / SRDF 文档](https://moveit.picknik.ai/humble/doc/examples/urdf_srdf/urdf_srdf_tutorial.html)。

虚拟关节的声明也不能独自证明运行时 TF 完整。本包提供 [static_virtual_joint_tfs.launch.py](../packages/panda_moveit_config/launch/static_virtual_joint_tfs.launch.py) 生成相关发布配置，实际参考变换仍应与机器人的安装位置一致。

## 3. 例子一：`ready` 不是启动时自动采用的姿态

**输入：** SRDF 中的 `ready` 为手臂七个关节赋值。按 `panda_joint1…panda_joint7` 排列，单位 rad：

```text
q_ready = [0, −0.5551, 0, −2.2867, 0, 1.4405, 1.2326]
```

而本地 `initial_positions.yaml` 把同样七个关节的初值全部写为零：

```text
q_initial = [0, 0, 0, 0, 0, 0, 0]
```

**结果与解释：** 两份文件表达不同信息。`ready` 是命名目标，只有被选用时才参与相应请求；本例控制 Xacro 将 YAML 初值填入 `state_interface` 的 `initial_value`。如果该配置链按预期加载，mock 初始位置来自后者，不会因为 SRDF 中存在 `ready` 就自动变成前者。

因此，“启动后规划起点无效”应先核对反馈状态与加载模型的关节限位，而不是只检查 `ready`。本章没有展开外部 URDF，不能据此断言全零构型在当前安装的模型中合法或无碰撞。

手爪的 `open` 把 `panda_finger_joint1` 设为 `0.035 m`，`close` 设为 `0 m`。这首先是一个关节的位移，不是整只夹爪的开口宽度。在对称、零偏置且两侧各移动 `0.035 m` 的理想模型下，开口才可推得 `0.070 m`；本例具体对应关系要结合外部 URDF 的几何与 mimic 配置确认。

`close=0` 也不是夹持力设定，更不能证明物体已被夹住。接触与夹持条件归[第六章](../06_pick_place/README.md)。

## 4. 规划组、末端与工具坐标：名称不能混用

| 名称 | 本地用途 | 不应误当作什么 |
| --- | --- | --- |
| `panda_arm` | 手臂规划组，`kinematics.yaml` 的顶层键 | 某个坐标系名称 |
| `hand` | 手爪规划组，同时也是 SRDF 末端名称 | 手臂 IK 的目标位置坐标 |
| `panda_hand` | link 名，MTC 源码用它作为相关参考 link | 自动等于指尖中心或笔尖的 TCP |
| TCP（tool center point） | 任务真正关心的工具工作点与朝向 | 仅由“末端组名”唯一确定的点 |

例如 [pick_and_place.cpp](../packages/hello_moveit/src/pick_and_place.cpp) 为任务设置 `group="panda_arm"`、`eef="hand"`、`ik_frame="panda_hand"`；抓取 IK 包装阶段又相对手爪 link 指定了带旋转和 `0.1 m` 平移的局部变换。这说明工具工作坐标与 link 原点需要明确区分，不能只看字符串里有“hand”就认定它们重合。

### 一个坐标偏移的静态例子

设基座为 `B`，手爪 link 为 `H`，工具工作坐标系为 `T`。记 `⁽ᴬ⁾T_B` 为把 B 系坐标变换到 A 系的齐次变换，则：

```text
⁽ᴮ⁾T_T = ⁽ᴮ⁾T_H · ⁽ᴴ⁾T_T
⁽ᴮ⁾T_H = ⁽ᴮ⁾T_T · (⁽ᴴ⁾T_T)⁻¹
```

**输入（教学示意）：** 三个坐标系轴向平行，工具在手爪的 `+Z` 方向偏移 `0.1 m`，目标工具位置在基座系下为 `(0.4,0,0.3) m`。

**结果：** 手爪 link 的目标位置应为 `(0.4,0,0.2) m`。若误把工具目标直接当作手爪 link 目标，工具会落在 `(0.4,0,0.4) m`，Z 方向偏差为 `0.1 m`。这里采用无旋转的简化条件，不是上述抓取源码的完整变换计算。

### 本地 SRDF 中需要核对的末端关系

当前文件写的是：

```xml
<end_effector name="hand" parent_link="panda_link0" group="hand"/>
```

`parent_link` 表达末端组与父结构的连接关系，不是“目标位姿用哪个参考坐标系”。这里把它写成基座 `panda_link0`，与手爪通常安装在手臂末端的结构不符，是应核对的配置疑点。正确值应依据实际展开的 URDF、手臂组与手爪组边界确定，不能因本地缺少外部模型而随意猜一个 link 替换。本次文档补充保留配置原值，也不声称已经观察到由此引起的运行失败。

## 5. IK 插件和规划器：分别求解什么？

本地 [kinematics.yaml](../packages/panda_moveit_config/config/kinematics.yaml) 的数值简写如下：

```yaml
panda_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.005
```

- 顶层 `panda_arm` 必须对应模型中的规划组，否则这份求解配置无法按预期关联到手臂。
- KDL 插件用于数值运动学求解。给定位姿和种子构型后求关节解，不是整条无碰撞路径的规划器。
- `kinematics_solver_timeout` 的单位是 s；这里 `0.005 s = 5 ms` 是 IK 求解相关的时间预算，不是整次运动规划预算，也不是控制周期。
- `kinematics_solver_search_resolution` 是求解器搜索冗余空间时可能使用的离散尺度，其实际使用依赖插件实现；不能把 `0.005` 解读成末端位置误差 `5 mm`。

参数用途参见 [Humble 运动学配置说明](https://moveit.picknik.ai/humble/doc/examples/kinematics_configuration/kinematics_configuration_tutorial.html)。配置里的数值不保证每个目标都能求解成功；超时、种子、关节限制和奇异性都会影响结果。

路径规划流水线再使用运动学、状态有效性和碰撞检查等信息搜索连接路径。本包没有本地 `ompl_planning.yaml`，launch 通过配置工具生成完整配置，可能采用工具提供的默认项。因此不能只根据 `kinematics.yaml` 判断实际使用哪个规划器；也不能因为缺少这个本地 YAML 就断言完全没有规划流水线。

## 6. 例子二：关节限制中的 `0.1` 到底是什么意思？

本地 [joint_limits.yaml](../packages/panda_moveit_config/config/joint_limits.yaml) 包含：

```yaml
default_velocity_scaling_factor: 0.1
default_acceleration_scaling_factor: 0.1
# 以下是 panda_joint1 条目的节选
has_velocity_limits: true
max_velocity: 2.3925
has_acceleration_limits: false
max_acceleration: 0
```

**输入与条件：** 假设 `panda_joint1` 的有效速度上限确为 `2.3925 rad/s`，且本次轨迹生成使用速度缩放 `0.1`。

**推导结果：** 缩放后的速度上限为 `0.23925 rad/s`。这是上限，不意味着关节全程都以该速度运动；更不是末端以 `0.1 m/s` 匀速运动。若请求或实际加载值不同，该数值也随之改变。

`has_acceleration_limits: false` 表示这条配置没有启用该项加速度限制，不能把后面的 `max_acceleration: 0` 理解为“机械臂必须零加速度”。也不能认为默认加速度缩放 `0.1` 自动补齐了有效上限；实际轨迹处理对未提供上限的处理依赖算法与版本，运行前需要核对加载后的限制。

转动关节的速度和加速度单位分别为 rad/s、rad/s²；手指移动关节则为 m/s、m/s²。位置上下限还要结合机器人描述。本文件的限制作用于规划与轨迹处理，不等于真实驱动器的限幅已经同步设置。相关处理见 [Humble 时间参数化说明](https://moveit.picknik.ai/humble/doc/examples/time_parameterization/time_parameterization_tutorial.html)。

`pilz_cartesian_limits.yaml` 另列了平移速度 `1.0 m/s` 等参数，但这是 Pilz 相关配置。文件存在并不能证明普通规划或本仓库的 `computeCartesianPath` 调用采用了这套笛卡尔限制。

## 7. 例子三：两份控制器配置怎样对上？

### 从 MoveIt 的执行接口找到 ros2_control 控制器

| 项目 | MoveIt 侧 | ros2_control 侧 |
| --- | --- | --- |
| 手臂名称 | `panda_arm_controller` | 同名控制器 |
| 手臂接口 | `FollowJointTrajectory`，`action_ns: follow_joint_trajectory` | `joint_trajectory_controller/JointTrajectoryController` |
| 手臂关节 | `panda_joint1…panda_joint7` | 相同七个关节 |
| 手爪名称 | `hand_controller` | 同名控制器 |
| 手爪接口 | `GripperCommand`，`action_ns: gripper_cmd` | `position_controllers/GripperActionController` |
| 手爪关节 | `panda_finger_joint1` | 同名命令关节 |

**静态结果：** 两份 YAML 的手臂关节列表及手爪命令关节对应一致。在没有额外 namespace 或 remap 的条件下，MoveIt 侧声明的目标 Action 名称分别为：

```text
/panda_arm_controller/follow_joint_trajectory
/hand_controller/gripper_cmd
```

这只证明配置声明相互对应，不证明 Action 服务端已经存在。MoveItSimpleControllerManager 使用这些映射连接执行接口，不会仅凭这份 YAML 自动完成 ros2_control 控制器的加载和激活。两侧分工见 [Humble 控制器配置说明](https://moveit.picknik.ai/humble/doc/examples/controller_configuration/controller_configuration_tutorial.html)。

### 再向下看命令接口和反馈

本地手臂控制器配置使用 `position` 命令接口，读取 `position` 和 `velocity` 状态接口；控制 Xacro 为七个手臂关节声明了对应接口。轨迹里可以有速度信息，但向这个硬件接口写入的命令类型仍然是位置，不能因此声称它在做力矩控制。

`controller_manager.update_rate: 100` 的单位是 Hz，对应名义更新间隔 `0.01 s`。这是控制管理循环的配置值，不是路径路点间隔，也不证明实际运行时每个周期都准时执行。

```mermaid
flowchart LR
    A[MoveIt 轨迹执行] -->|Action| B[手臂或手爪控制器]
    B -->|position 命令| C[硬件接口：本例为 GenericSystem]
    C -->|状态接口| D[joint_state_broadcaster]
    D -->|关节状态| E[MoveIt 当前状态与机器人显示]
```

这张图说明预期的数据关系。本地控制 Xacro 的插件为 `mock_components/GenericSystem`，用途是提供理想化的命令与状态接口行为，便于检查软件连接。即使在该系统中看到机器人运动，也不能推断已经模拟电机力矩、重力或物体摩擦。mock 的用途见 [ros2_control Humble 文档](https://control.ros.org/humble/doc/ros2_control/hardware_interface/doc/mock_components_userdoc.html)。

本地控制 Xacro 只声明一个手指的控制接口，第二手指如何随动和反馈，需要结合模型及硬件插件的 mimic 配置核对，不能仅凭左右手指都在 SRDF 中出现就认定完整链路已成立。

## 8. 哪份配置真的被加载？

[本地 demo.launch.py](../packages/panda_moveit_config/launch/demo.launch.py) 明确构造：

```python
MoveItConfigsBuilder("panda", package_name="panda_moveit_config")
```

而 [mtc_tutorial 的 launch](../packages/mtc_tutorial/launch/pick_place_demo.launch.py) 和 [hello_moveit 中的抓放 launch](../packages/hello_moveit/launch/pick_place_demo.launch.py) 使用：

```python
MoveItConfigsBuilder("moveit_resources_panda")
```

**结果与解释：** 后两者没有显式选择本地 `panda_moveit_config`，不能假定修改本地 YAML 会改变它们的行为。要按具体 launch、配置工具解析结果和工作区覆盖顺序确认实际包来源；如果客户端和 `move_group` 使用不同机器人语义，还可能出现组名或状态理解不一致。

此外，这两个抓放 launch 的正文只创建任务节点，不等于同时启动了 `move_group`、控制器和状态发布节点。运行入口的文件名本身不足以说明整套系统已被启动。

本地 [package.xml](../packages/panda_moveit_config/package.xml) 声明了外部模型包等依赖，但没有锁定实际版本；其中 `joint_trajectory_controller` 的依赖声明还是注释，而控制器 YAML 实际引用了它。因此包清单也不能单独证明运行依赖齐全。运行时需要使包依赖与控制器配置一致。

## 9. 遇到问题时从哪一层查？

| 现象 | 首先核对 | 原因 |
| --- | --- | --- |
| 模型无法展开或网格丢失 | 外部描述包、Xacro 包含路径、资源路径 | wrapper 依赖第三方模型 |
| 找不到 `panda_arm` 或 `hand` | 实际加载的 SRDF、组名拼写 | 代码中的组名必须属于当前模型 |
| 找不到 IK 插件或无法初始化 | 插件依赖、规划组与链结构、节点参数 | YAML 名字与实际插件、模型必须对应 |
| IK 失败但目标看起来很近 | 参考系、目标 link、TCP 偏移、姿态与限制 | “位置近”不是完整位姿可达的保证 |
| 启动状态与 `ready` 不同 | mock 初始值与当前关节反馈 | 命名姿态不会自动覆盖启动状态 |
| 控制器配置了却无法执行 | 加载与激活状态、Action 名称、关节覆盖和接口 | 映射配置不等于服务端可用 |
| 没有当前状态或状态过期 | broadcaster、反馈名称、时间戳与时钟来源 | 规划需要当前状态，不能只依靠模型文件 |
| 修改 YAML 后行为没变 | launch 选用的包、安装副本和节点参数 | 修改的可能不是运行中的配置来源 |

## 源码与参考

复习配置时可沿“外部模型 → SRDF 组与末端 → IK 与限制 → 控制器映射 → 硬件接口与反馈 → 实际加载入口”查阅。关节名、link 名、坐标系、单位和版本是贯穿各层的核对项。

配置说明来自仓库 XML / YAML 和 Humble 资料。外部模型的末端父链接、零位与手指随动关系，需要结合模型和运行时配置核对；本例尚未构建或启动验证。

[上一章：运动规划基础](../01_motion_planning/README.md) · [下一章：运动请求与执行反馈](../03_move_group_interface/README.md) · [返回 MoveIt 目录](../README.md)
