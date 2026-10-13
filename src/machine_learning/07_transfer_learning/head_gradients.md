# 分类头的完整求导：从固定特征到一步 SGD

本文行数：221行，预期阅读时长：8分钟

冻结特征提取部分后，训练仍需要回答一个具体问题：一张纸板图片被预测为纸张，怎样从这个错误算出分类头每个权重与偏置的改变量？本页沿用 [README](README.md#例子分类头学的是什么) 的两维特征，把前向、损失、求导与更新连起来。

**教学结果：** 正确类别纸板的概率由 `0.259496` 增至 `0.276122`，交叉熵由 `1.349012` 降至 `1.286911`。一步更新后最高分仍属于纸张，因此损失下降与预测类别立即变正确是两个不同结果。这是人为选定参数的单样本算例；真实图片的单批与整轮结果保留在 [reference](reference.md) 和[实验结果](results.md)中。

## 1. 输入、参数和类别顺序

将实际的 512 维特征缩小为 2 维。所有数值均无量纲，采用列向量表示单样本；参数下标从 0 开始。类别顺序沿用 [data.py](src/data.py) 的 `paper=0`、`cardboard=1`、`metal=2`，正确标签是纸板 `y=1`。

$$
h=\begin{bmatrix}2\\1\end{bmatrix},\qquad
W=\begin{bmatrix}1&0\\0&1\\-1&1\end{bmatrix},\qquad
b=\begin{bmatrix}0\\0\\0\end{bmatrix}.
$$

| 量 | 形状 | 含义 |
| --- | --- | --- |
| h | 2×1 | 冻结骨干为这张图片算出的特征；本例保持不变 |
| W | 3×2 | 每行属于一个类别，每列对应一个特征 |
| b | 3×1 | 每个类别自己的偏置 |
| z、p | 3×1 | 类别原始分数与 softmax 概率 |
| y | 一个整数 | 正确类别编号，不是输入特征 |

PyTorch 的 `nn.Linear(2, 3)` 保存 `weight.shape=[3,2]`、`bias.shape=[3]`，与这里 W 的排列一致。偏置在数学中写成列向量，代码中通常存为一维张量。

## 2. 前向：分数 → softmax → 交叉熵

分类头计算每个类别的分数：

$$
z=Wh+b
=\begin{bmatrix}2\\1\\-1\end{bmatrix}.
$$

纸张分数最高，但标签是纸板。训练需要衡量正确类别拿到了多少概率，而不只看一次 `argmax`。

$$
p_i=\frac{e^{z_i}}{\sum_{k=0}^{2}e^{z_k}}.
$$

为避免指数过大，可以同时减去最大分数 2，概率不变：

$$
p=\frac{1}{1+e^{-1}+e^{-3}}
\begin{bmatrix}1\\e^{-1}\\e^{-3}\end{bmatrix}
\approx\begin{bmatrix}0.705385\\0.259496\\0.035119\end{bmatrix}.
$$

交叉熵使用自然对数，取正确类别 `y=1` 的概率：

$$
L=-\ln p_1
=-z_1+\ln\left(\sum_{k=0}^{2}e^{z_k}\right)
\approx1.349012216768.
$$

[loss.py](src/loss.py)直接把 logits 和整数标签交给 `CrossEntropyLoss`。上面拆开 softmax 只是为了解释计算，训练代码无需先生成概率再交给这个损失函数。

## 3. 求导第一段：损失怎样传回三个分数

用 `t=[0,1,0]ᵀ` 表示正确类别的 one-hot 向量，仅用于数学推导；实际标签仍是整数 1。令 δ 为 Kronecker delta，两个下标相等时取 1，否则取 0。

$$
\frac{\partial L}{\partial p_k}=-\frac{t_k}{p_k},\qquad
\frac{\partial p_k}{\partial z_i}=p_k(\delta_{ki}-p_i).
$$

每个分数都会影响 softmax 的共同分母，所以求分数梯度时要汇总所有概率分支：

$$
\frac{\partial L}{\partial z_i}
=\sum_{k=0}^{2}\frac{\partial L}{\partial p_k}
\frac{\partial p_k}{\partial z_i}
=-\sum_{k=0}^{2}t_k(\delta_{ki}-p_i)
=p_i-t_i.
$$

最后一步使用了 `t` 只有正确类别为 1、总和为 1。也可以对上一节的 `−z₁+logsumexp(z)` 直接求导，得到同一个结果。

$$
g_z=\frac{\partial L}{\partial z}=p-t
\approx\begin{bmatrix}0.705385\\-0.740504\\0.035119\end{bmatrix}.
$$

正确类别的梯度为负，沿负梯度更新会提高它的分数；其他类别的梯度为正，会压低它们的分数。三个梯度之和为 0，对所有 logits 加同一个常数不会改变 softmax，这也提供一个核对方式。通用分类与批量反向链见 [06 的完整求导](../06_pytorch_networks/backpropagation.md)。

## 4. 求导第二段：分数怎样传回权重和偏置

第 i 类的线性计算为：

$$
z_i=W_{i0}h_0+W_{i1}h_1+b_i.
$$

修改 `Wᵢⱼ` 只影响第 i 类分数，变化系数为对应特征 `hⱼ`；修改 `bᵢ` 的变化系数为 1。于是链式法则给出：

$$
\frac{\partial L}{\partial W_{ij}}
=\frac{\partial L}{\partial z_i}
\frac{\partial z_i}{\partial W_{ij}}
=(g_z)_i h_j,\qquad
\frac{\partial L}{\partial b_i}=(g_z)_i.
$$

把每个参数的梯度排列为与参数相同的形状：

$$
\nabla_W L=g_z h^T
\approx\begin{bmatrix}
1.410769&0.705385\\
-1.481007&-0.740504\\
0.070238&0.035119
\end{bmatrix},\qquad
\nabla_b L=g_z
\approx\begin{bmatrix}0.705385\\-0.740504\\0.035119\end{bmatrix}.
$$

这就是 `loss.backward()` 写入 `fc.weight.grad` 与 `fc.bias.grad` 的数值类型。3×2 的权重梯度是 3×1 与 1×2 的外积；不是对每个类别重复同一个标量梯度。

例如纸板行第一个权重的梯度为 `−0.74050354×2=−1.48100708`，第二个权重的梯度为 `−0.74050354×1=−0.74050354`。同样的分类误差，经不同特征值缩放，会得到不同权重梯度。

<a id="sgd-update"></a>

## 5. 一步 SGD：旧参数减学习率乘梯度

沿用 [train_step.py](src/train_step.py) 的默认学习率 `η=0.01`，无动量、无权重衰减；只进行一次更新，并继续使用相同 h：

$$
W'=W-\eta\nabla_W L,\qquad
b'=b-\eta\nabla_b L.
$$

$$
W'\approx\begin{bmatrix}
0.985892&-0.007054\\
0.014810&1.007405\\
-1.000702&0.999649
\end{bmatrix},\qquad
b'\approx\begin{bmatrix}-0.007054\\0.007405\\-0.000351\end{bmatrix}.
$$

纸板行第一个权重由 0 增至 `0−0.01×(−1.48100708)=0.01481007`；偏置也增加。两部分都参与抬高正确类别的分数。

重新前向计算，只观察结果，不做第二次更新：

$$
z'=W'h+b'
\approx\begin{bmatrix}1.957677\\1.044430\\-1.002107\end{bmatrix},\qquad
p'\approx\begin{bmatrix}0.688208\\0.276122\\0.035670\end{bmatrix}.
$$

$$
L'=-\ln p'_1\approx1.286911215585.
$$

| 同一特征上的结果 | 更新前 | 一步更新后 |
| --- | ---: | ---: |
| 正确类别纸板的分数 | 1.000000 | 1.044430 |
| 正确类别纸板的概率 | 0.259496 | 0.276122 |
| 交叉熵 | 1.349012 | 1.286911 |
| 最高分类别 | paper | paper |

分数有改善，但尚不足以改变最高分类别。表中值按未舍入的参数计算；若用打印出的六位小数复算，会有舍入差异。这个给定算例的同样本损失下降，不说明验证集表现，也不保证任意学习率的一步更新都下降。

<a id="real-head"></a>

## 6. 对应真实的 `[B,512] → [B,3]`

实际 ResNet18 骨干输出 B 张图片的特征矩阵 H，每行是一张图片，分类头沿用同一种线性关系：

$$
Z=HW^T+\mathbf{1}_B b^T,
\qquad H\in\mathbb{R}^{B\times512},\quad
W\in\mathbb{R}^{3\times512},\quad Z\in\mathbb{R}^{B\times3}.
$$

| 源码中的量 | 实际形状与求导约定 |
| --- | --- |
| `images` | `[B,3,224,224]`，普通训练输入不要求图像梯度 |
| 骨干特征 H | `[B,512]`，当前骨干参数冻结，特征作为分类头输入 |
| `model.fc.weight`、`.grad` | 均为 `[3,512]` |
| `model.fc.bias`、`.grad` | 均为 `[3]` |
| `logits`、`labels` | `[B,3]` 原始分数与 `[B]` int64 类别编号 |
| `loss` | 标量；`reduction="mean"` 使每张图片的梯度带 `1/B` 因子 |

单样本外积要在批次内汇总并取平均。批量矩阵乘法、偏置梯度的归约和形状检查复用 [06 的完整反向链](../06_pytorch_networks/backpropagation.md)，本章只把输入维度与类别数换成 512 和 3。可训练参数共 `3×512+3=1,539` 个。

## 7. 冻结与 `no_grad` 决定在哪一段求导

[model.py](src/model.py)先加载预训练模型并把原参数设为 `requires_grad=False`，再新建 `nn.Linear(512,3)`，因此只有新层的 `fc.weight`、`fc.bias` 需要梯度。[train_step.py](src/train_step.py)在通常的梯度上下文中调用 `model(images)`；骨干参数及输入图片都不要求梯度时，特征 H 不要求梯度，分类头仍会记录计算，并利用 H 求出参数梯度。

固定特征不表示数学上的损失对特征不敏感。若把本例 h 当作变量，还能算出：

$$
\nabla_h L=W^Tg_z
\approx\begin{bmatrix}0.670265\\-0.705385\end{bmatrix}.
$$

当前训练把 h 当作固定输入，因此不继续沿骨干求导，骨干参数的 `.grad` 保持 `None`；这与“它们的数学导数一定为零”不同。如果以后微调骨干，要重新启用对应参数的梯度，并让优化器管理它们。

将模型拆成 `backbone` 与 `head` 后，也可以用下面的**等价教学结构**表达固定特征训练；这不是当前源码中的对象拆分：

```python
with torch.no_grad():
    h = backbone(images)     # 仅骨干这一段不记录求导信息
logits = head(h)             # 分类头保留计算图
loss = criterion(logits, labels)
loss.backward()
optimizer.step()
```

求分类头梯度需要：分类头参数 `requires_grad=True`、前向在梯度上下文中执行、对原始 loss 张量调用 `backward()`；真正更新还需要把这些参数交给优化器并调用 `step()`。若将整个 `model(images)` 包进 `no_grad()`，分类头也不会记录计算，本案例就无法对它训练。

骨干保持 `eval()` 是为了固定 BatchNorm 运行统计量，与是否求参数梯度是两件事。实际训练每批调用 `set_head_training_mode()`，而前向检查、验证和更新后观察使用 `no_grad()`；完整解释见 [concepts 的模式与梯度](concepts.md#gradient-modes)。

本页数值使用标准库双精度计算，中心差分步长 `1e-5` 核对了 6 个权重、3 个偏置和 2 个特征的导数，最大绝对差约 `1.93e-11`；并重新计算了一步 SGD 后的分数、概率和损失。没有使用真实图片、下载权重或重新训练。

[返回本章](README.md) · [06 批量反向传播](../06_pytorch_networks/backpropagation.md) · [实现与既有结果](reference.md)
