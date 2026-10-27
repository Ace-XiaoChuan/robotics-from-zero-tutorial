# 03：怎样读懂和组织 MJCF 场景

本文行数：93行，预期阅读时长：5分钟

## 开发者理解：找到每项场景信息的归属

一份机械臂场景可能包含多个 XML 文件和很多网格。阅读时先找到“整个场景的入口”，再分辨机器人结构、外部资源和全局设置。这样，当你想增加桌面、改质量或换相机时，能定位该改哪一部分。

MJCF 是 MuJoCo 的场景描述格式，本质是以 XML 来表达结构和参数。**文件的组织关系与机器人的父子关系是两件事：include 组合文件，body 嵌套定义空间层级。** XML 文件本身不负责循环步进或自动执行任务。

## 速记：先看哪些部分

| 部分 | 放什么 | 典型问题 |
| --- | --- | --- |
| `compiler` | 编译时的角度约定、资源目录等 | XML 中的角度是度还是 rad |
| `option` | 重力、物理步长、积分器等 | 物理计算采用什么条件 |
| `default` | 一组元素的默认属性 | 为什么很多 joint 没有显式写阻尼 |
| `asset` | mesh、材质、纹理等可引用资源 | 外观和网格从哪里来 |
| `worldbody` | 机器人、地面、物体、相机与灯光 | 场景里有什么、怎样摆放 |
| `actuator` | 执行器及其传动关联 | 哪个输入作用于哪个关节 |
| `sensor` | 需要生成的传感器输出 | 要读什么量、维度多大 |
| `equality` / `tendon` | 等式约束或肌腱传动等关系 | 独立关节之间是否存在额外耦合 |
| `keyframe` | 可命名的状态与输入参考值 | 是否提供了 home 等初始构型 |

这些部分按需要出现。第一个单摆不需要 mesh、纹理或复杂约束；先看懂少量对象，也能理解一个完整的仿真循环。

## 例子：机器人文件与场景文件怎样合作

本教程的两关节机械臂使用以下布局：

```text
models/
├── arm_scene.xml       场景入口：全局设置、默认属性、地面、灯光和相机
└── planar_arm.xml      被 include 的结构、执行器、传感器与 home
```

[arm_scene.xml](../mujoco/models/arm_scene.xml) 中的核心关系如下，完整可编译文件见链接：

```xml
<mujoco model="tutorial_planar_arm_scene">
  <compiler angle="radian"/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <default>
    <default class="arm">
      <joint type="hinge" axis="0 0 1" damping="0.1" armature="0.01" limited="true"/>
      <geom type="capsule" size="0.025" contype="0" conaffinity="0"/>
    </default>
  </default>
  <include file="planar_arm.xml"/>
  <!-- worldbody 中还定义地面、相机和灯光 -->
</mujoco>
```

这个片段用于展示组织方式，省略了被引用的文件内容和环境。完整场景编译后，机械臂有两个 hinge、两个位置执行器、五个传感器，`nq=2、nv=2、nu=2`。地面与相机没有增加机器人运动自由度。

被包含的 [planar_arm.xml](../mujoco/models/planar_arm.xml) 用 `<mujocoinclude>` 包住片段。加载入口时，编译器把其内容插入 include 所在位置。它依赖入口中的 `arm` 默认类，不能把它当作一个独立场景直接加载。

## default、class 与 childclass 怎样理解

默认类可以看成一组预先填写的属性。它减少重复，但也意味着“这个元素没写某属性”不代表该属性不存在。

本例在 `arm` 类中声明 joint 阻尼为 `0.1 N·m·s/rad`，机器人根 body 使用 `childclass="arm"`，其内部与后代的 joint、geom 继承相应默认值。因此 shoulder 与 elbow 都有这个阻尼，检查结果为 `[0.1, 0.1]`。

查一个属性时按以下顺序理解：

1. 元素显式填写的属性优先，例如 forearm geom 单独指定颜色。
2. 元素有 `class` 时使用该类的默认属性。
3. 未显式选类时，查看最近祖先 body 的 `childclass`，再追溯默认类的继承关系。
4. 没有相应选择时使用顶层默认类；仍未修改的值来自 MuJoCo 内置默认值。

`class` 选择当前元素使用的默认类，`childclass` 为 body 内部和后代提供默认类。默认类中的 dummy joint、geom 不是场景中的实际对象，不会额外生成关节。

执行器的 position、motor 等写法属于快捷定义，也会影响内部参数；修改默认执行器时要核对具体类型。初学时建议在少量实际执行器上显式写清输入范围和关键增益，见[第六章](../06_actuation/README.md)。

## asset 定义资源，geom 引用资源

假设想显示一只夹爪：先在 `asset` 声明 mesh，随后在某个 body 内用 geom 引用它。**有 mesh 资源不等于场景中已有一个物体。** 物体的空间位置来自 body/geom，动力学行为来自质量、惯量、关节与接触设置。

外观精细的网格也不保证碰撞同样精细。常规刚性 mesh 的碰撞通常使用凸包；凹槽、空腔等需要合适的碰撞建模方法，见[接触章节](../08_contact_constraints/README.md)。

`include`、`meshdir` 和资源文件都是模型依赖。相对 include 按模型文件的包含关系解析，不是随意依赖终端当前目录；资源目录的完整规则查[官方文件引用说明](https://mujoco.readthedocs.io/en/3.13.0/XMLreference.html#include)。迁移模型时应保留原目录结构，并实际加载确认。

## 从 URDF 或外部机械臂模型开始

URDF 主要描述机器人的连杆与关节；MJCF 可以一起描述仿真环境、执行器、传感器和接触。URDF 导入后的模型仍需检查惯性、碰撞、驱动和场景设置；原系统的控制器不会随 URDF 自动变成 MuJoCo 执行器。

Panda 等机械臂可参考官方 [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie)。使用时保留许可证、完整资源及实际 commit SHA。通常 `scene.xml` 是带环境的入口，机器人 XML 是可复用部分，具体以该模型 README 为准。

本教程用自建两关节模型完成综合例子，方便直接看清结构和输入映射。以后换成 Panda，首先沿用同样的检查顺序：入口与依赖 → 关节与工具 → 执行器 → 初态 → 数值运行。

资料：[MJCF 建模与默认类](https://mujoco.readthedocs.io/en/3.13.0/modeling.html) · [XML 元素参考](https://mujoco.readthedocs.io/en/3.13.0/XMLreference.html)

[上一章：对象与空间关系](../02_scene_objects/README.md) · [返回目录](../README.md) · [下一章：model 与 data](../04_model_data/README.md)
