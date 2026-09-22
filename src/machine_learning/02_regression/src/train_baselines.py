"""训练 Ames Housing 的均值参照模型与线性回归基线，并保存评估结果。"""

import argparse
import json
import os
import tempfile
from pathlib import Path

import joblib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week02_regression_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train.csv"
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test.csv"
SPLIT_METADATA_PATH = PROJECT_DIR / "data" / "split_metadata.json"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_COLUMN = "SalePrice"
IDENTIFIER_COLUMNS = ["Order", "PID"]
FORCE_CATEGORICAL_COLUMNS = ["MS SubClass", "Mo Sold"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Ames Housing regression baselines.")
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH, help="训练集 CSV 路径。")
    parser.add_argument("--test-path", type=Path, default=DEFAULT_TEST_PATH, help="测试集 CSV 路径。")
    return parser.parse_args()


def load_features_and_target(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """读取已划分的数据，分开输入特征和房价目标。"""
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到数据文件：{data_path}")

    data = pd.read_csv(data_path)
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"数据中没有目标列 {TARGET_COLUMN!r}：{data_path}")

    y = data[TARGET_COLUMN].copy()
    x = data.drop(columns=[TARGET_COLUMN, *IDENTIFIER_COLUMNS], errors="ignore").copy()
    return x, y


def identify_feature_columns(features: pd.DataFrame) -> tuple[list[str], list[str]]:
    """将数值代码字段显式归为类别，其余按数据类型识别。"""
    forced_categories = [column for column in FORCE_CATEGORICAL_COLUMNS if column in features.columns]
    inferred_numeric = features.select_dtypes(include="number").columns.tolist()
    numeric_columns = [column for column in inferred_numeric if column not in forced_categories]
    categorical_columns = [column for column in features.columns if column not in numeric_columns]
    return numeric_columns, categorical_columns


def prepare_categorical_values(features: pd.DataFrame, categorical_columns: list[str]) -> pd.DataFrame:
    """统一类别的表示形式；真正的缺失值仍交由 Pipeline 内的填补器处理。"""
    prepared = features.copy()
    for column in categorical_columns:
        prepared[column] = prepared[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return prepared


def build_linear_regression_pipeline(numeric_columns: list[str], categorical_columns: list[str]) -> Pipeline:
    """构建“预处理 → 线性回归”的无泄漏工作流。"""
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
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        verbose_feature_names_out=False,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", LinearRegression())])


def calculate_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    return {
        "mse": float(mean_squared_error(y_true, predictions)),
        "mae": float(mean_absolute_error(y_true, predictions)),
        "r2": float(r2_score(y_true, predictions)),
    }


def evaluate_model(model, x_train: pd.DataFrame, y_train: pd.Series, x_test: pd.DataFrame, y_test: pd.Series) -> tuple[dict, np.ndarray]:
    train_predictions = model.predict(x_train)
    test_predictions = model.predict(x_test)
    metrics = {
        "train": calculate_metrics(y_train, train_predictions),
        "test": calculate_metrics(y_test, test_predictions),
    }
    return metrics, test_predictions


def save_actual_vs_predicted_plot(
    y_test: pd.Series, mean_predictions: np.ndarray, linear_predictions: np.ndarray
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True)
    lower_bound = min(y_test.min(), mean_predictions.min(), linear_predictions.min())
    upper_bound = max(y_test.max(), mean_predictions.max(), linear_predictions.max())

    for axis, predictions, title in (
        (axes[0], mean_predictions, "Mean reference"),
        (axes[1], linear_predictions, "Linear regression"),
    ):
        axis.scatter(y_test, predictions, alpha=0.55, s=18, color="#4C78A8")
        axis.plot([lower_bound, upper_bound], [lower_bound, upper_bound], "--", color="#E45756")
        axis.set_title(title)
        axis.set_xlabel("Actual SalePrice (USD)")
        axis.ticklabel_format(style="plain", axis="both")
    axes[0].set_ylabel("Predicted SalePrice (USD)")
    figure.suptitle("Test Set: Actual vs. Predicted SalePrice")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "actual_vs_predicted.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_residual_plot(y_test: pd.Series, linear_predictions: np.ndarray) -> None:
    residuals = y_test.to_numpy() - linear_predictions
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.scatter(linear_predictions, residuals, alpha=0.6, s=20, color="#4C78A8")
    axis.axhline(0, color="#E45756", linestyle="--")
    axis.set_title("Linear Regression Residuals (Test Set)")
    axis.set_xlabel("Predicted SalePrice (USD)")
    axis.set_ylabel("Residual: Actual - Predicted (USD)")
    axis.ticklabel_format(style="plain", axis="both")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "residual_plot.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_largest_errors(x_test: pd.DataFrame, y_test: pd.Series, predictions: np.ndarray) -> pd.DataFrame:
    errors = x_test.copy()
    errors["actual_saleprice"] = y_test.to_numpy()
    errors["predicted_saleprice"] = predictions
    errors["residual"] = errors["actual_saleprice"] - errors["predicted_saleprice"]
    errors["absolute_error"] = errors["residual"].abs()
    largest_errors = errors.sort_values("absolute_error", ascending=False).head(5)
    largest_errors.to_csv(OUTPUT_DIR / "largest_errors.csv", index=False)
    return largest_errors


def print_metric_table(all_metrics: dict[str, dict[str, dict[str, float]]]) -> None:
    rows = []
    for model_name, model_metrics in all_metrics.items():
        for split_name, metric_values in model_metrics.items():
            rows.append(
                {
                    "模型": model_name,
                    "数据集": "训练集" if split_name == "train" else "测试集",
                    "MSE": metric_values["mse"],
                    "MAE": metric_values["mae"],
                    "R²": metric_values["r2"],
                }
            )
    table = pd.DataFrame(rows)
    print(table.to_string(index=False, formatters={"MSE": "{:,.0f}".format, "MAE": "{:,.0f}".format, "R²": "{:.3f}".format}))


def load_split_metadata() -> dict:
    """读取固定切分的可复现信息；文件缺失时不阻止模型训练。"""
    if not SPLIT_METADATA_PATH.is_file():
        return {}
    with SPLIT_METADATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    arguments = parse_arguments()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    x_train, y_train = load_features_and_target(arguments.train_path)
    x_test, y_test = load_features_and_target(arguments.test_path)
    numeric_columns, categorical_columns = identify_feature_columns(x_train)
    x_train = prepare_categorical_values(x_train, categorical_columns)
    x_test = prepare_categorical_values(x_test, categorical_columns)

    # fit 的含义：在训练数据上学习。均值参照只记住 y_train 的平均房价。
    mean_reference = DummyRegressor(strategy="mean")
    mean_reference.fit(x_train, y_train)

    # Pipeline.fit 会按顺序在训练集上学习填补规则、标准化参数、类别列表和线性回归权重。
    linear_regression = build_linear_regression_pipeline(numeric_columns, categorical_columns)
    linear_regression.fit(x_train, y_train)

    mean_metrics, mean_test_predictions = evaluate_model(mean_reference, x_train, y_train, x_test, y_test)
    linear_metrics, linear_test_predictions = evaluate_model(linear_regression, x_train, y_train, x_test, y_test)
    all_metrics = {"mean_reference": mean_metrics, "linear_regression": linear_metrics}

    save_actual_vs_predicted_plot(y_test, mean_test_predictions, linear_test_predictions)
    save_residual_plot(y_test, linear_test_predictions)
    largest_errors = save_largest_errors(x_test, y_test, linear_test_predictions)
    joblib.dump(linear_regression, OUTPUT_DIR / "linear_regression_pipeline.joblib")

    results = {
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "data_split": load_split_metadata(),
        "target_column": TARGET_COLUMN,
        "excluded_identifier_columns": IDENTIFIER_COLUMNS,
        "numeric_feature_count": len(numeric_columns),
        "categorical_feature_count": len(categorical_columns),
        "mean_saleprice_from_training_set": float(mean_reference.constant_[0, 0]),
        "metrics": all_metrics,
        "largest_absolute_test_error": float(largest_errors.iloc[0]["absolute_error"]),
    }
    with (OUTPUT_DIR / "regression_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("均值参照模型与线性回归基线训练完成\n")
    print(f"训练集平均房价（均值参照的固定预测）：${results['mean_saleprice_from_training_set']:,.2f}")
    print_metric_table(all_metrics)
    print("\n输出文件：")
    print(f"- {OUTPUT_DIR / 'regression_metrics.json'}")
    print(f"- {OUTPUT_DIR / 'actual_vs_predicted.png'}")
    print(f"- {OUTPUT_DIR / 'residual_plot.png'}")
    print(f"- {OUTPUT_DIR / 'largest_errors.csv'}")


if __name__ == "__main__":
    main()
