# 01～20 教学数值与接口条件核对

本文行数：152行，预期阅读时长：12分钟

最近核对：2026-10-12。01～08 使用 [check_foundations.py](check_foundations.py)，09～11 使用 [check_advanced_examples.py](check_advanced_examples.py)，12～17 使用 [check_multimodal_examples.py](check_multimodal_examples.py)，18～20 使用 [check_robot_learning_examples.py](check_robot_learning_examples.py)；均为 Python 3.10.12 标准库程序。它们检查人工输入的计算、梯度、解析解与接口条件，不读取数据集、加载权重、训练真实模型或运行 ROS 2 与机器人。

## 实际核对结果

| 章节 | 教学计算结果 | 核对关注点 |
| --- | --- | --- |
| [01 KNN](../01_supervised_knn/README.md) | m/g 下距离约 `[200.000025,10.049876]`，m/kg 下约 `[0.223607,1.000050]` | 原始单位改变预测；同步归一化尺度后距离保持一致 |
| 01 | K=1 输出 B，K=3 等权输出 A，反距离加权输出 B | 邻居数与权重的区别；二点边界满足 `d_A²−d_B²=4x` |
| [02 回归](../02_regression/README.md) | w=0.5，b=7/6，MSE=1/18；一步梯度更新后 MSE=14/15 | 闭式解、残差驻点与梯度更新 |
| 02 | λ=1 时 L2 w=0.8、L1 w=1.25；λ=3 时 L2 w=4/11、L1 w=0 | 对最优系数的双侧扰动不会降低对应目标 |
| [03 预处理](../03_preprocessing_pipeline/README.md) | 年龄训练均值 30、标准差 10，验证 80 对应 z=5 | 复用训练统计；独热编码列与未知类别 |
| 03 | τ=0.3/0.5/0.8 时精确率为 0.6/0.666667/1，召回率为 1/0.666667/0.333333 | 混淆矩阵计数与样本总数一致 |
| [04 泛化](../04_model_selection/README.md) | 两种预测方案的期望 MSE 为 11/12 和 0.5 | 枚举训练预测与独立标签噪声，验证偏差—方差—噪声分解 |
| 04 | 训练轨迹 A/B、验证 C、测试 D | 轨迹编号不跨集合；不证明实际数据划分已通过 |
| [05 聚类与 PCA](../05_clustering/README.md) | 中心 `(0,1)`、`(8,1)`，SSE=4 | 二维中心更新与簇内平方距离 |
| 05 | 协方差对角为 64/3、4/3；投影 `[-4,−4,4,4]`；保留 16/17 方差 | 投影、重建误差与被丢弃的上下类别信息 |
| [06 反向传播](../06_pytorch_networks/README.md) | 梯度 `[-1,−2,−1,−0.25,−0.5]`；学习率 0.05 后 ŷ=2.135，L=0.0091125 | 每个参数的解析梯度与中央差分一致 |
| 06 | 学习率 0.1 后 L=0.302253125；交叉熵 logit 梯度约 `[-0.334759,0.244728,0.090031]` | 大步长可能增损失；交叉熵梯度亦用差分交叉核对 |
| [07 CNN](../07_transfer_learning/README.md) | 卷积图 `[[-4,−4],[-4,5]]`，ReLU 后全局平均为 1.25 | 互相关、激活与池化的不同含义 |
| 07 | 两层步幅 1 的 3×3 卷积感受野为 5×5；RGB 到两个通道的小层含 56 个参数 | 感受野递推与共享参数数目 |
| [08 机器人结合](../08_robot_integration/README.md) | 相机点 `[0.075,0.025,0.5] m`，基座点 `[0.7,−0.075,0.775] m`，教学 TCP 点 z=0.875 m | 刚体点变换往返与距离保持 |
| 08 | 原候选通过，10 个失败输入按预期拒绝；阈值边界通过 | 低分、非法数字、错坐标/时钟/类别、缺几何、范围与时效条件 |
| 08 | 0.2 m/s×0.25 s=0.05 m；26/40=65% | 延迟位移与条件阶段通过率的乘积 |

实际结果为 `checks_passed=17`，完整计算输出见[小型结果记录](results.json)。其中机器人筛选不判断物体朝向、IK、碰撞、夹爪接触或控制能力，不能用于声明抓取已验证。

第 02、04 章的合成回归图表与 7 项求解器检查仍单独保存在[容量实验记录](../02_regression/examples/capacity/README.md)；它们与本页的标准库手算核对范围不同。

## 维护时如何核对

从仓库根目录运行：

~~~bash
python3 src/machine_learning/examples/check_foundations.py
~~~

程序只向终端输出 JSON。命令供 agent 维护和读者按需查看，正文与上表已给出结果，不是必做练习。数值结果证明这些人工例子的计算一致，不代表历史模型重训、真实数据上的泛化或机器人闭环效果。

<a id="advanced"></a>

## 09～11：概率、模型与训练机制

标准库程序实际通过 **20 组检查**，计算输出见 [advanced_results.json](advanced_results.json)。表中的概率、标签、梯度序列和参数都是人工输入；解析解与小步更新没有使用 scikit-learn 或 PyTorch 求解器。

| 章节与检查组 | 结果 | 核对方法或边界 |
| --- | --- | --- |
| [09](../09_probability_uncertainty/README.md)：先验偏移 | π=0.5/0.1/0.01 时后验为 0.9/0.5/0.083333 | 贝叶斯、独立计数、赔率调整一致；依赖类别条件分布不变 |
| 09：位置统计 | 均值 0.5 m，方差 0.0002 m²，标准差约 14.14 mm | 两种方差公式一致；旋转后方差转移；±1σ 覆盖率仅 50% |
| 09：似然 | 最大似然 p=0.75，平均 NLL≈0.562335 | 数值差分驻点、邻近参数比较与标签逐项损失相符 |
| 09：校准组计数 | 0.9 分数组实际正类 80%；Brier 0.17→0.16 | 在给定标签组上，报正类频率使平方损失最小；未拟合校准器 |
| 09：熵与分歧 | 熵 0.693147/0.325083/0.056002 nat，模型熵差 0.368064 nat | 零概率边界与平均分布；不证明真实后验或异常输入识别 |
| [10](../10_classical_models/README.md)：逻辑回归 | XOR 原始特征驻点为 0；交互特征概率约 0.119203/0.880797 | 各参数中央差分和扰动目标；指定交互系数未拟合 |
| 10：线性 SVM | 对称驻点平均 hinge=1 | 差分梯度、参数扰动与多个同最优偏置 |
| 10：RBF SVM | α≈1.337533，训练间隔为 1；查询分数≈0.818561 | 对偶可行性、间隔条件、原始与对偶目标一致；解析解 |
| 10：树切分 | 根 Gini=0.5，任一轴首次改善为 0 | 独立统计叶子；手工深度 2 树正确，未运行树训练 |
| 10：森林汇总 | 纯叶子 `[1,1,0]` 平均 2/3；混合叶子 `[0.51,0.51,0]` 平均 0.34 | 硬投票与概率平均可能不同；三棵树均为手工构造 |
| 10：梯度提升 | η=1/0.1 后交叉熵 0.474077/0.668460 | 负梯度与差分相符；树桩每叶负梯度均值为 0 |
| 10：同组查询比较 | 线性方法漏检 2 个；其余指定方法四点正确 | 实际计算表中边界输出；查询标签人为给定，不是泛化评估 |
| [11](../11_training_optimization/README.md)：梯度链与初始化 | 20 层比例约 9.54×10⁻⁷ / 3,325.257 | 导数与差分相符；Xavier/He 标准差 0.1/0.141421 |
| 11：学习率 | 初始 loss=50.5；η=0.1/0.01 后 4,050.405/0.49005 | 二次损失差分梯度与长期收敛、边界及发散情况 |
| 11：SGD 与动量 | 两步后 θ=0.9/0.72 | 同一固定梯度序列，分别核对更新与速度状态 |
| 11：Adam | 两步后 θ≈0.873366 | 递推状态与历史梯度权重展开一致，包含偏差修正 |
| 11：权重衰减 | SGD / Adam 合入 L2 / AdamW 首步约 0.98/0.90/0.89 | SGD 等价式、两种自适应更新的不同公式；未调用优化器 |
| 11：裁剪 | `(3,4)`→`(0.6,0.8)` | 范数变为 1、方向保持，较小范数不改变 |
| 11：归一化 | BN 训练 `[-1,1]`、评估 `[0.5,1.5]`；LN 每样本 `[-1,1]` | 统计维度与总体/无偏方差区别；本例 ε=0，未模拟运行统计更新 |
| 11：Dropout | 四种输出的期望为 `[2,4]`；标量训练期望损失 4、评估损失 2 | 枚举全部等概率掩码，区分激活期望和非线性损失 |

11 的[训练曲线图](../11_training_optimization/training_curves_illustration.png)已用 Python 3.10.12、Matplotlib 3.5.1 生成并检查。图中数据是人工构造的五轮序列，不能当作本轮或历史模型训练记录；[绘图源码](../11_training_optimization/plot_training_curves.py)保留供维护参考。

维护命令：

~~~bash
python3 src/machine_learning/examples/check_advanced_examples.py
MPLCONFIGDIR=/tmp/robotics-ml-mpl python3 src/machine_learning/11_training_optimization/plot_training_curves.py
~~~

第一条只输出 JSON；第二条重画人工曲线，需要 Matplotlib，不是数值检查的依赖。正文已提供所有结果，读者无需运行。09～11 没有实际模型拟合、深度训练、概率校准评估、PyTorch 运行时对照或机器人闭环验证。

<a id="multimodal"></a>

## 12～17：视觉、序列、VLM 与生成机制

[check_multimodal_examples.py](check_multimodal_examples.py)实际通过 **33 组检查**，完整输入与结果见 [multimodal_results.json](multimodal_results.json)。不是深度模型训练测试、COCO 评估或 Diffusion Policy 运行；去噪采样使用人工已知真噪声，称为 oracle 仅表示它掌握了这项输入。

| 章节 | 检查组数 | 核对过的教学结果 |
| --- | ---: | --- |
| [12 视觉输出](../12_detection_segmentation/README.md) | 6 | 框 IoU=2/3，NMS 保留首个与第三个框；一对一匹配 `[TP,FP,TP]`，非插值 AP=5/6；掩码 IoU=0.5、Dice=2/3；关键点误差 5 px；补边框 `[42,77,77,133]` 往返 |
| [13 序列](../13_sequence_models/README.md) | 5 | 相同当前位置外推 0.3/0.1 m；递推 `[0,1,2.5]` 与反序 `[2,2,1]`；共享参数梯度 −0.5；GRU 保留门 0.1/0.9 时状态 0.26/0.74；四个 token 平均 NLL≈0.383119 |
| [14 注意力](../14_attention_transformer/README.md) | 7 | 第二位置非因果输出约 `[0.598888,1.604448]`、因果输出 `[0.330238,1.339523]`；交叉输出 `[6.697615,6.604769]`；位置、多头、下一 token 与逐步单层缓存；教学 KV 为 25,600 字节 |
| [15 表示学习](../15_representation_learning/README.md) | 5 | 两输入同编码 h=1、重建损失 1；正例概率≈0.982014、loss≈0.018150；坍塌对比 loss=ln2；翻转框 `[420,140,520,300]`；掩码 MSE=0.25、49 个可见 patch |
| [16 VLM 深化](../16_vision_language/README.md) | 4 | 候选变化使红杯概率约 0.598688/0.999999998/0.374487；两查询压缩四项视觉表示；冻结模块仍传回梯度 −18，一步后 loss=1.8432；固定答案普通正确率 50%、成对正确率 0%，错对象 IoU=0 |
| [17 生成与扩散](../17_generative_models/README.md) | 6 | 双峰均值损失更低但不在模式上；路径均值撞障碍；x₀=2 加噪得 x₂=1，预测偏差后恢复 1.85；oracle DDPM 均值≈1.490712、方差 1/9；oracle DDIM 回到 2；引导 s=2 时噪声预测 −1 |

关键性质还做了独立核对：

- 框缩放后 IoU 不变，非法/空框被拒绝；重复预测不能重复匹配同一真值。
- RNN 共享参数、对比损失与冻结连接器的解析梯度和中央差分一致；padding 不改变有效 token 平均损失。
- 扰动未来输入后，因果输出前两项保持不变；所有位置被屏蔽时拒绝无效 softmax。
- K/V 同步重排不改变 cross-attention 输出；不含位置的 self-attention 满足相应置换性质；单层逐步 KV cache 与完整因果前缀一致。
- 图像坐标翻转两次恢复原框；只在遮住位置计预测误差，未用可见位置稀释 loss。
- 扩散链一、二阶矩一致；噪声误差传播与差分一致；oracle DDPM 均值与已知 x₀ 的条件后验公式一致。矩核对用独立零均值、单位方差的离散变量枚举，不把它们当成高斯分布或生成质量评估。

原有 VLM 的 [8 组核对](../16_vision_language/examples/README.md)也在本轮重新运行通过，源码保留。新增两张图使用 Python 3.10.12、Matplotlib 3.5.1 实际生成并检查：[同场景视觉输出](../12_detection_segmentation/vision_outputs_illustration.png)、[绕障与均值](../17_generative_models/trajectory_modes_illustration.png)；它们来自手工形状和解析路径。

维护命令：

~~~bash
python3 src/machine_learning/examples/check_multimodal_examples.py
MPLCONFIGDIR=/tmp/robotics-ml-mpl python3 src/machine_learning/examples/plot_multimodal_examples.py
python3 src/machine_learning/16_vision_language/examples/check_numeric_examples.py
~~~

数值程序只输出 JSON，绘图程序只重画指定教学输入。没有新数据训练、真实 tokenizer、视觉/语言网络、VLM 换图推理、扩散去噪器或机器人执行；本文结果不证明真实任务的准确率、概率校准、泛化或闭环成功。

<a id="robot-learning"></a>

## 18～20：动作学习、回报与泛化评价

2026-10-12 实际运行 [check_robot_learning_examples.py](check_robot_learning_examples.py)，**26 组检查通过**，输入与结果保存在 [robot_learning_results.json](robot_learning_results.json)。其中 episode、成功数与扰动结果均为人工构造；没有 BC、ACT、Diffusion Policy、PPO 或 SAC 训练，也没有机器人 rollout。

| 章节 | 检查组数 | 已核对的教学结果 |
| --- | ---: | --- |
| [18 模仿学习](../18_imitation_learning/README.md) | 7 | BC 解析增益 0.2，初始动作 RMSE≈14.14 mm；理想 reaching 第 20 步误差≈1.153 mm；固定偏差回放 20 mm、反馈约 4.942 mm；偏离状态专家增量 −4 mm；四步块执行前两步到 0.236 m；同刻集成目标≈0.251333 m |
| [19 强化学习](../19_reinforcement_learning/README.md) | 10 | 回报 6.2；三状态 V 为 0.8/1/0；四次 Q 更新 0.5/0.175/0.75/0.375；策略梯度与基线期望均为 0.25；PPO 裁剪项 2.4/−1.6；SAC 目标 0.665；受限增量≈0.048201 m；终止/外部截断目标 −0.1/0.62；错误等待奖励产生价值 2 |
| [20 泛化与迁移](../20_generalization_sim2real/README.md) | 9 | 轨迹分组无交集；保持容差从 0.1 到 0.6 s；人工扰动比例 90%/75%/60%/55%/35%；8/10 与 80/100 的 Wilson 区间；合计/场景等权为 76%/55%；质量加倍使质点位移减半；延迟位置差 50 mm；限幅后 +5/−10 mm；恢复不增加任务分母 |

除逐项数值比较外，还检查：

- BC 损失的中央差分与解析梯度一致，扰动最优参数会增加损失；位置目标、增量与速度不能混用。
- 反馈递推与幂级数展开一致；动作块末尾填充不计入损失，未跨 episode 拼接标签。
- Bellman 最优值迭代与完整奖励展开一致；策略梯度通过动作枚举与数值差分独立比较，动作无关基线不改变期望。
- PPO 在两种已超出改善范围的比率处，裁剪目标的差分梯度为零；不将此性质当作策略距离硬约束。
- tanh 动作雅可比与差分一致；在物理动作坐标对密度积分，与原高斯区间概率一致，包含动作尺度修正。
- Wilson 端点满足原评分检验方程，成功/失败互换后区间互补；全成功/全失败边界仍在 `[0,1]`。
- 持续时间按时间差计算；中途越界或 NaN 会重置保持计时。限幅检查边界与五种无效输入，不覆盖机械臂执行保护。

[误差曲线](robot_learning_error_illustration.png)使用 Matplotlib 3.5.1 从已核对的递推结果生成并视觉检查；[绘图程序](plot_robot_learning_examples.py)保留。横轴为 0.1 s 控制周期下的时间，纵轴为毫米，图中明确标注无训练或机器人执行。

维护命令：

~~~bash
python3 src/machine_learning/examples/check_robot_learning_examples.py
MPLCONFIGDIR=/tmp/robotics-ml-mpl python3 src/machine_learning/examples/plot_robot_learning_examples.py
~~~

数值程序只输出 JSON；绘图程序读取保存的人工结果重画曲线。正文已给出输入、结果与解释，读者无需执行。01～20 四个共享程序合计 **96 组**教学检查，原 VLM 另有 8 组；检查组数不等于模型能力、策略泛化或机器人验收项数。

[机器学习目录](../README.md) · [20 章工作目录](../机器学习入门实战清单.md) · [核对记录](../verification.md)
