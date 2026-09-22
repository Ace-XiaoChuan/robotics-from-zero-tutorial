"""在一次性保留的测试集上评估已选定的泰坦尼克号模型。"""

import argparse
import json
import os
import tempfile
from pathlib import Path

import joblib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week03_titanic_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test_split.csv"
DEFAULT_MODEL_PATH = PROJECT_DIR / "outputs" / "models" / "best_cross_validated_pipeline.joblib"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_COLUMN = "Survived"
CATEGORICAL_COLUMNS = ["Pclass", "Sex", "Embarked"]
FEATURE_COLUMNS = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the selected Titanic model on the held-out test set.")
    parser.add_argument("--test-path", type=Path, default=DEFAULT_TEST_PATH, help="保留测试集 CSV 路径。")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH, help="已拟合模型 Pipeline 路径。")
    return parser.parse_args()


def load_features_and_target(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到测试集：{data_path}。请先运行 src/split_titanic.py。")
    data = pd.read_csv(data_path)
    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据缺少必需字段：{missing_columns}")
    return data[FEATURE_COLUMNS].copy(), data[TARGET_COLUMN].copy()


def prepare_categorical_values(features: pd.DataFrame) -> pd.DataFrame:
    """保持与训练阶段相同的类别字段类型；空值仍由已拟合 Pipeline 填补。"""
    prepared = features.copy()
    for column in CATEGORICAL_COLUMNS:
        prepared[column] = prepared[column].map(lambda value: str(value) if pd.notna(value) else float("nan"))
    return prepared


def calculate_metrics(y_true: pd.Series, predictions: pd.Series) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
    }


def save_confusion_matrix(y_true: pd.Series, predictions: pd.Series) -> list[list[int]]:
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    figure, axis = plt.subplots(figsize=(5, 4))
    image = axis.imshow(matrix, cmap="Blues")
    figure.colorbar(image, ax=axis)
    axis.set(
        title="Selected Model: Final Test Confusion Matrix",
        xlabel="Predicted label",
        ylabel="True label",
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["Not survived (0)", "Survived (1)"],
        yticklabels=["Not survived (0)", "Survived (1)"],
    )
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, str(matrix[row_index, column_index]), ha="center", va="center")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "figures" / "final_test_confusion_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(figure)
    return matrix.tolist()


def main() -> None:
    arguments = parse_arguments()
    if not arguments.model_path.is_file():
        raise FileNotFoundError(f"未找到已选模型：{arguments.model_path}。请先运行 src/train_models.py。")
    for directory in (OUTPUT_DIR / "figures", OUTPUT_DIR / "tables"):
        directory.mkdir(parents=True, exist_ok=True)

    x_test, y_test = load_features_and_target(arguments.test_path)
    x_test = prepare_categorical_values(x_test)
    model = joblib.load(arguments.model_path)

    # 这里刻意只调用 predict / predict_proba；不能在测试集上调用 fit 或 fit_transform。
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    metrics = calculate_metrics(y_test, predictions)
    matrix = save_confusion_matrix(y_test, predictions)

    prediction_table = x_test.copy()
    prediction_table["actual_survived"] = y_test.to_numpy()
    prediction_table["predicted_survived"] = predictions
    prediction_table["predicted_survival_probability"] = probabilities
    prediction_table["is_correct"] = prediction_table["actual_survived"] == prediction_table["predicted_survived"]
    prediction_table.to_csv(OUTPUT_DIR / "tables" / "final_test_predictions.csv", index=False)
    errors = prediction_table.loc[~prediction_table["is_correct"]].sort_values("predicted_survival_probability")
    errors.to_csv(OUTPUT_DIR / "tables" / "final_test_errors.csv", index=False)

    report = {
        "model_path": str(arguments.model_path.relative_to(PROJECT_DIR)),
        "test_data_path": str(arguments.test_path.relative_to(PROJECT_DIR)),
        "test_samples": len(x_test),
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "metrics": metrics,
        "confusion_matrix_labels": [0, 1],
        "confusion_matrix": matrix,
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "test_set_used_for_fitting": False,
    }
    with (OUTPUT_DIR / "tables" / "final_test_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print("最终测试集评估完成（测试集未参与模型拟合）\n")
    print(f"测试集样本数：{len(x_test)}")
    print(
        f"accuracy={metrics['accuracy']:.3f}, precision={metrics['precision']:.3f}, "
        f"recall={metrics['recall']:.3f}, f1={metrics['f1']:.3f}"
    )
    print(f"混淆矩阵（行=真实 0/1，列=预测 0/1）：{matrix}")
    print("\n输出文件：")
    print(f"- {OUTPUT_DIR / 'tables' / 'final_test_metrics.json'}")
    print(f"- {OUTPUT_DIR / 'tables' / 'final_test_predictions.csv'}")
    print(f"- {OUTPUT_DIR / 'tables' / 'final_test_errors.csv'}")
    print(f"- {OUTPUT_DIR / 'figures' / 'final_test_confusion_matrix.png'}")


if __name__ == "__main__":
    main()
