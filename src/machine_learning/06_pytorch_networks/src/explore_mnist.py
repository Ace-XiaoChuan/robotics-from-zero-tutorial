"""Explore the local MNIST dataset without training a model.

This script is the first executable step of Week 6. It answers four questions:

1. How many samples are in the official train and test portions?
2. What do one sample and one batch look like as tensors?
3. How many official-training examples belong to each digit class?
4. What do representative handwritten digits look like?

It never trains a model and never downloads or modifies the source dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_DIR / "data"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs"

# Matplotlib otherwise tries to create a cache below the user's home directory.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week06_mnist_mplconfig")
)

import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the local MNIST dataset and save learning-note outputs."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing MNIST/raw (default: project data directory).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for figures and tables (default: project outputs directory).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size used only for demonstrating DataLoader output.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="DataLoader worker processes; zero is the most portable choice.",
    )
    return parser.parse_args()


def load_local_mnist(data_dir: Path) -> tuple[datasets.MNIST, datasets.MNIST]:
    """Load already-downloaded MNIST files and fail clearly if they are absent."""

    transform = transforms.ToTensor()
    try:
        train_dataset = datasets.MNIST(
            root=data_dir, train=True, transform=transform, download=False
        )
        test_dataset = datasets.MNIST(
            root=data_dir, train=False, transform=transform, download=False
        )
    except RuntimeError as exc:
        raise RuntimeError(
            f"MNIST was not found below {data_dir / 'MNIST'}. "
            "Download and extract the four raw IDX files before running this script."
        ) from exc

    return train_dataset, test_dataset


def class_counts(dataset: datasets.MNIST) -> np.ndarray:
    """Count labels 0 through 9 in a torchvision MNIST dataset."""

    targets = dataset.targets.detach().cpu().numpy()
    return np.bincount(targets, minlength=10)


def first_index_per_class(targets: torch.Tensor) -> list[int]:
    """Return the first sample index for every digit label."""

    indices: list[int] = []
    for digit in range(10):
        matches = torch.nonzero(targets == digit, as_tuple=False)
        if matches.numel() == 0:
            raise ValueError(f"Dataset contains no sample for digit {digit}.")
        indices.append(int(matches[0].item()))
    return indices


def save_class_distribution(
    train_counts: np.ndarray,
    figures_dir: Path,
    tables_dir: Path,
) -> None:
    """Save official-training class counts and a percentage bar chart."""

    csv_path = tables_dir / "class_distribution.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "digit",
                "count",
                "percent",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for digit in range(10):
            writer.writerow(
                {
                    "digit": digit,
                    "count": int(train_counts[digit]),
                    "percent": round(
                        100 * int(train_counts[digit]) / int(train_counts.sum()), 4
                    ),
                }
            )

    digits = np.arange(10)
    train_percent = 100 * train_counts / train_counts.sum()
    figure, axis = plt.subplots(figsize=(10, 5.5))
    train_bars = axis.bar(
        digits,
        train_percent,
        width=0.65,
        color="#4C78A8",
    )
    axis.bar_label(train_bars, padding=2, fontsize=8, fmt="%.2f")
    axis.set_title("MNIST official-training class proportions")
    axis.set_xlabel("Digit label")
    axis.set_ylabel("Share of official training portion (%)")
    axis.set_xticks(digits)
    axis.set_ylim(0, train_percent.max() + 1.5)
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    figure.savefig(figures_dir / "class_distribution.png", dpi=160)
    plt.close(figure)


def save_representative_samples(
    train_dataset: datasets.MNIST, figures_dir: Path
) -> list[int]:
    """Save the first official-train example for every digit class."""

    sample_indices = first_index_per_class(train_dataset.targets)
    figure, axes = plt.subplots(2, 5, figsize=(12, 6.5), constrained_layout=True)

    for digit, (axis, sample_index) in enumerate(zip(axes.flat, sample_indices)):
        image, label = train_dataset[sample_index]
        axis.imshow(image.squeeze(0).numpy(), cmap="gray", vmin=0.0, vmax=1.0)
        axis.set_title(f"label={label}, index={sample_index}")
        axis.axis("off")

    figure.suptitle("One representative MNIST training image per digit", fontsize=14)
    figure.savefig(figures_dir / "mnist_representative_samples.png", dpi=160)
    plt.close(figure)
    return sample_indices


def save_dataset_overview(
    train_dataset: datasets.MNIST,
    test_dataset: datasets.MNIST,
    batch_images: torch.Tensor,
    batch_labels: torch.Tensor,
    train_counts: np.ndarray,
    representative_indices: list[int],
    batch_size: int,
    num_workers: int,
    tables_dir: Path,
) -> dict[str, object]:
    """Save the main facts needed to review MNIST tensor structure later."""

    sample_image, sample_label = train_dataset[0]
    raw_sample = train_dataset.data[0]

    overview: dict[str, object] = {
        "dataset": "MNIST",
        "task": "10-class handwritten digit classification",
        "classes": list(range(10)),
        "software": {
            "python_torch": torch.__version__,
            "torchvision": torchvision.__version__,
        },
        "official_portions": {
            "train_samples": len(train_dataset),
            "test_samples": len(test_dataset),
            "train_class_counts": {
                str(digit): int(train_counts[digit]) for digit in range(10)
            },
            "test_class_counts": "not inspected before final evaluation",
        },
        "raw_storage": {
            "train_images_shape": list(train_dataset.data.shape),
            "train_labels_shape": list(train_dataset.targets.shape),
            "single_image_shape": list(raw_sample.shape),
            "image_dtype": str(raw_sample.dtype),
            "pixel_min": int(train_dataset.data.min().item()),
            "pixel_max": int(train_dataset.data.max().item()),
        },
        "after_to_tensor": {
            "single_image_shape": list(sample_image.shape),
            "single_label": int(sample_label),
            "image_dtype": str(sample_image.dtype),
            "pixel_min": float(sample_image.min().item()),
            "pixel_max": float(sample_image.max().item()),
        },
        "inspection_dataloader": {
            "batch_size": batch_size,
            "shuffle": False,
            "num_workers": num_workers,
            "image_batch_shape": list(batch_images.shape),
            "label_batch_shape": list(batch_labels.shape),
            "image_dtype": str(batch_images.dtype),
            "label_dtype": str(batch_labels.dtype),
            "label_min": int(batch_labels.min().item()),
            "label_max": int(batch_labels.max().item()),
        },
        "representative_train_indices": {
            str(digit): representative_indices[digit] for digit in range(10)
        },
        "important_boundary": (
            "Before final evaluation, the official test portion is checked only for "
            "availability and total length. Its images and label distribution are not explored."
        ),
    }

    overview_path = tables_dir / "dataset_overview.json"
    with overview_path.open("w", encoding="utf-8") as file:
        json.dump(overview, file, ensure_ascii=False, indent=2)
        file.write("\n")

    return overview


def main() -> None:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be a positive integer.")
    if args.num_workers < 0:
        raise ValueError("--num-workers cannot be negative.")

    data_dir = args.data_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    train_dataset, test_dataset = load_local_mnist(data_dir)
    inspection_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )
    batch_images, batch_labels = next(iter(inspection_loader))

    train_counts = class_counts(train_dataset)
    representative_indices = save_representative_samples(train_dataset, figures_dir)
    save_class_distribution(train_counts, figures_dir, tables_dir)
    overview = save_dataset_overview(
        train_dataset=train_dataset,
        test_dataset=test_dataset,
        batch_images=batch_images,
        batch_labels=batch_labels,
        train_counts=train_counts,
        representative_indices=representative_indices,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        tables_dir=tables_dir,
    )

    print("MNIST data exploration complete")
    print(
        f"Official portions: train={len(train_dataset):,}, "
        f"test={len(test_dataset):,}"
    )
    print(
        "Raw storage: "
        f"shape={tuple(train_dataset.data.shape)}, "
        f"dtype={train_dataset.data.dtype}, "
        f"range=[{overview['raw_storage']['pixel_min']}, "
        f"{overview['raw_storage']['pixel_max']}]"
    )
    print(
        "First transformed sample: "
        f"shape={tuple(train_dataset[0][0].shape)}, "
        f"dtype={train_dataset[0][0].dtype}, label={train_dataset[0][1]}"
    )
    print(
        "Inspection batch: "
        f"images={tuple(batch_images.shape)}, labels={tuple(batch_labels.shape)}"
    )
    print(f"Figures: {figures_dir}")
    print(f"Tables: {tables_dir}")


if __name__ == "__main__":
    main()
