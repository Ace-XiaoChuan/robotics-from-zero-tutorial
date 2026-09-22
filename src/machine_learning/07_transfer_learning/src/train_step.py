"""完成一个 batch 的训练，并检查哪些参数和模型状态发生了变化。"""

import argparse
import json
import math

import torch

from data import make_dataloaders
from loss import build_criterion
from model import PROJECT_DIR, build_model, set_head_training_mode


def build_optimizer(model, learning_rate=0.01):
    """先用无动量、无权重衰减的 SGD，方便直接理解更新公式。"""
    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("学习率必须是有限的正数。")
    # 只把可训练参数交给优化器，本周就是 fc.weight 和 fc.bias。
    parameters = [p for p in model.parameters() if p.requires_grad]
    return torch.optim.SGD(parameters, lr=learning_rate)


def train_one_batch(model, images, labels, criterion, optimizer, return_metrics=False):
    """后续遍历训练集时，可以对每个 batch 调用这个函数。"""
    set_head_training_mode(model)
    optimizer.zero_grad(set_to_none=True)  # 清掉旧梯度，避免批次间意外累加。
    logits = model(images)                # 前向传播。
    loss = criterion(logits, labels)      # 与真实标签比较。
    if not torch.isfinite(loss).item():
        raise ValueError("损失不是有限数值，停止更新。")
    loss.backward()                      # 反向传播本身就是计算梯度。
    # 更新之前检查梯度；异常梯度不能交给优化器。
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            if parameter.grad is None or not torch.isfinite(parameter.grad).all().item():
                raise ValueError(f"{name} 的梯度缺失或不是有限数值。")
    optimizer.step()                      # SGD：新参数 = 旧参数 - 学习率 × 梯度。
    # 返回的是更新前算出的损失；item() 用于记录，反向已使用上面的原始张量。
    if return_metrics:
        return loss.item(), (logits.detach().argmax(dim=1) == labels).sum().item()
    return loss.item()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)
    model = build_model()
    criterion = build_criterion()
    optimizer = build_optimizer(model, args.learning_rate)
    images, labels = next(iter(make_dataloaders(batch_size=args.batch_size)["train"]))

    # clone 必不可少：保存更新前的副本，而不是继续指向正在更新的张量。
    # state_dict 同时包含参数和 BatchNorm 的缓冲区，能检查完整的冻结状态。
    before = {name: value.clone() for name, value in model.state_dict().items()}
    loss_before = train_one_batch(model, images, labels, criterion, optimizer)
    after = {name: value.clone() for name, value in model.state_dict().items()}
    changed = [name for name in before if not torch.equal(before[name], after[name])]
    assert set(changed) == {"fc.weight", "fc.bias"}
    assert all(p.grad is None for name, p in model.named_parameters()
               if not name.startswith("fc."))
    gradients, updates = {}, {}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            gradients[name] = parameter.grad.norm().item()
            updates[name] = (parameter.detach() - before[name]).abs().max().item()
            # 交叉核对本次 SGD 更新确实来自刚才的梯度。
            expected = before[name] - args.learning_rate * parameter.grad
            assert torch.allclose(parameter.detach(), expected, atol=1e-7, rtol=1e-5)

    # 对同一批图片再算一次，仅用来观察更新效果；没有第二次参数更新。
    model.eval()
    with torch.no_grad():
        loss_after = criterion(model(images), labels).item()
    assert math.isfinite(loss_after)
    assert all(torch.equal(after[name], value) for name, value in model.state_dict().items())
    report = {
        "seed": 42, "split": "train", "batch_size": len(labels),
        "optimizer": "SGD", "learning_rate": args.learning_rate,
        "momentum": 0, "weight_decay": 0, "optimizer_steps": 1,
        "loss_before": loss_before, "loss_after_same_batch": loss_after,
        "gradient_norms": gradients, "max_abs_parameter_updates": updates,
        "changed_state_keys": changed, "frozen_state_unchanged": True,
        "checks_passed": True, "checkpoint_saved": False,
    }
    output = PROJECT_DIR / "outputs" / "tables" / "train_step_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完成 1 个 batch（{len(labels)} 张）的训练；SGD 学习率 {args.learning_rate}")
    print(f"更新前损失：{loss_before:.6f}；更新后同批损失：{loss_after:.6f}")
    print(f"发生变化：{changed}；冻结参数和 BatchNorm 缓冲区均未变化。")
    print(f"结果：{output}；本次仅演示一步更新，没有保存模型权重。")


if __name__ == "__main__":
    main()
