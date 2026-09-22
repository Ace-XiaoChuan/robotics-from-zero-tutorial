"""学习笔记：把数据、模型、损失和优化器组装成一次完整的基线训练。

先运行 python src/train.py --smoke 检查流程，再运行 python src/train.py。
训练核心请看 engine.py；本文件还负责保存配置、曲线和最佳验证权重。
"""

import argparse
import csv
import json
import os
import platform
import tempfile
from datetime import datetime
from pathlib import Path
from time import perf_counter

import torch
import torchvision
from torch import nn
from torch.utils.data import DataLoader, Subset

from data import PROJECT_DIR, SPLIT_PATH, make_dataloaders
from engine import evaluate, train_one_epoch
from model import DigitMLP

# 将绘图缓存放到临时目录；Agg 允许没有图形窗口时也能保存曲线。
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week06_mnist_mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_json(path, content):
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="仅用小子集训练 1 轮，检查流程")
    args = parser.parse_args()
    experiment = "E00" if args.smoke else "E01"
    # 每次运行放在独立目录，避免覆盖以前的学习记录。
    output = PROJECT_DIR / "outputs/runs" / f"{experiment}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(42)  # 控制模型初始参数；数据加载器另外有自己的随机生成器。
    torch.set_num_threads(1)  # 小型 CPU 任务使用一个计算线程，减少线程调度开销。
    device = torch.device("cpu")
    train_loader, validation_loader = make_dataloaders()

    if args.smoke:
        # 只从已划定的两个集合内部取小子集，两者仍然没有重叠。
        # E00 是流程检查，不能把它的成绩与完整数据训练的 E01 比较。
        train_subset = Subset(train_loader.dataset, list(range(512)))
        validation_subset = Subset(validation_loader.dataset, list(range(256)))
        save_json(output / "smoke_indices.json", {
            "train": train_loader.dataset.indices[:512],
            "validation": validation_loader.dataset.indices[:256],
        })
        train_loader = DataLoader(train_subset, batch_size=64, shuffle=True,
                                  generator=torch.Generator().manual_seed(42))
        validation_loader = DataLoader(validation_subset, batch_size=64, shuffle=False,
                                       generator=torch.Generator().manual_seed(42))

    model = DigitMLP().to(device)
    # CrossEntropyLoss 接收 [B, 10] 的原始分数和 [B] 的整数标签。
    loss_fn = nn.CrossEntropyLoss()
    # model.parameters() 把待学习的权重与偏置交给优化器；学习率控制调整尺度。
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    epochs = 1 if args.smoke else 5
    config = {
        "experiment": experiment, "seed": 42, "device": str(device), "cpu_threads": 1,
        "model": {"input_features": 784, "hidden_size": 128, "classes": 10, "activation": "ReLU"},
        "class_mapping": list(range(10)), "preprocessing": "ToTensor: uint8 / 255; [1,28,28]",
        "batch_size": 64, "epochs": epochs, "optimizer": "Adam", "learning_rate": 1e-3,
        "loss": "CrossEntropyLoss", "selection": "highest validation accuracy; earliest epoch on tie",
        "train_samples": len(train_loader.dataset), "validation_samples": len(validation_loader.dataset),
        "split_file": str(SPLIT_PATH.relative_to(PROJECT_DIR)),
        "python": platform.python_version(), "torch": torch.__version__, "torchvision": torchvision.__version__,
        "parameter_count": sum(p.numel() for p in model.parameters()), "official_test_loaded": False,
    }
    save_json(output / "config.json", config)

    # 用验证集固定的一批检查形状，避免为了抽查而推进训练取样顺序。
    # 此时参数尚未训练，分数没有识别能力；只检查数据是否顺利通过网络。
    fixed_images, fixed_labels = next(iter(validation_loader))
    model.eval()
    with torch.no_grad():
        initial_logits = model(fixed_images.to(device))
    assert initial_logits.shape == (len(fixed_labels), 10)
    assert bool(torch.isfinite(initial_logits).all())
    save_json(output / "batch_inspection.json", {
        "images": list(fixed_images.shape), "labels": list(fixed_labels.shape),
        "logits": list(initial_logits.shape), "logits_dtype": str(initial_logits.dtype),
        "first_untrained_scores": initial_logits[0].tolist(),
        "first_true_label": int(fixed_labels[0]),
    })

    start = perf_counter()
    history, best_accuracy, best_epoch = [], -1.0, 0
    print(f"{experiment}: {output}", flush=True)
    for epoch in range(1, epochs + 1):
        epoch_start = perf_counter()
        train_metrics = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        validation_metrics = evaluate(model, validation_loader, loss_fn, device)
        row = {"epoch": epoch, "train_loss": train_metrics["loss"],
               "train_accuracy": train_metrics["accuracy"], "validation_loss": validation_metrics["loss"],
               "validation_accuracy": validation_metrics["accuracy"], "seconds": perf_counter() - epoch_start}
        history.append(row)
        # 只按验证准确率选择最佳轮次，不接触测试集。
        if row["validation_accuracy"] > best_accuracy:
            best_accuracy, best_epoch = row["validation_accuracy"], epoch
            with torch.no_grad():
                best_fixed_logits = model(fixed_images.to(device)).clone()
            torch.save(model.state_dict(), output / "best_state_dict.pt")
        with (output / "history.csv").open("w", newline="", encoding="utf-8") as file:
            # 固定使用 LF 换行，避免不同操作系统生成不同的 CSV 行尾。
            writer = csv.DictWriter(file, fieldnames=list(row), lineterminator="\n")
            writer.writeheader()
            writer.writerows(history)
        print(f"Epoch {epoch}/{epochs}: train loss={row['train_loss']:.4f}, "
              f"accuracy={row['train_accuracy']:.2%}; validation loss={row['validation_loss']:.4f}, "
              f"accuracy={row['validation_accuracy']:.2%}", flush=True)

    # state_dict 只保存参数；重新建立相同结构才能正确加载。
    # 比较固定输入的输出，确认写入磁盘后的权重可以完整恢复。
    restored = DigitMLP(hidden_size=config["model"]["hidden_size"]).to(device)
    restored.load_state_dict(torch.load(output / "best_state_dict.pt", map_location=device, weights_only=True))
    restored.eval()
    with torch.no_grad():
        after = restored(fixed_images.to(device))
    assert torch.equal(best_fixed_logits, after)
    save_json(output / "summary.json", {
        "best_epoch": best_epoch, "best_validation_accuracy": best_accuracy,
        "training_seconds": sum(row["seconds"] for row in history),
        "elapsed_seconds_through_reload": perf_counter() - start,
        "reload_outputs_identical": True, "official_test_loaded": False,
    })

    # 两条曲线分别回答“错误程度有没有下降”和“猜对比例有没有上升”。
    # 训练指标是在参数持续更新时累计的，验证指标是在每轮末固定参数后计算的。
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    for axis, metric in zip(axes, ("loss", "accuracy")):
        for split in ("train", "validation"):
            axis.plot([row["epoch"] for row in history],
                      [row[f"{split}_{metric}"] for row in history], marker="o", label=split)
        axis.set(xlabel="Epoch", ylabel=metric, title=f"{experiment} {metric}")
        axis.set_xticks(list(range(1, epochs + 1)))
        axis.legend()
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output / "learning_curves.png", dpi=160)
    plt.close(figure)
    print(f"完成：最佳验证准确率 {best_accuracy:.2%}（第 {best_epoch} 轮），权重加载检查通过。", flush=True)


if __name__ == "__main__":
    main()
