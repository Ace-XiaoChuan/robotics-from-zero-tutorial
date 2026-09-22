"""Check local training data and save a reproducible train/validation split.

Only indices are saved: images are neither copied nor changed. The official
test portion is not loaded. Run this file before implementing model training.
"""

import json
from pathlib import Path

import torch
from torchvision.datasets import MNIST


PROJECT_DIR = Path(__file__).resolve().parents[1]
SEED = 42


def main() -> None:
    dataset = MNIST(PROJECT_DIR / "data", train=True, download=False)
    images, labels = dataset.data, dataset.targets
    assert images.shape == (60000, 28, 28)
    assert labels.shape == (60000,)
    assert images.dtype == torch.uint8
    assert labels.dtype == torch.int64
    assert bool(((labels >= 0) & (labels <= 9)).all())

    # A dedicated generator keeps this split independent of other random calls.
    indices = torch.randperm(len(dataset), generator=torch.Generator().manual_seed(SEED))
    train_indices, validation_indices = indices[:50000], indices[50000:]
    assert len(torch.unique(indices)) == 60000
    assert int(indices.min()) == 0 and int(indices.max()) == 59999

    counts = {}
    for name, subset in (("train", train_indices), ("validation", validation_indices)):
        counts[name] = torch.bincount(labels[subset], minlength=10).tolist()

    output_dir = PROJECT_DIR / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    split = {
        "source": "MNIST official training portion; indices are zero-based",
        "method": "torch.randperm; first 50000 train, remaining 10000 validation",
        "seed": SEED,
        "torch_version": torch.__version__,
        "train_indices": train_indices.tolist(),
        "validation_indices": validation_indices.tolist(),
    }
    summary = {
        "seed": SEED,
        "train_samples": len(train_indices),
        "validation_samples": len(validation_indices),
        "official_test": "10000 samples retained separately; not loaded by this script",
        "class_counts_0_to_9": counts,
        "quality_checks": {
            "image_shape_and_dtype_valid": True,
            "image_label_counts_match": True,
            "all_labels_in_0_to_9": True,
            "raw_pixels": "uint8: values 0 to 255, no NaN representation; zero is valid background",
            "decision": "No additional cleaning needed based on integrity and basic format checks; no manual audit of every label.",
        },
        "split_checks": "Disjoint subsets, 50000/10000 sizes, all 60000 source indices covered exactly once",
    }
    for filename, content in (("mnist_split_indices.json", split), ("split_summary.json", summary)):
        (output_dir / filename).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
