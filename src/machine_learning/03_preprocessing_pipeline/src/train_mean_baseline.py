"""训练泰坦尼克号生存预测的先验概率（均值）基线。"""

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
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train_split.csv"
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test_split.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_COLUMN = "Survived"
NUMERIC_COLUMNS = ["Age", "SibSp", "Parch", "Fare"]
CATEGORICAL_COLUMNS = ["Pclass", "Sex", "Embarked"]
FEATURE_COLUMNS = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Titanic's prior-probability baseline.")
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH, help="训练集 CSV 路径。")
    parser.add_argument("--test-path", type=Path, default=DEFAULT_TEST_PATH, help="测试集 CSV 路径。")
    return parser.parse_args()


def load_features_and_target(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """读取已切分数据，并只保留已确定的七个输入特征。"""
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到数据文件：{data_path}。请先运行 src/split_titanic.py。")

    data = pd.read_csv(data_path)
    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据缺少必需字段：{missing_columns}")
    return data[FEATURE_COLUMNS].copy(), data[TARGET_COLUMN].copy()


def prepare_categorical_values(features: pd.DataFrame) -> pd.DataFrame:
    """将 Pclass 明确视为类别；空值保留为空，交给 Pipeline 内的填补器。"""
    prepared = features.copy()
    for column in CATEGORICAL_COLUMNS:
        prepared[column] = prepared[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return prepared


def build_preprocessor() -> ColumnTransformer:
    """构建七个特征的无泄漏预处理器。"""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
        ],
        verbose_feature_names_out=False,
    )


def calculate_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
    }


def save_confusion_matrix(y_test: pd.Series, predictions: np.ndarray) -> list[list[int]]:
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    figure, axis = plt.subplots(figsize=(5, 4))
    image = axis.imshow(matrix, cmap="Blues")
    figure.colorbar(image, ax=axis)
    axis.set(
        title="Mean / Prior Baseline: Test Confusion Matrix",
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
    figure.savefig(OUTPUT_DIR / "figures" / "mean_baseline_confusion_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(figure)
    return matrix.tolist()


def main() -> None:
    arguments = parse_arguments()
    for directory in (OUTPUT_DIR / "figures", OUTPUT_DIR / "models", OUTPUT_DIR / "tables"):
        directory.mkdir(parents=True, exist_ok=True)

    x_train, y_train = load_features_and_target(arguments.train_path)
    x_test, y_test = load_features_and_target(arguments.test_path)
    x_train = prepare_categorical_values(x_train)
    x_test = prepare_categorical_values(x_test)

    # Pipeline.fit 只从训练集学习：数值中位数、标准化参数、类别列表和类别先验概率。
    # DummyClassifier(strategy="prior") 的生存概率等于训练集 Survived 的平均值；
    # 因本训练集平均值小于 0.5，它的类别预测会全部为“未生存”。
    mean_baseline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", DummyClassifier(strategy="prior")),
        ]
    )
    mean_baseline.fit(x_train, y_train)

    train_predictions = mean_baseline.predict(x_train)
    test_predictions = mean_baseline.predict(x_test)
    test_probabilities = mean_baseline.predict_proba(x_test)[:, 1]
    train_survival_rate = float(y_train.mean())

    metrics = {
        "train": calculate_metrics(y_train, train_predictions),
        "test": calculate_metrics(y_test, test_predictions),
    }
    matrix = save_confusion_matrix(y_test, test_predictions)
    prediction_table = x_test.copy()
    prediction_table["actual_survived"] = y_test.to_numpy()
    prediction_table["predicted_survived"] = test_predictions
    prediction_table["predicted_survival_probability"] = test_probabilities
    prediction_table.to_csv(OUTPUT_DIR / "tables" / "mean_baseline_predictions.csv", index=False)
    joblib.dump(mean_baseline, OUTPUT_DIR / "models" / "mean_baseline_pipeline.joblib")

    results = {
        "model": "DummyClassifier(strategy='prior')",
        "meaning": "对每名乘客预测训练集中的平均生存概率；类别输出为训练集中占多数的类别。",
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "numeric_preprocessing": "median imputation -> standard scaling",
        "categorical_preprocessing": "constant 'Missing' imputation -> one-hot encoding",
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "training_survival_rate": train_survival_rate,
        "metrics": metrics,
        "test_confusion_matrix_labels": [0, 1],
        "test_confusion_matrix": matrix,
    }
    with (OUTPUT_DIR / "tables" / "mean_baseline_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("均值（先验概率）基线训练完成\n")
    print(f"训练集平均生存率：{train_survival_rate:.3f}")
    print("它对每名乘客给出相同的生存概率；类别预测使用多数类。")
    for split_name, split_metrics in metrics.items():
        print(
            f"{split_name}: accuracy={split_metrics['accuracy']:.3f}, "
            f"precision={split_metrics['precision']:.3f}, recall={split_metrics['recall']:.3f}, "
            f"f1={split_metrics['f1']:.3f}"
        )
    print("\n输出文件：")
    print(f"- {OUTPUT_DIR / 'tables' / 'mean_baseline_metrics.json'}")
    print(f"- {OUTPUT_DIR / 'tables' / 'mean_baseline_predictions.csv'}")
    print(f"- {OUTPUT_DIR / 'figures' / 'mean_baseline_confusion_matrix.png'}")
    print(f"- {OUTPUT_DIR / 'models' / 'mean_baseline_pipeline.joblib'}")


if __name__ == "__main__":
    main()
