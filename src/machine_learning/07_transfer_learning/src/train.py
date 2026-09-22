"""按轮训练分类头、验证并保存最佳模型；不使用测试集。"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.models import resnet18

from data import CLASS_TO_IDX, TRAIN_AUGMENTATION, TrashDataset, build_transform
from loss import build_criterion
from model import PROJECT_DIR, WEIGHTS, build_model
from train_step import build_optimizer, train_one_batch


def train_epoch(model, loader, criterion, optimizer):
    total_loss, correct, count = 0.0, 0, 0
    for images, labels in loader:
        loss, batch_correct = train_one_batch(
            model, images, labels, criterion, optimizer, return_metrics=True
        )
        # 按样本数加权，最后不足 32 张的一批不会被多算。
        total_loss += loss * len(labels)
        correct += batch_correct
        count += len(labels)
    return {"loss": total_loss / count, "accuracy": correct / count, "samples": count}


def evaluate(model, loader, criterion):
    model.eval()
    total_loss, correct, count = 0.0, 0, 0
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images)
            loss = criterion(logits, labels)
            if not torch.isfinite(loss).item():
                raise ValueError("验证损失不是有限数值。")
            total_loss += loss.item() * len(labels)
            correct += (logits.argmax(dim=1) == labels).sum().item()
            count += len(labels)
    return {"loss": total_loss / count, "accuracy": correct / count, "samples": count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--no-augmentation", action="store_true",
                        help="关闭训练集随机增强，用于与原始基线对比")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs 和 batch-size 必须为正整数。")
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    # 模型、优化器、加载器只创建一次，轮次之间保留参数和随机生成器状态。
    model = build_model()
    optimizer = build_optimizer(model, args.learning_rate)
    criterion = build_criterion()
    loaders = {
        split: DataLoader(
            TrashDataset(split, augment=not args.no_augmentation), batch_size=args.batch_size,
            shuffle=(split == "train"), num_workers=0, drop_last=False,
            generator=torch.Generator().manual_seed(args.seed),
        ) for split in ("train", "val")
    }
    output_dir = args.output_dir or (
        PROJECT_DIR / "outputs" / "runs" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output_dir.mkdir(parents=True, exist_ok=False)  # 每次独立目录，避免覆盖先前实验。
    frozen_before = {n: v.clone() for n, v in model.state_dict().items() if not n.startswith("fc.")}
    transform = build_transform()
    metadata = {
        "architecture": "resnet18", "pretrained_weights": WEIGHTS.name,
        "class_to_idx": CLASS_TO_IDX, "seed": args.seed,
        "epochs": args.epochs, "batch_size": args.batch_size,
        "optimizer": "SGD", "learning_rate": args.learning_rate,
        "preprocessing": {
            # 这里记录所有集合共用的固定预处理，推理时也使用它。
            # 训练专用增强单独记录，不能在验证/推理时照搬。
            "color_mode": "RGB", "resize_size": transform.resize_size,
            "crop_size": transform.crop_size, "mean": transform.mean,
            "std": transform.std, "interpolation": transform.interpolation.value,
            "antialias": transform.antialias, "random_augmentation": False,
        },
        "train_augmentation": (None if args.no_augmentation else dict(TRAIN_AUGMENTATION)),
        "split_sha256": {
            split: hashlib.sha256((PROJECT_DIR / "data" / "splits" / f"{split}.json").read_bytes()).hexdigest()
            for split in loaders
        },
        "selection_rule": "lowest validation loss; first epoch wins ties",
        "test_evaluated": False,
    }
    history, best_loss, best_epoch = [], float("inf"), None
    print(f"输出目录：{output_dir}", flush=True)
    for epoch in range(1, args.epochs + 1):
        train_metrics = train_epoch(model, loaders["train"], criterion, optimizer)
        val_metrics = evaluate(model, loaders["val"], criterion)
        assert all(torch.equal(v, model.state_dict()[n]) for n, v in frozen_before.items())
        history.append({"epoch": epoch, "train": train_metrics, "val": val_metrics})
        if val_metrics["loss"] < best_loss:
            best_loss, best_epoch = val_metrics["loss"], epoch
            # 保存完整模型状态，后续推理无需再次下载原始预训练权重。
            torch.save({"model_state_dict": model.state_dict(), "metadata": metadata,
                        "epoch": epoch, "val_metrics": val_metrics}, output_dir / "best_model.pt")
        print(f"Epoch {epoch}/{args.epochs}: train loss={train_metrics['loss']:.4f}, "
              f"acc={train_metrics['accuracy']:.2%}; val loss={val_metrics['loss']:.4f}, "
              f"acc={val_metrics['accuracy']:.2%}", flush=True)
        report = {"metadata": metadata, "history": history, "best_epoch": best_epoch,
                  "best_val_loss": best_loss, "frozen_state_unchanged": True}
        (output_dir / "history.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 重新构建模型并加载保存的最佳状态，用同一批验证图片确认预测一致。
    checkpoint = torch.load(output_dir / "best_model.pt", map_location="cpu", weights_only=True)
    restored = resnet18(weights=None)
    restored.fc = nn.Linear(restored.fc.in_features, len(CLASS_TO_IDX))
    restored.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    restored.eval()
    images, _ = next(iter(loaders["val"]))
    with torch.no_grad():
        assert torch.equal(model(images), restored(images))
    report["checkpoint_reload_verified"] = True
    (output_dir / "history.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完成；最佳轮次 {best_epoch}，权重重新加载检查通过。", flush=True)


if __name__ == "__main__":
    main()
