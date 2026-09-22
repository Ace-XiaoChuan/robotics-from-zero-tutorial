"""对选定的 Digits Pipeline 执行一次最终保留测试集评估。"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import joblib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week04_digits_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from digits_utils import (
    BEST_PIPELINE_PATH,
    FIGURES_DIR,
    MODELS_DIR,
    TABLES_DIR,
    TEST_PATH,
    ensure_output_directories,
    load_split,
    write_json,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在保留的 Digits 测试集上执行最终一次评估。")
    parser.add_argument("--test-path", type=str, default=str(TEST_PATH), help="保留测试集 CSV 路径。")
    parser.add_argument("--model-path", type=Path, default=BEST_PIPELINE_PATH, help="训练集上选定并拟合的 Pipeline。")
    parser.add_argument("--force", action="store_true", help="明确允许覆盖已有最终测试结果；仅在确有必要时使用。")
    return parser.parse_args()


def resolve_test_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else (TEST_PATH.parent.parent / path)


def save_confusion_matrix(matrix: np.ndarray, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 6))
    image = axis.imshow(matrix, cmap="Blues")
    figure.colorbar(image, ax=axis, label="Samples")
    labels = np.arange(10)
    axis.set(
        title="Final held-out test set: confusion matrix",
        xlabel="Predicted digit",
        ylabel="True digit",
        xticks=labels,
        yticks=labels,
    )
    threshold = matrix.max() / 2
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color="white" if matrix[row, column] > threshold else "black",
            )
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    ensure_output_directories()
    if not arguments.model_path.is_file():
        raise FileNotFoundError(f"未找到选定模型：{arguments.model_path}。请先运行 src/select_models.py。")
    metrics_path = TABLES_DIR / "final_test_metrics.json"
    if metrics_path.exists() and not arguments.force:
        raise FileExistsError(
            f"已存在最终测试结果：{metrics_path}。为避免将测试集反复用于调参，脚本默认拒绝再次评估。"
            "如确实需要覆盖，请显式传入 --force。"
        )

    features, target, sample_indices = load_split(resolve_test_path(arguments.test_path))
    model = joblib.load(arguments.model_path)
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)
    confidence = probabilities.max(axis=1)

    metrics = {
        "accuracy": float(accuracy_score(target, predictions)),
        "precision_macro": float(precision_score(target, predictions, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(target, predictions, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(target, predictions, average="macro", zero_division=0)),
        "test_samples": int(len(target)),
        "test_data_used_only_for_final_evaluation": True,
        "classification_report": classification_report(target, predictions, output_dict=True, zero_division=0),
    }
    matrix = confusion_matrix(target, predictions, labels=np.arange(10))
    metrics["confusion_matrix_labels"] = list(range(10))
    metrics["confusion_matrix"] = matrix.tolist()
    write_json(metrics, metrics_path)
    save_confusion_matrix(matrix, FIGURES_DIR / "final_test_confusion_matrix.png")

    prediction_table = pd.DataFrame(
        {
            "sample_index": sample_indices.to_numpy(),
            "actual_digit": target.to_numpy(),
            "predicted_digit": predictions,
            "predicted_confidence": confidence,
            "is_correct": predictions == target.to_numpy(),
        }
    )
    prediction_table.to_csv(TABLES_DIR / "final_test_predictions.csv", index=False)
    errors = prediction_table.loc[~prediction_table["is_correct"]].sort_values("predicted_confidence")
    errors.to_csv(TABLES_DIR / "final_test_errors.csv", index=False)
    joblib.dump(model, MODELS_DIR / "final_model.joblib")

    print("最终保留测试集评估完成")
    print(
        f"accuracy={metrics['accuracy']:.3f}, precision_macro={metrics['precision_macro']:.3f}, "
        f"recall_macro={metrics['recall_macro']:.3f}, f1_macro={metrics['f1_macro']:.3f}"
    )
    print(f"误分类样本：{len(errors)} / {len(target)}")
    print(f"指标：{metrics_path}")
    print(f"混淆矩阵：{FIGURES_DIR / 'final_test_confusion_matrix.png'}")


if __name__ == "__main__":
    main()
