"""使用保存的最佳模型评估测试集，并保存指标、预测、混淆矩阵和错误样本。"""

import argparse
import csv
import json
import shutil
import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import torch
from torch.utils.data import DataLoader

from data import CLASS_TO_IDX, TrashDataset
from loss import build_criterion
from model import PROJECT_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path, help="train.py 生成的实验目录")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output-dir", type=Path,
                        help="评估产物目录；默认放在该实验目录的 test_evaluation")
    args = parser.parse_args()
    torch.set_num_threads(2)
    if args.batch_size < 1:
        parser.error("batch-size 必须为正整数。")
    if args.model_dir.is_absolute():
        model_dir = args.model_dir
    elif args.model_dir.exists():
        # 允许从仓库根目录传 07_transfer_learning/... 这样的路径。
        model_dir = args.model_dir.resolve()
    else:
        # 也允许简写为 outputs/runs/<实验目录>。
        model_dir = (PROJECT_DIR / args.model_dir).resolve()
    checkpoint_path = model_dir / "best_model.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    metadata = checkpoint["metadata"]
    if metadata["class_to_idx"] != CLASS_TO_IDX:
        raise ValueError("检查点的类别映射与数据集不一致。")

    # 不调用 build_model：它会重新下载并初始化分类头。检查点已经包含完整状态。
    from torchvision.models import resnet18
    from torch import nn
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_TO_IDX))
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    dataset = TrashDataset("test", augment=False)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False,
                        num_workers=0, drop_last=False)
    criterion = build_criterion()
    total_loss, correct = 0.0, 0
    records = []
    confusion = torch.zeros((len(CLASS_TO_IDX), len(CLASS_TO_IDX)), dtype=torch.int64)
    idx_to_class = {value: key for key, value in CLASS_TO_IDX.items()}
    with torch.no_grad():
        for batch_indices, (images, labels) in enumerate(loader):
            logits = model(images)
            if not torch.isfinite(logits).all():
                raise ValueError("模型输出包含非有限值。")
            probabilities = logits.softmax(dim=1)
            total_loss += criterion(logits, labels).item() * len(labels)
            predictions = logits.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            for offset, (label, prediction, probability) in enumerate(
                    zip(labels.tolist(), predictions.tolist(), probabilities.tolist())):
                sample = dataset.samples[batch_indices * args.batch_size + offset]
                confidence = probability[prediction]
                confusion[label, prediction] += 1
                records.append({
                    "path": sample["path"], "true_label": idx_to_class[label],
                    "predicted_label": idx_to_class[prediction],
                    "correct": label == prediction, "confidence": confidence,
                    "probabilities": {idx_to_class[i]: probability[i]
                                      for i in range(len(CLASS_TO_IDX))},
                })

    output_dir = args.output_dir or model_dir / "test_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    errors_dir = output_dir / "errors"
    errors_dir.mkdir(exist_ok=True)
    for index, record in enumerate(records):
        if not record["correct"]:
            source = dataset.data_dir / record["path"]
            # 文件名加入真实/预测类别，打开错误样本时无需另看 CSV。
            destination = errors_dir / (
                f"{index:03d}_true-{record['true_label']}"
                f"_pred-{record['predicted_label']}_{Path(record['path']).name}"
            )
            shutil.copy2(source, destination)

    total = len(records)
    per_class = {}
    for index, name in idx_to_class.items():
        support = int(confusion[index].sum())
        class_correct = int(confusion[index, index])
        predicted_total = int(confusion[:, index].sum())
        per_class[name] = {
            "support": support,
            "correct": class_correct,
            "accuracy_recall": class_correct / support if support else None,
            "precision": class_correct / predicted_total if predicted_total else None,
            "f1": 2 * class_correct / (support + predicted_total) if support + predicted_total else 0.0,
        }
    metrics = {
        "model_dir": str(model_dir), "checkpoint_epoch": checkpoint["epoch"],
        "class_to_idx": CLASS_TO_IDX, "samples": total,
        "loss": total_loss / total, "accuracy": correct / total,
        "correct": correct, "errors": total - correct,
        "error_rate": (total - correct) / total,
        "per_class": per_class, "confusion_matrix": confusion.tolist(),
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(per_class),
        "checkpoint_sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        "test_split_sha256": hashlib.sha256((dataset.data_dir / "splits/test.json").read_bytes()).hexdigest(),
        "train_augmentation": metadata.get("train_augmentation"),
        "selection_note": "各实验模型由验证集最低损失选择；测试成绩仅报告，不用于继续调参。",
    }
    (output_dir / "test_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "test_predictions.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["path", "true_label", "predicted_label",
                                                   "correct", "confidence"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in records)
    (output_dir / "test_predictions.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "errors.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["path", "true_label", "predicted_label", "confidence"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in records if not row["correct"])

    names = [idx_to_class[i] for i in range(len(CLASS_TO_IDX))]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    image = ax.imshow(confusion.numpy(), cmap="Blues")
    fig.colorbar(image, ax=ax, label="Samples")
    # 使用英文坐标标题，避免当前 CPU 环境缺少中文字体时产生乱码；类别名本身已是英文。
    ax.set(xticks=range(len(names)), yticks=range(len(names)),
           xticklabels=names, yticklabels=names, xlabel="Predicted label",
           ylabel="True label", title="Test confusion matrix")
    for row in range(len(names)):
        for column in range(len(names)):
            ax.text(column, row, int(confusion[row, column]), ha="center", va="center",
                    color="white" if confusion[row, column] > confusion.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(output_dir / "confusion_matrix.png", dpi=160)
    plt.close(fig)
    # 错误样本联系表展示原图，方便一起观察；模型实际输入还经过中心裁剪。
    from PIL import Image
    errors = [row for row in records if not row["correct"]]
    if errors:
        fig, axes = plt.subplots((len(errors) + 3) // 4, 4,
                                 figsize=(16, 3 * ((len(errors) + 3) // 4)), squeeze=False)
        for ax in axes.flat:
            ax.axis("off")
        for ax, row in zip(axes.flat, errors):
            with Image.open(dataset.data_dir / row["path"]) as source:
                ax.imshow(source.convert("RGB"))
            ax.set_title(f"{Path(row['path']).name}\nTrue: {row['true_label']} / Pred: {row['predicted_label']}\n"
                         f"Softmax: {row['confidence']:.1%}", fontsize=9)
        fig.tight_layout()
        fig.savefig(output_dir / "error_gallery.png", dpi=120)
        plt.close(fig)
    print(f"测试集：{total} 张；准确率 {metrics['accuracy']:.2%}；错误 {metrics['errors']} 张")
    print(f"评估产物：{output_dir}")


if __name__ == "__main__":
    main()
