"""可视化并汇总 scikit-learn 内置的 Digits 数据集。"""

import argparse
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week04_digits_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import load_digits


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"
DEFAULT_TABLES_DIR = PROJECT_DIR / "outputs" / "tables"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize feature types and distributions in the Digits dataset.")
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR, help="图表输出目录。")
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR, help="表格输出目录。")
    return parser.parse_args()


def save_sample_grid(images: np.ndarray, targets: np.ndarray, output_path: Path) -> None:
    """为每个数字类别保存一张代表性的 8×8 图像，并额外保留若干示例。"""
    figure, axes = plt.subplots(3, 10, figsize=(13, 4.2))
    selected_indices = list(range(10)) + list(range(10, 30))

    for axis, index in zip(axes.flat, selected_indices):
        axis.imshow(images[index], cmap="gray_r", interpolation="nearest", vmin=0, vmax=16)
        axis.set_title(f"label={targets[index]}", fontsize=9)
        axis.set_xticks([])
        axis.set_yticks([])

    figure.suptitle("Digits samples: each image has 8 x 8 pixel-intensity features", y=1.01)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_target_distribution(targets: np.ndarray, output_path: Path) -> None:
    """保存每个目标数字的样本数量。"""
    classes, counts = np.unique(targets, return_counts=True)
    figure, axis = plt.subplots(figsize=(8, 4.5))
    bars = axis.bar(classes, counts, color="#4C78A8")
    axis.bar_label(bars, padding=3)
    axis.set(
        title="Target label distribution",
        xlabel="Digit class (target)",
        ylabel="Number of samples",
        xticks=classes,
        ylim=(0, int(counts.max()) + 20),
    )
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_pixel_value_distribution(features: np.ndarray, output_path: Path) -> None:
    """保存全部数值型像素强度的分布。"""
    values, counts = np.unique(features, return_counts=True)
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.bar(values, counts, width=0.8, color="#F58518")
    axis.set(
        title="Distribution of all 64 pixel-intensity features",
        xlabel="Pixel intensity (0 = background, 16 = strongest stroke)",
        ylabel="Number of pixel values",
        xticks=values,
    )
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_pixel_statistics(images: np.ndarray, output_path: Path) -> None:
    """可视化数据集中像素的亮度、变化程度和非零位置。"""
    statistics = [
        (images.mean(axis=0), "Mean intensity"),
        (images.std(axis=0), "Standard deviation"),
        ((images > 0).mean(axis=0), "Nonzero rate"),
    ]
    figure, axes = plt.subplots(1, 3, figsize=(11, 3.8))

    for axis, (matrix, title) in zip(axes, statistics):
        image = axis.imshow(matrix, cmap="viridis", interpolation="nearest")
        axis.set_title(title)
        axis.set_xlabel("Pixel column")
        axis.set_ylabel("Pixel row")
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)

    figure.suptitle("Feature statistics mapped back to the 8 x 8 image", y=1.02)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_single_sample_storage(image: np.ndarray, target: int, sample_index: int, output_path: Path) -> None:
    """展示一个图像样本实际存储的 8×8 数值矩阵。"""
    figure, axis = plt.subplots(figsize=(6.5, 5.5))
    display = axis.imshow(image, cmap="gray_r", interpolation="nearest", vmin=0, vmax=16)
    axis.set(
        title=(
            f"Sample {sample_index}, label={target}: stored as an 8 x 8 intensity matrix\n"
            "Flattened row by row into 64 input features"
        ),
        xlabel="Pixel column",
        ylabel="Pixel row",
        xticks=np.arange(8),
        yticks=np.arange(8),
    )
    for row in range(image.shape[0]):
        for column in range(image.shape[1]):
            value = int(image[row, column])
            text_color = "white" if value < 8 else "black"
            axis.text(column, row, str(value), ha="center", va="center", color=text_color, fontsize=10)
    figure.colorbar(display, ax=axis, label="Pixel intensity (0 to 16)")
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def build_feature_summary(features: np.ndarray) -> pd.DataFrame:
    """为 64 个像素特征分别创建一行描述性统计信息。"""
    records = []
    for index in range(features.shape[1]):
        row, column = divmod(index, 8)
        values = features[:, index]
        records.append(
            {
                "feature": f"pixel_{row}_{column}",
                "feature_index": index,
                "image_row": row,
                "image_column": column,
                "semantic_type": "numeric_pixel_intensity",
                "storage_dtype": str(features.dtype),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "mean": float(values.mean()),
                "standard_deviation": float(values.std()),
                "zero_rate": float((values == 0).mean()),
                "unique_value_count": int(np.unique(values).size),
            }
        )
    return pd.DataFrame(records)


def main() -> None:
    arguments = parse_arguments()
    arguments.figures_dir.mkdir(parents=True, exist_ok=True)
    arguments.tables_dir.mkdir(parents=True, exist_ok=True)

    digits = load_digits()
    features = digits.data
    images = digits.images
    targets = digits.target

    save_sample_grid(images, targets, arguments.figures_dir / "digits_samples.png")
    save_target_distribution(targets, arguments.figures_dir / "target_distribution.png")
    save_pixel_value_distribution(features, arguments.figures_dir / "pixel_value_distribution.png")
    save_pixel_statistics(images, arguments.figures_dir / "pixel_feature_statistics.png")

    sample_index = 0
    sample_image = images[sample_index]
    sample_target = int(targets[sample_index])
    save_single_sample_storage(
        sample_image,
        sample_target,
        sample_index,
        arguments.figures_dir / "single_sample_storage.png",
    )

    summary = build_feature_summary(features)
    summary.to_csv(arguments.tables_dir / "feature_summary.csv", index=False)

    classes, class_counts = np.unique(targets, return_counts=True)
    overview = {
        "dataset": "scikit-learn Digits",
        "samples": int(features.shape[0]),
        "image_shape": list(images.shape[1:]),
        "feature_count": int(features.shape[1]),
        "feature_semantic_type": "64 numeric pixel-intensity features (pixel_0_0 through pixel_7_7)",
        "feature_storage_dtype": str(features.dtype),
        "feature_value_range": [float(features.min()), float(features.max())],
        "missing_feature_values": int(np.isnan(features).sum()),
        "target_semantic_type": "multiclass digit label",
        "target_storage_dtype": str(targets.dtype),
        "target_classes": [int(value) for value in classes],
        "target_class_counts": {str(label): int(count) for label, count in zip(classes, class_counts)},
    }
    with (arguments.tables_dir / "dataset_overview.json").open("w", encoding="utf-8") as file:
        json.dump(overview, file, ensure_ascii=False, indent=2)

    sample_storage = {
        "sample_index": sample_index,
        "target_label": sample_target,
        "image_shape": [int(value) for value in sample_image.shape],
        "storage_dtype": str(features.dtype),
        "matrix": sample_image.astype(int).tolist(),
        "flattening_order": "row-major: pixel_0_0, pixel_0_1, ..., pixel_7_7",
        "flattened_features": features[sample_index].astype(int).tolist(),
    }
    with (arguments.tables_dir / "single_sample_storage.json").open("w", encoding="utf-8") as file:
        json.dump(sample_storage, file, ensure_ascii=False, indent=2)

    print("Digits 数据探索完成")
    print(f"样本数：{overview['samples']}；图像尺寸：{images.shape[1]} x {images.shape[2]}")
    print(f"特征：{overview['feature_count']} 个数值像素强度，范围 {overview['feature_value_range']}")
    print(f"标签：{overview['target_semantic_type']}，类别 {overview['target_classes']}")
    print(f"缺失特征值：{overview['missing_feature_values']}")
    print(f"示例样本：索引 {sample_index}，标签 {sample_target}；其 8 x 8 矩阵和 64 个展平特征已导出。")
    print(f"图表目录：{arguments.figures_dir}")
    print(f"表格目录：{arguments.tables_dir}")


if __name__ == "__main__":
    main()
