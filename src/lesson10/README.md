# 本周任务：MuJoCo / MJCF 基础学习

## 1. 任务目标

本周主要完成以下内容：

1. 简要了解 MJCF。
2. 学习以下 MuJoCo 基础操作：

   * 关节位置读取
   * 关节速度读取
   * 末端位姿读取
   * body / site ID 查询
   * PID 控制
   * position actuator
   * torque actuator
3. 编写一个关节空间轨迹跟踪 demo。

---

## 2. MJCF 最小示例

URDF 的内容此处不再展开。本节主要通过一个微型 MJCF 示例，帮助快速理解 MuJoCo 模型文件的基本组织方式。

MJCF 官方 XML 参考文档：

> https://mujoco.readthedocs.io/en/stable/XMLreference.html

下面给出一个尽量小、但结构相对完整的 MJCF demo。该示例包含以下模块：

1. 全局仿真设置：`compiler`、`option`
2. 可视化设置：`visual`
3. 默认属性：`default`
4. 资源定义：`asset`
5. 世界主体：`worldbody`
6. 刚体、关节、几何体和站点：`body`、`joint`、`geom`、`site`
7. 执行器：`actuator`
8. 传感器：`sensor`
9. 初始关键帧：`keyframe`

```xml
<mujoco model="learning_mjcf_example">
  <!--
    MuJoCo MJCF 学习示例

    该示例展示一个最小但相对完整的仿真场景：
    - 一个二维机械臂
    - 一个可自由运动的 box
    - 基本的执行器、传感器和初始状态
  -->

  <!--
    compiler：编译设置
    angle="degree" 表示角度单位使用度。
    coordinate="local" 表示局部坐标系定义。
  -->
  <compiler angle="degree" coordinate="local"/>

  <!--
    option：全局仿真参数
    timestep 是仿真步长。
    gravity 是重力加速度。
    integrator 指定积分器类型。
  -->
  <option timestep="0.002" gravity="0 0 -9.81" integrator="RK4"/>

  <!-- visual：可视化设置，不直接影响物理仿真 -->
  <visual>
    <headlight
      diffuse="0.6 0.6 0.6"
      ambient="0.25 0.25 0.25"
      specular="0.1 0.1 0.1"
    />
    <map znear="0.01" zfar="50"/>
  </visual>

  <!--
    default：默认属性
    可为同类元素设置统一默认值，减少重复书写。
  -->
  <default>
    <geom friction="0.8 0.1 0.1" density="1000" contype="1" conaffinity="1"/>
    <joint damping="0.8" armature="0.01" limited="true"/>
    <motor ctrllimited="true"/>
  </default>

  <!--
    asset：资源定义
    常用于定义 material、texture、mesh 等资源。
  -->
  <asset>
    <material name="mat_ground" rgba="0.8 0.8 0.8 1"/>
    <material name="mat_robot" rgba="0.1 0.45 0.9 1"/>
    <material name="mat_tip" rgba="0.9 0.25 0.15 1"/>
    <material name="mat_box" rgba="0.25 0.8 0.35 1"/>
  </asset>

  <worldbody>
    <!-- 地面 -->
    <geom
      name="ground"
      type="plane"
      size="4 4 0.1"
      material="mat_ground"
    />

    <!-- 光源 -->
    <light
      name="main_light"
      pos="0 0 3"
      dir="0 0 -1"
      diffuse="1 1 1"
    />

    <!-- 相机 -->
    <camera
      name="overview"
      pos="2.2 -2.8 1.7"
      xyaxes="0.78 0.63 0 -0.28 0.35 0.89"
    />

    <!--
      一个固定在世界中的二维机械臂。
      机械臂包含两个 hinge 关节：shoulder 和 elbow。
    -->
    <body name="robot_base" pos="0 0 0.05">
      <geom
        name="base_geom"
        type="cylinder"
        size="0.12 0.05"
        material="mat_robot"
      />

      <body name="upper_arm" pos="0 0 0.08">
        <!-- shoulder：绕 z 轴旋转的铰链关节 -->
        <joint
          name="shoulder"
          type="hinge"
          axis="0 0 1"
          range="-120 120"
        />

        <!--
          capsule 的 fromto 表示胶囊两端点坐标。
          它很适合用来表示机械臂连杆。
        -->
        <geom
          name="upper_arm_geom"
          type="capsule"
          fromto="0 0 0 0.55 0 0"
          size="0.035"
          material="mat_robot"
        />

        <body name="forearm" pos="0.55 0 0">
          <!-- elbow：同样绕 z 轴旋转 -->
          <joint
            name="elbow"
            type="hinge"
            axis="0 0 1"
            range="-135 135"
          />

          <geom
            name="forearm_geom"
            type="capsule"
            fromto="0 0 0 0.45 0 0"
            size="0.03"
            material="mat_robot"
          />

          <body name="end_effector" pos="0.45 0 0">
            <geom
              name="tip_geom"
              type="sphere"
              size="0.055"
              material="mat_tip"
            />

            <!--
              site 常用于：
              - 传感器参考点
              - 末端执行器位置标记
              - 可视化辅助点
            -->
            <site
              name="ee_site"
              pos="0 0 0"
              size="0.025"
              rgba="1 1 0 1"
            />
          </body>
        </body>
      </body>
    </body>

    <!--
      一个可自由运动、可碰撞的物体。
      freejoint 使该 body 拥有 6 自由度。
    -->
    <body name="free_box" pos="0.7 0.45 0.35">
      <freejoint name="box_free"/>
      <geom
        name="box_geom"
        type="box"
        size="0.08 0.08 0.08"
        material="mat_box"
        mass="0.2"
      />
    </body>
  </worldbody>

  <!--
    actuator：执行器
    motor 用于向指定 joint 施加控制输入。
    ctrlrange 表示控制量范围。
  -->
  <actuator>
    <motor
      name="shoulder_motor"
      joint="shoulder"
      gear="1.0"
      ctrlrange="-2 2"
    />
    <motor
      name="elbow_motor"
      joint="elbow"
      gear="1.0"
      ctrlrange="-2 2"
    />
  </actuator>

  <!--
    sensor：传感器
    用于读取仿真状态，例如关节角度、关节速度、末端位置等。
  -->
  <sensor>
    <jointpos name="shoulder_angle" joint="shoulder"/>
    <jointpos name="elbow_angle" joint="elbow"/>
    <jointvel name="shoulder_velocity" joint="shoulder"/>
    <jointvel name="elbow_velocity" joint="elbow"/>
    <framepos
      name="end_effector_position"
      objtype="site"
      objname="ee_site"
    />
  </sensor>

  <!--
    keyframe：关键帧
    用于保存一个初始姿态。

    本例中的 qpos 顺序为：
    1. shoulder
    2. elbow
    3. free_box 的 7 个 qpos

    freejoint 的 qpos 格式为：
    x y z qw qx qy qz
  -->
  <keyframe>
    <key
      name="home"
      qpos="25 -60  0.7 0.45 0.35  1 0 0 0"
      ctrl="0 0"
    />
  </keyframe>
</mujoco>
```

---

## 3. MJCF 文件结构说明

通过上面的示例可以看到，MJCF 文件通常按照如下层次组织：

```text
mujoco
├── compiler     # 编译相关设置
├── option       # 仿真参数
├── visual       # 可视化参数
├── default      # 默认属性
├── asset        # 材质、纹理、mesh 等资源
├── worldbody    # 世界中的物体、机器人、相机、光源等
├── actuator     # 执行器
├── sensor       # 传感器
└── keyframe     # 初始姿态或预设状态
```

其中：

* `worldbody` 是模型主体结构的核心部分。机器人、物体、地面、光源和相机通常都定义在这里。
* `actuator` 负责向关节施加控制输入。
* `sensor` 用于读取仿真过程中的状态信息。
* `keyframe` 可用于保存初始姿态或预设状态，便于快速恢复模型状态。

这个 demo 虽然很小，但已经覆盖了阅读和编写 MJCF 文件时最常见的几个模块。

---

## 4. 状态读取与 ID 查询

本部分主要学习以下内容：

* 关节位置读取
* 关节速度读取
* 末端位姿读取
* body ID 查询
* site ID 查询
* actuator 控制量读取

相关代码文件：

* `get_all_body_xpos.py`
* `get_all_body_qpos_qvel_ctrl.py`

建议重点关注以下 MuJoCo 数据结构：

* `model`

  * 存储模型的静态信息，例如 body、joint、site、actuator 的数量、名称和索引等。
* `data`

  * 存储仿真过程中的动态状态，例如 `qpos`、`qvel`、`ctrl`、`xpos` 等。

常见读取对象包括：

```python
data.qpos      # 广义坐标，例如关节角度、freejoint 位姿等
data.qvel      # 广义速度
data.ctrl      # actuator 控制输入
data.xpos      # body 的世界坐标位置
data.site_xpos # site 的世界坐标位置
```

---

## 5. PID / Position Actuator / Torque Actuator 学习

### 5.1 PID 控制

PID 相关代码见：

```text
PID.py
```

需要注意的是，当前所使用的 Panda 机械臂模型 `panda.xml` 中，执行器本身已经带有类似 PD 控制器的设置。例如：

```xml
<actuator>
  <general
    class="panda"
    name="actuator1"
    joint="joint1"
    gainprm="4500"
    biasprm="0 -4500 -450"
  />
</actuator>
```

这类 actuator 的本质并不是单纯的力矩输入，而是已经包含了类似 PD 控制的内部机制。

因此，如果在外层再写 PID，就会形成类似下面的结构：

```text
外层 PID
  ↓
生成目标角度
  ↓
内层 PD actuator
  ↓
生成实际控制力 / 力矩
```

也就是说，Panda 机械臂并不是最适合作为“从零实现 PID”的练习对象。

不过，本阶段主要以教育和理解为目的，因此暂时不深入考虑该嵌套控制结构带来的影响。

---

### 5.2 Position Actuator

Position actuator 通常用于输入目标关节位置，由 MuJoCo 内部根据 actuator 参数产生对应控制力。

适合用于：

* 关节位置控制
* 简单轨迹跟踪
* 快速验证机械臂运动逻辑

需要重点理解：

* actuator 输入并不一定等价于力矩。
* 对于 position actuator，`data.ctrl` 通常表示目标位置。
* 实际产生的控制力由 actuator 的增益、偏置和关节状态共同决定。

---

### 5.3 Torque Actuator

Torque actuator 更接近直接力矩控制。

适合用于：

* 自定义 PID / PD 控制
* 关节空间力矩控制
* 动力学控制算法验证

需要重点理解：

* 对于 torque actuator，`data.ctrl` 通常表示输入`力矩`。
* 控制器需要自己根据误差计算力矩。
* 相比 position actuator，torque actuator 更灵活，但也更容易不稳定。

---

## 6. 关节空间轨迹跟踪 Demo

本周最终目标是完成一个关节空间轨迹跟踪 demo。

建议 demo 包含以下基本流程：

1. 加载 MJCF 模型。
2. 获取需要控制的关节 ID。
3. 构造期望关节轨迹，例如：

   * 简单的插值轨迹
   
4. 在仿真循环中读取当前关节位置和速度。
5. 根据控制方式计算控制输入：

   * position actuator：直接输入目标关节角度
   * torque actuator：使用 PD / PID 计算控制力矩
6. 写入 `data.ctrl`。
7. 调用 `mujoco.mj_step(model, data)` 推进仿真。


---

## 7. 阶段总结

本周学习重点可以概括为：

1. 理解 MJCF 的基本文件结构。
2. 能够阅读简单的 MJCF 模型。
3. 掌握关节、body、site、actuator 的基本查询方式。
4. 能够读取关节状态和末端位姿。
5. 区分 position actuator 和 torque actuator 的控制含义。
6. 理解 Panda 模型中 actuator 自带 PD 控制这一点。
7. 完成一个关节空间轨迹跟踪 demo，为后续学习更复杂的机械臂控制打基础。
