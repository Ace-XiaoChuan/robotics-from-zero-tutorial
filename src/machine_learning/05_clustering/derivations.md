# K-Means 与 PCA：从目标函数求导到中心、投影与重建

本文行数：303行，预期阅读时长：12分钟

本页补齐两条计算链：K-Means 为什么把非空簇的均值作为中心，PCA 为什么把协方差矩阵的特征向量作为主方向。先读[本章入口](README.md)中的分组和轴对齐例子，再按需要查看这里的求导；本文新例为无量纲教学数据，不是客户实测结果。

## K-Means：固定分组，对中心的每个分量求导

### 先分清正在改变什么

有 N 个样本，每个样本有 D 个特征。数学中把单个样本写成列向量 $x_i\in\mathbb R^D$，代码中数据表 X 的形状为 `[N,D]`，每行存一个样本。K 个中心记为 $\mu_k\in\mathbb R^D$，`cluster_centers_` 的形状为 `[K,D]`；簇编号 $c_i$ 是整数。

平方距离目标为：

$$
J(c,\mu)=\sum_{i=1}^{N}\|x_i-\mu_{c_i}\|_2^2.
$$

固定中心时，每个样本独立选择最近的中心；距离与平方距离的最小者相同。固定分组时，属于第 k 簇的索引集合 $C_k=\{i:c_i=k\}$ 不变，样本数为 $n_k=|C_k|$，只更新中心。下面求导的是后一步；离散簇编号没有被当作连续变量求导。

### 平方距离展开后，各维可以分别求解

第 k 簇的贡献为：

$$
J_k(\mu_k)
=\sum_{i\in C_k}\sum_{j=1}^{D}(x_{ij}-\mu_{kj})^2.
$$

对中心的第 j 个分量 $\mu_{kj}$ 求偏导时，其他维的项都是常数。单项用链式法则：

$$
\frac{\partial (x_{ij}-\mu_{kj})^2}{\partial\mu_{kj}}
=2(x_{ij}-\mu_{kj})(-1)
=2(\mu_{kj}-x_{ij}).
$$

样本固定，可以先逐项求导再相加：

$$
\frac{\partial J_k}{\partial\mu_{kj}}
=2\sum_{i\in C_k}(\mu_{kj}-x_{ij})
=2n_k\mu_{kj}-2\sum_{i\in C_k}x_{ij}.
$$

令这个分量的导数为零。对于非空簇 $n_k>0$，两边先除以 2，再除以 $n_k$：

$$
2n_k\mu_{kj}-2\sum_{i\in C_k}x_{ij}=0
\quad\Longrightarrow\quad
\mu_{kj}=\frac{1}{n_k}\sum_{i\in C_k}x_{ij}.
$$

对所有 D 个分量这样处理，得到向量形式：

$$
\nabla_{\mu_k}J_k
=2\left(n_k\mu_k-\sum_{i\in C_k}x_i\right),
\qquad
\mu_k=\frac{1}{n_k}\sum_{i\in C_k}x_i.
$$

梯度与中心同为 D 维；它表示中心各分量增大时，平方误差如何变化。二阶导数矩阵为 $2n_kI_D$。非空时它正定，因此这个驻点是**固定分组下唯一的最小值**，而不只是某个导数为零的位置。

若簇为空，$J_k=0$，任何中心都给出相同贡献，梯度也恒为零；此时既不能除以 $n_k=0$，也不能从目标推出一个唯一中心。空簇重新定位属于算法实现处理。

### 对照现有二维例子

左簇包含 `(0,0)` 与 `(0,2)`，设中心为 $(a,b)$：

$$
J_1(a,b)=a^2+b^2+a^2+(2-b)^2
=2a^2+2b^2-4b+4.
$$

$$
\frac{\partial J_1}{\partial a}=4a=0,
\qquad
\frac{\partial J_1}{\partial b}=4b-4=0
\quad\Longrightarrow\quad
(a,b)=(0,1).
$$

右簇同理得到 `(8,1)`。这对应源码中 K-Means 的中心更新；正式客户脚本由 scikit-learn 完成这些步骤。固定分组时更新中心、固定中心时重新分配，都不增加当前目标，但多个变量交替更新仍可能停在局部解；不能把上面的凸性结论扩大成整个 K-Means 的全局最优保证。[K-Means 官方说明](https://scikit-learn.org/1.7/modules/clustering.html#k-means)

## PCA：投影方差为什么变成特征值问题

### 数据先减均值，再投影

仍用 N 行、D 列数据，要求 $N\ge2$。PCA 的列均值记为 $m\in\mathbb R^D$，以免与 K-Means 的多个中心混淆。定义：

$$
m=\frac1N\sum_{i=1}^{N}x_i,
\qquad
x_{c,i}=x_i-m,
\qquad
S=\frac{X_c^{\mathsf T}X_c}{N-1}.
$$

$X_c$ 形状为 `[N,D]`，每行是 $x_{c,i}^{\mathsf T}$；S 形状为 `[D,D]`，是对称、半正定的样本协方差矩阵。减均值后 $\sum_i x_{c,i}=0$，所以任意固定方向上的投影也具有零均值。

选列向量 $u\in\mathbb R^D$，单个样本的得分 $z_i=x_{c,i}^{\mathsf T}u$ 是标量。整列得分 $z=X_cu$ 的形状为 `[N,1]`。由零均值得分的样本方差出发：

$$
\begin{aligned}
\operatorname{Var}(z)
&=\frac1{N-1}\sum_{i=1}^{N}z_i^2\\
&=\frac1{N-1}(X_cu)^{\mathsf T}(X_cu)\\
&=u^{\mathsf T}\left(\frac{X_c^{\mathsf T}X_c}{N-1}\right)u\\
&=u^{\mathsf T}Su.
\end{aligned}
$$

这不是新增的近似：第一行是样本方差定义，第二行把平方和写为向量内积，第三行使用矩阵连乘规则，最后代入 S。若不限制 u 的长度，只要有非零方差方向，就能把 u 放大而让方差无限增加；因此主方向必须是单位向量。

### 用拉格朗日函数处理单位长度约束

第一主方向求解：

$$
\max_u\ u^{\mathsf T}Su,
\qquad u^{\mathsf T}u=1.
$$

引入标量乘子 $\lambda$，把约束写进拉格朗日函数：

$$
\mathcal L(u,\lambda)
=u^{\mathsf T}Su-\lambda(u^{\mathsf T}u-1).
$$

先展开 $u^{\mathsf T}Su=\sum_{j=1}^{D}\sum_{k=1}^{D}u_jS_{jk}u_k$。对第 l 个分量 $u_l$ 求导时，左侧的 $u_j$ 与右侧的 $u_k$ 都会产生贡献：

$$
\begin{aligned}
\frac{\partial(u^{\mathsf T}Su)}{\partial u_l}
&=\sum_{k=1}^{D}S_{lk}u_k+\sum_{j=1}^{D}u_jS_{jl}\\
&=2\sum_{k=1}^{D}S_{lk}u_k.
\end{aligned}
$$

第二步用到 S 的对称性 $S_{jl}=S_{lj}$；如果矩阵不对称，梯度应为 $(S+S^{\mathsf T})u$，不能直接写成 $2Su$。约束项的偏导为 $-2\lambda u_l$，所以全部分量组成的梯度及乘子导数为：

$$
\nabla_u\mathcal L=2Su-2\lambda u,
\qquad
\frac{\partial\mathcal L}{\partial\lambda}=1-u^{\mathsf T}u.
$$

同时令两者为零，就得到：

$$
Su=\lambda u,
\qquad u^{\mathsf T}u=1.
$$

这正是单位特征向量与特征值的关系。再左乘 $u^{\mathsf T}$，代入单位长度：

$$
u^{\mathsf T}Su=\lambda u^{\mathsf T}u=\lambda.
$$

因此该方向上的投影方差等于对应特征值。这里乘子最终成为方差值，不是人为设置的学习率。

### 为什么选最大特征值，而不随便选一个驻点

S 是实对称矩阵，可取正交单位特征向量 $v_1,\ldots,v_D$，特征值按 $\lambda_1\ge\cdots\ge\lambda_D\ge0$ 排列。把任意单位方向写成 $u=\sum_j a_jv_j$，则 $\sum_j a_j^2=1$。利用特征方程与正交性：

$$
u^{\mathsf T}Su
=\sum_{j=1}^{D}\lambda_ja_j^2
\le\lambda_1\sum_{j=1}^{D}a_j^2
=\lambda_1.
$$

取 $u=v_1$ 能达到这个上界，所以第一主方向应选最大特征值对应的向量。求导为零只给出所有候选驻点；这个上界解释了怎样从中选择最大值。若最大特征值重复，其特征子空间中的单位方向都能取得同样方差，主方向不唯一。

第二方向还要避免重复描述第一方向：$u_2^{\mathsf T}u_2=1$、$u_1^{\mathsf T}u_2=0$。增加正交约束乘子 $\gamma$ 后：

$$
\mathcal L_2
=u_2^{\mathsf T}Su_2-\lambda(u_2^{\mathsf T}u_2-1)
-\gamma u_1^{\mathsf T}u_2,
\qquad
2Su_2-2\lambda u_2-\gamma u_1=0.
$$

左乘 $u_1^{\mathsf T}$。因为 $Su_1=\lambda_1u_1$、S 对称且 $u_1^{\mathsf T}u_2=0$，前两项为零，得到 $\gamma=0$。第二方向因此也是特征向量；在与第一方向正交的子空间中选剩余最大特征值 $\lambda_2$。后续方向同理。这解释了“依次保留最多变化”，而不是对第一方向随意转一个角度。

### 多个方向怎样组成得分与重建

保留 R 个正交方向，按列组成 $U_R=[u_1,\ldots,u_R]$，形状 `[D,R]`，满足 $U_R^{\mathsf T}U_R=I_R$。代码一般用行样本，因此整张表的投影与重建是：

$$
Z=X_cU_R\quad[N,R],
\qquad
\widehat X=X_cU_RU_R^{\mathsf T}+\mathbf1_Nm^{\mathsf T}
=ZU_R^{\mathsf T}+\mathbf1_Nm^{\mathsf T}\quad[N,D].
$$

$\mathbf1_N$ 是 N 维全 1 列向量，最后一项给每行加回训练均值。单个样本重建为 $\widehat x_i=m+\sum_{j=1}^{R}z_{ij}u_j$；没有保留的方向无法从 Z 恢复。

在正交特征方向上，被删除部分与保留部分互相垂直，每个删除方向的训练得分平方和为 $(N-1)\lambda_j$，所以：

$$
\sum_i\|x_i-\widehat x_i\|_2^2
=(N-1)\sum_{j=R+1}^{D}\lambda_j.
$$

总方差非零时，保留方差比例为 $\sum_{j=1}^{R}\lambda_j/\sum_{j=1}^{D}\lambda_j$。最大化保留方差也等价于最小化这种欧氏重建平方误差；它没有使用类别或机器人任务标签。

## 带交叉项的二维例子：主方向不沿原坐标轴

令 $r=\sqrt3/2\approx0.8660254$，四个无量纲样本如下，均值为 $m=(2,1)^{\mathsf T}$：

| 样本 | 原始点 $x_i$ | 中心化后的 $x_{c,i}$ |
| --- | --- | --- |
| 1 | $(2+3r,1+3r)$ | $(3r,3r)$ |
| 2 | $(2-3r,1-3r)$ | $(-3r,-3r)$ |
| 3 | $(2+r,1-r)$ | $(r,-r)$ |
| 4 | $(2-r,1+r)$ | $(-r,r)$ |

两个对角协方差都是 $(9+9+1+1)r^2/3=5$；交叉项为 $(9+9-1-1)r^2/3=4$。分母 3 来自 $N-1$，因此：

$$
S=\begin{bmatrix}5&4\\4&5\end{bmatrix},
\qquad
\det(S-\lambda I)=(5-\lambda)^2-16
=(\lambda-9)(\lambda-1)=0.
$$

特征值为 9 与 1。代入 $Su=\lambda u$：当 $\lambda=9$ 时，$-4u_x+4u_y=0$，即两分量相等；归一化后取 $u_1=(1,1)^{\mathsf T}/\sqrt2$。当 $\lambda=1$ 时，$4u_x+4u_y=0$，两分量互为相反数，取 $u_2=(1,-1)^{\mathsf T}/\sqrt2$。

它们长度为 1、内积为零，而且 $Su_1=9u_1$、$Su_2=u_2$。两个原始特征一起增减使沿 45° 的第一方向变化最大；保留方差为 $9/(9+1)=90\%$。

定义 $a=3\sqrt{3/2}\approx3.6742346$、$b=\sqrt{3/2}\approx1.2247449$。得分是点积，重建是沿方向加回均值：

| 样本 | 第一得分 $z_{i1}=x_{c,i}^{\mathsf T}u_1$ | 第二得分 $z_{i2}=x_{c,i}^{\mathsf T}u_2$ | 只保留第一方向的重建 |
| --- | ---: | ---: | --- |
| 1 | a | 0 | $(2+3r,1+3r)$ |
| 2 | −a | 0 | $(2-3r,1-3r)$ |
| 3 | 0 | b | $(2,1)$ |
| 4 | 0 | −b | $(2,1)$ |

例如第一点的得分为 $(3r+3r)/\sqrt2=a$，所以 $au_1=(3r,3r)^{\mathsf T}$。第三点的第一得分为 $(r-r)/\sqrt2=0$，删去第二方向后就只能重建到均值。后两点各有平方误差 $2r^2=1.5$，总误差为 3，与 $(N-1)\lambda_2=3\times1$ 一致。保留两个方向则可以重建全部四点。

把任意主方向整体取反，对应得分也取反，重建中的乘积 $z_{ij}u_j$ 不变。软件与手算的主成分符号不同不代表结果错误；应比较方向张成的轴、投影关系与重建结果。

## 和本章 PCA 源码怎样对应

[compare_k2_k3.py](src/compare_k2_k3.py)读取六个已做 `log1p + RobustScaler` 的特征，调用一次 `pca.fit_transform(features)` 得到两列绘图得分，再对 K-Means 中心调用同一个 `pca.transform(center_frame)`。K=2 和 K=3 的图因此共享均值、方向与坐标，不是分别拟合两套 PCA。[通用可视化脚本](src/fit_and_visualize_clusters.py)也在预处理后的输入上拟合 PCA。

默认 `whiten=False` 时，下面的接口对应本页的普通正交投影：

| Python 属性或方法 | 对应数学量与形状 |
| --- | --- |
| `pca.mean_` | 拟合输入的列均值 m，`[D]` |
| `pca.components_` | 每行一个主方向，等于 $U_R^{\mathsf T}$，`[R,D]` |
| `pca.explained_variance_` | 保留方向的样本方差，即前 R 个特征值，`[R]` |
| `pca.explained_variance_ratio_` | 各保留方向方差除以全部方向总方差，`[R]` |
| `pca.transform(X)` | `(X - pca.mean_) @ pca.components_.T`，`[N,R]` |
| `pca.inverse_transform(Z)` | `Z @ pca.components_ + pca.mean_`，`[N,D]` |

PCA 会减去**当前拟合输入的平均值**，不会自动将各列缩放成单位方差；`explained_variance_` 使用 `N−1` 分母。启用 `whiten=True` 会进一步缩放得分，不能原样套用表中的普通投影等式。[scikit-learn 1.7 PCA API](https://scikit-learn.org/1.7/modules/generated/sklearn.decomposition.PCA.html)

本章正式输入已经经过 RobustScaler 的中位数/IQR 变换；PCA 再对该空间减均值，这两次处理没有矛盾。重建也先得到这个处理空间中的数据；若要回到原始消费金额，还需按原预处理关系还原。`log1p` 的逆变换是 `expm1`，此前六位小数舍入已经丢失的信息无法精确恢复。玩具四点例子没有缩放，按同一无量纲单位直接计算样本协方差。

下面只对上面的四点拟合小模型，避免把数学例子与客户实验混在一起：

```python
import numpy as np
from sklearn.decomposition import PCA

r = np.sqrt(3) / 2
X = np.array([[2 + 3*r, 1 + 3*r], [2 - 3*r, 1 - 3*r],
              [2 + r, 1 - r], [2 - r, 1 + r]])  # [4,2]
pca = PCA(n_components=1, svd_solver="full", whiten=False)
Z = pca.fit_transform(X)                          # [4,1]
X_rebuilt = pca.inverse_transform(Z)              # [4,2]
print(pca.mean_)                                 # [2,1]
print(pca.components_)                           # [1,2]；u1 的正或负方向
print(pca.explained_variance_)                    # [9]
print(pca.explained_variance_ratio_)              # [0.9]
```

这个例子只保留第一主方向；正式脚本保留两个方向，其 `components_` 为 `[2,6]`，图中坐标为 `[440,2]`。投影 K 个中心的输入为 `[K,6]`，输出为 `[K,2]`，同样要减去拟合 PCA 时的训练均值。

## 数值核对

[check_derivations.py](check_derivations.py)默认只用标准库，核对固定分组中心梯度的有限差分、均值最小值、空簇条件、PCA 方差梯度、四点样本协方差、特征方程与正交性、得分和重建误差，以及符号翻转后的重建一致性。它不读取客户数据、训练正式聚类模型或生成输出资产。

本机复核：标准库 7 项全部通过；加入 scikit-learn 1.7.2 / NumPy 2.2.6 的实际 PCA 接口后，8 项全部通过。中心梯度采用中心差分步长 `h=1e-5`，最大绝对差约 `2.813e-10`；四点接口核对包含方差 `[9,1]`、比例 `[0.9,0.1]` 与一维重建误差总和 3。

```bash
# 从仓库根目录运行；只用 Python 标准库。
python3 src/machine_learning/05_clustering/check_derivations.py
# 已有 NumPy / scikit-learn 环境时，再核对 PCA 的实际接口。
python3 src/machine_learning/05_clustering/check_derivations.py --sklearn
```

有限差分核对的是导数和实现的一致性；四点的 90% 方差比例与总重建误差 3 是明确教学输入的数值结果，不是客户案例性能。

[本章入口](README.md) · [客户案例实现说明](reference.md)
