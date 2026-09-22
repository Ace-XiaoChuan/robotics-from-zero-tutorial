"""学习笔记：训练一轮与验证一轮，关键区别是是否更新参数。"""

import torch


def train_one_epoch(model, loader, loss_fn, optimizer, device):
    """遍历训练集一次；每一批都执行一次参数更新。"""
    # train() 设置训练模式；它本身不会开始训练，也不会更新参数。
    model.train()
    total_loss, correct, count = 0.0, 0, 0
    for images, labels in loader:
        # 数据和模型应放在相同设备；本周使用 CPU。
        images, labels = images.to(device), labels.to(device)
        # 1. 清零旧梯度：PyTorch 默认会累加梯度，本次只用当前批次的梯度。
        optimizer.zero_grad()
        # 2. 前向传播：用当前参数计算每张图片的十个类别分数。
        logits = model(images)
        # 3. 计算损失：交叉熵对照真实标签，得到当前批次的平均损失。
        loss = loss_fn(logits, labels)
        if not bool(torch.isfinite(loss)):
            raise ValueError("训练损失出现 NaN 或无穷值，请检查输入和学习率。")
        # 4. 反向传播：计算损失对各参数的梯度，暂时还没有改变参数。
        loss.backward()
        # 5. 优化器读取梯度并更新参数，这一步才是实际修改模型。
        optimizer.step()

        # argmax(dim=1) 在每张图片的十个分数中找最大值所在的类别。
        # 准确率只用于观察效果；不能用离散的“猜对几个”代替交叉熵求梯度。
        size = labels.size(0)
        correct += int((logits.argmax(dim=1) == labels).sum())
        # 最后一批只有 16 张，所以先乘样本数，最后除以总数，不能直接平均批次损失。
        total_loss += loss.item() * size
        count += size
    return {"loss": total_loss / count, "accuracy": correct / count, "samples": count}

# `@...` 是 Python 的“装饰器”语法：它在不改写函数主体的情况下，
# 为整个函数附加一项行为。这里相当于每次调用 evaluate(...) 时，
# 都自动把函数内部的计算放进 `with torch.no_grad():` 环境。
#
# `torch.no_grad()` 告诉 PyTorch：验证阶段只需要计算预测结果，不需要建立
# 反向传播使用的计算图，也不需要保存中间梯度信息，因此可以减少内存和计算开销。
# 它不会删除已有梯度，也不会主动改变模型参数；这里只是让本函数中的新计算
# 不被自动求导系统记录。由于验证中也没有 loss.backward() 和 optimizer.step()，
# 模型参数会保持不变。
#
# 它和下面的 model.eval() 不是一回事：no_grad() 管理“是否记录梯度”，
# eval() 管理 Dropout、BatchNorm 等层在验证时的工作方式。标准验证流程通常两者都用。
@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    """固定模型参数，遍历验证数据，检查当前模型的学习效果。"""
    # no_grad 关闭梯度记录，节省计算和内存；eval 切换为评估模式。
    # 两者作用不同；本网络没有 Dropout 等模式敏感层，但保留标准使用方式。
    model.eval()
    total_loss, correct, count = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        logits = model(images)
        loss = loss_fn(logits, labels)
        if not bool(torch.isfinite(loss)):
            raise ValueError("验证损失出现 NaN 或无穷值。")
        # 验证只前向计算与统计，不调用 backward 或 optimizer.step。
        size = labels.size(0)
        total_loss += loss.item() * size
        correct += int((logits.argmax(dim=1) == labels).sum())
        count += size
    return {"loss": total_loss / count, "accuracy": correct / count, "samples": count}
