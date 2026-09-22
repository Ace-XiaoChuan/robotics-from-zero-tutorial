"""第一步：查看本地图片、类别数量，以及图片变成张量的过程。"""

import json
import os
import random
import tempfile
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week07_mpl"))

import matplotlib

matplotlib.use("Agg")  # 保存图片，在没有桌面窗口的环境中也能运行。
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
CLASS_TO_IDX = {"paper": 0, "cardboard": 1, "metal": 2}
SEED = 42


def to_tensor(path):
    """RGB 图片 [高, 宽, 通道] → float32 张量 [通道, 高, 宽]。"""
    with Image.open(path) as image:
        pixels = np.array(image.convert("RGB"), copy=True)
    # 原像素为 0～255 的整数，除以 255 后变成 0～1 的浮点数。
    # 这只是张量转换演示；接入预训练模型时还需采用该模型要求的预处理。
    return torch.from_numpy(pixels).permute(2, 0, 1).float() / 255.0


def main():
    samples = json.loads((DATA_DIR / "selected_samples.json").read_text())
    if not samples:
        raise ValueError("样本清单为空。")

    counts = Counter()
    image_formats = Counter()
    seen = set()
    # 逐张打开，确认清单对应的文件存在、可解码，并统计实际尺寸和颜色模式。
    for sample in samples:
        label, relative_path = sample["label"], sample["path"]
        if label not in CLASS_TO_IDX:
            raise ValueError(f"未知类别：{label}")
        if relative_path in seen:
            raise ValueError(f"清单存在重复路径：{relative_path}")
        seen.add(relative_path)
        if Path(relative_path).parent.name != label:
            # 原图目录保留来源标签；允许清单中附有原标签和原因的人工修正。
            if (sample.get("original_label") != Path(relative_path).parent.name
                    or not sample.get("correction_reason")):
                raise ValueError(f"目录与标签不一致，且缺少修正记录：{sample}")
        with Image.open(DATA_DIR / relative_path) as image:
            image.load()
            image_formats[(image.width, image.height, image.mode)] += 1
        counts[label] += 1

    # 每类抽三张；局部随机数生成器保证抽样可复现。
    rng = random.Random(SEED)
    selected = []
    for label in CLASS_TO_IDX:
        candidates = [sample for sample in samples if sample["label"] == label]
        if len(candidates) < 3:
            raise ValueError(f"{label} 不足三张，无法生成九宫格。")
        selected.extend(rng.sample(candidates, 3))

    figures_dir = OUTPUT_DIR / "figures"
    tables_dir = OUTPUT_DIR / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(12, 9))
    for ax, sample in zip(axes.flat, selected):
        with Image.open(DATA_DIR / sample["path"]) as image:
            ax.imshow(image.convert("RGB"))
        # 使用数据集的英文标签，避免系统缺少中文字体导致方框。
        ax.set_title(f"{sample['label']} | {Path(sample['path']).name}")
        ax.axis("off")
    fig.suptitle("TrashNet: paper / cardboard / metal (seed=42)")
    fig.tight_layout()
    figure_path = figures_dir / "sample_grid.png"
    fig.savefig(figure_path, dpi=150)
    plt.close(fig)

    # 取不同类别的三张图组成演示批次；这不是训练集划分，也不是训练批次。
    batch_samples = selected[::3]
    tensors = [to_tensor(DATA_DIR / sample["path"]) for sample in batch_samples]
    if len({tuple(tensor.shape) for tensor in tensors}) != 1:
        raise ValueError("演示图片尺寸不同，需统一尺寸才能组成批次。")
    batch = torch.stack(tensors)
    labels = torch.tensor([CLASS_TO_IDX[s["label"]] for s in batch_samples])
    summary = {
        "seed": SEED,
        "total": len(samples),
        "class_counts": dict(counts),
        "class_to_idx": CLASS_TO_IDX,
        "image_formats": [
            {"width": w, "height": h, "mode": mode, "count": count}
            for (w, h, mode), count in sorted(image_formats.items())
        ],
        "grid_samples": selected,
        "batch_samples": batch_samples,
        "single_tensor_shape": list(tensors[0].shape),
        "batch_shape": list(batch.shape),
        "batch_dtype": str(batch.dtype),
        "batch_range": [batch.min().item(), batch.max().item()],
        "labels": labels.tolist(),
        "labels_shape": list(labels.shape),
        "labels_dtype": str(labels.dtype),
    }
    (tables_dir / "inspection_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"样本总数：{len(samples)}；类别数量：{dict(counts)}")
    print(f"原图（宽、高、颜色模式）：{dict(image_formats)}")
    print(f"单张张量 [C, H, W]：{list(tensors[0].shape)}")
    print(f"批次张量 [B, C, H, W]：{list(batch.shape)}，{batch.dtype}")
    print(f"批次像素范围：{summary['batch_range']}")
    print(f"类别编号：{CLASS_TO_IDX}")
    print(f"标签：{labels.tolist()}，形状 {list(labels.shape)}，{labels.dtype}")
    print(f"九宫格：{figure_path}")
    print(f"探索记录：{tables_dir / 'inspection_summary.json'}")


if __name__ == "__main__":
    main()
