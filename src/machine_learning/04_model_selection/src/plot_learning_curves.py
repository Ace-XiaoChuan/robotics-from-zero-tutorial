"""为选定的 Digits Pipeline 绘制仅使用训练集的学习曲线。"""

from __future__ import annotations

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
from sklearn.model_selection import StratifiedKFold, learning_curve

from digits_utils import (
    MODEL_SELECTION_PATH,
    RANDOM_STATE,
    TABLES_DIR,
    TRAIN_PATH,
    build_estimator,
    candidate_name,
    ensure_output_directories,
    load_split,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为训练集内部选定的 Digits 模型绘制学习曲线。")
    parser.add_argument("--train-path", type=str, default=str(TRAIN_PATH), help="训练集 CSV 路径。")
    parser.add_argument("--selection-path", type=Path, default=MODEL_SELECTION_PATH, help="模型选择 JSON 路径。")
    return parser.parse_args()


def resolve_train_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else (TRAIN_PATH.parent.parent / path)


def main() -> None:
    arguments = parse_arguments()
    ensure_output_directories()
    if not arguments.selection_path.is_file():
        raise FileNotFoundError(f"未找到模型选择结果：{arguments.selection_path}。请先运行 src/select_models.py。")

    with arguments.selection_path.open(encoding="utf-8") as file:
        selection_report = json.load(file)
    candidate = selection_report["selected_candidate"]
    cross_validation = selection_report["cross_validation"]
    features, target, _ = load_split(resolve_train_path(arguments.train_path))
    estimator = build_estimator(candidate)
    cross_validator = StratifiedKFold(
        n_splits=int(cross_validation["n_splits"]),
        shuffle=bool(cross_validation["shuffle"]),
        random_state=int(cross_validation["random_state"]),
    )
    train_sizes, train_scores, validation_scores = learning_curve(
        estimator,
        features,
        target,
        cv=cross_validator,
        scoring="accuracy",
        train_sizes=np.linspace(0.1, 1.0, 6),
        shuffle=True,
        random_state=RANDOM_STATE,
        n_jobs=1,
        error_score="raise",
    )
    results = pd.DataFrame(
        {
            "train_size": train_sizes,
            "train_accuracy_mean": train_scores.mean(axis=1),
            "train_accuracy_std": train_scores.std(axis=1, ddof=1),
            "validation_accuracy_mean": validation_scores.mean(axis=1),
            "validation_accuracy_std": validation_scores.std(axis=1, ddof=1),
        }
    )
    results.to_csv(TABLES_DIR / "learning_curve_results.csv", index=False)

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(train_sizes, results["train_accuracy_mean"], marker="o", label="Training accuracy", color="#4C78A8")
    axis.fill_between(
        train_sizes,
        results["train_accuracy_mean"] - results["train_accuracy_std"],
        results["train_accuracy_mean"] + results["train_accuracy_std"],
        alpha=0.18,
        color="#4C78A8",
    )
    axis.plot(train_sizes, results["validation_accuracy_mean"], marker="o", label="Validation accuracy", color="#F58518")
    axis.fill_between(
        train_sizes,
        results["validation_accuracy_mean"] - results["validation_accuracy_std"],
        results["validation_accuracy_mean"] + results["validation_accuracy_std"],
        alpha=0.18,
        color="#F58518",
    )
    axis.set(
        title=f"Learning curve (training data only)\n{candidate_name(candidate)}",
        xlabel="Training samples per cross-validation fold",
        ylabel="Accuracy",
        ylim=(0.75, 1.01),
    )
    axis.grid(alpha=0.25)
    axis.legend(loc="lower right")
    figure.tight_layout()
    output_path = TABLES_DIR.parent / "figures" / "learning_curve_selected_model.png"
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print("学习曲线已生成（只使用训练集）")
    print(f"选定模型：{candidate_name(candidate)}")
    print(f"图表：{output_path}")
    print(f"数据表：{TABLES_DIR / 'learning_curve_results.csv'}")


if __name__ == "__main__":
    main()
