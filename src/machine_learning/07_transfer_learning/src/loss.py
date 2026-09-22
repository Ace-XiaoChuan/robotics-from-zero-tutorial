"""将类别分数和正确标签交给交叉熵，检查一个训练批次的损失。"""

import argparse
import json

import torch
from torch import nn

from data import CLASS_TO_IDX, make_dataloaders
from model import PROJECT_DIR, build_model, set_head_training_mode


def build_criterion():
    """返回后续训练可复用的损失函数，先对所有样本采用相同权重。"""
    # 输入 logits 是 [B, 3] 的原始分数，不要先做 softmax。
    # labels 是 [B] 的 int64 类别编号，不是 one-hot，也不需要除以 255。
    # mean 表示先算每张图片的损失，再取这一批的平均值。
    return nn.CrossEntropyLoss(reduction="mean")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)
    model = build_model()
    set_head_training_mode(model)
    criterion = build_criterion()
    images, labels = next(iter(make_dataloaders(batch_size=args.batch_size)["train"]))

    # 前向得到分数，再与真实标签比较。保留计算图，后续才能 loss.backward()。
    logits = model(images)
    loss = criterion(logits, labels)
    assert logits.shape == (len(labels), len(CLASS_TO_IDX))
    assert labels.dtype == torch.int64
    assert loss.ndim == 0 and torch.isfinite(loss).item()
    assert loss.requires_grad

    # 以下逐张损失仅用于讲解和验证，不替代上面的训练用 loss。
    with torch.no_grad():
        per_sample = nn.CrossEntropyLoss(reduction="none")(logits, labels)
        assert torch.allclose(loss.detach(), per_sample.mean())
    report = {
        "seed": 42, "split": "train", "batch_size": len(labels),
        "criterion": "CrossEntropyLoss", "reduction": "mean",
        "class_to_idx": CLASS_TO_IDX,
        "logits_shape": list(logits.shape), "labels_shape": list(labels.shape),
        "loss": loss.item(), "loss_shape": list(loss.shape),
        "loss_requires_grad": loss.requires_grad,
        "first_three_labels": labels[:3].tolist(),
        "first_three_logits": logits[:3].detach().tolist(),
        "first_three_losses": per_sample[:3].tolist(),
        "checks_passed": True, "backward_performed": False,
        "optimizer_step_performed": False,
    }
    output = PROJECT_DIR / "outputs" / "tables" / "loss_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"logits：{list(logits.shape)}；labels：{list(labels.shape)}")
    print(f"前 3 张的真实标签：{labels[:3].tolist()}")
    print(f"前 3 张的损失：{per_sample[:3].tolist()}")
    # item 只用于显示/记录；反向传播时应使用 loss 张量，而不是这个 Python 数字。
    print(f"整批平均损失：{loss.item():.6f}；可反向传播：{loss.requires_grad}")
    print(f"检查通过：{output}；本次未反向传播、未更新参数。")


if __name__ == "__main__":
    main()
