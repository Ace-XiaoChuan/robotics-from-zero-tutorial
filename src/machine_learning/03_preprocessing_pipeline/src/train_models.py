"""在训练集内部用交叉验证比较泰坦尼克号分类模型。"""

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
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train_split.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_COLUMN = "Survived"
NUMERIC_COLUMNS = ["Age", "SibSp", "Parch", "Fare"]
CATEGORICAL_COLUMNS = ["Pclass", "Sex", "Embarked"]
FEATURE_COLUMNS = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
RANDOM_STATE = 42


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Titanic classifiers with cross-validation on training data.")
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH, help="训练集 CSV 路径。")
    parser.add_argument("--cv-folds", type=int, default=5, help="分层交叉验证折数，默认 5。")
    return parser.parse_args()


def load_features_and_target(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到训练集：{data_path}。请先运行 src/split_titanic.py。")
    data = pd.read_csv(data_path)
    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据缺少必需字段：{missing_columns}")
    return data[FEATURE_COLUMNS].copy(), data[TARGET_COLUMN].copy()


def prepare_categorical_values(features: pd.DataFrame) -> pd.DataFrame:
    """将 Pclass 作为类别；真正的缺失值仍由 Pipeline 中的填补器处理。"""
    prepared = features.copy()
    for column in CATEGORICAL_COLUMNS:
        prepared[column] = prepared[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return prepared


def build_preprocessor() -> ColumnTransformer:
    """返回每次交叉验证折内重新拟合的预处理器。"""
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


def build_candidate_models() -> dict[str, Pipeline]:
    """建立只更换分类器、其余处理完全一致的三条 Pipeline。"""
    classifiers = {
        "logistic_regression": LogisticRegression(max_iter=1_000, random_state=RANDOM_STATE),
        "knn_k5": KNeighborsClassifier(n_neighbors=5),
        "decision_tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
    }
    return {
        name: Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", classifier)])
        for name, classifier in classifiers.items()
    }


def selection_key(result: dict[str, object]) -> tuple[float, float, float]:
    """优先选择生存类 F1，其次召回率和准确率。"""
    means = result["means"]
    return (means["f1"], means["recall"], means["accuracy"])


def save_comparison_plot(summary: pd.DataFrame) -> None:
    metric_columns = ["accuracy_mean", "precision_mean", "recall_mean", "f1_mean"]
    figure, axis = plt.subplots(figsize=(9, 5))
    positions = np.arange(len(summary))
    width = 0.19
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]

    for index, (column, color) in enumerate(zip(metric_columns, colors)):
        axis.bar(positions + (index - 1.5) * width, summary[column], width, label=column.removesuffix("_mean"), color=color)

    axis.set(title="5-Fold Cross-Validation: Training Set Only", ylabel="Score", ylim=(0, 1))
    axis.set_xticks(positions, summary["model"].str.replace("_", " "))
    axis.legend(loc="lower right")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "figures" / "cross_validation_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    if arguments.cv_folds < 2:
        raise ValueError("--cv-folds 至少为 2。")

    for directory in (OUTPUT_DIR / "figures", OUTPUT_DIR / "models", OUTPUT_DIR / "tables"):
        directory.mkdir(parents=True, exist_ok=True)
    x_train, y_train = load_features_and_target(arguments.train_path)
    x_train = prepare_categorical_values(x_train)

    # 每一折都会只在该折的训练部分 fit 填补器、标准化器、编码器和模型，验证折不参与学习。
    cross_validator = StratifiedKFold(n_splits=arguments.cv_folds, shuffle=True, random_state=RANDOM_STATE)
    scoring = {
        "accuracy": "accuracy",
        "precision": make_scorer(precision_score, zero_division=0),
        "recall": make_scorer(recall_score, zero_division=0),
        "f1": "f1",
    }

    results: list[dict[str, object]] = []
    for model_name, pipeline in build_candidate_models().items():
        scores = cross_validate(
            pipeline,
            x_train,
            y_train,
            cv=cross_validator,
            scoring=scoring,
            return_train_score=False,
            n_jobs=1,
        )
        fold_scores = {metric: [float(value) for value in scores[f"test_{metric}"]] for metric in scoring}
        means = {metric: float(np.mean(values)) for metric, values in fold_scores.items()}
        standard_deviations = {metric: float(np.std(values, ddof=1)) for metric, values in fold_scores.items()}
        results.append(
            {
                "model": model_name,
                "fold_scores": fold_scores,
                "means": means,
                "standard_deviations": standard_deviations,
            }
        )

    best_result = max(results, key=selection_key)
    best_model_name = str(best_result["model"])
    best_pipeline = clone(build_candidate_models()[best_model_name])
    best_pipeline.fit(x_train, y_train)
    joblib.dump(best_pipeline, OUTPUT_DIR / "models" / "best_cross_validated_pipeline.joblib")

    summary_rows = []
    for result in results:
        row: dict[str, object] = {"model": result["model"]}
        for metric in scoring:
            row[f"{metric}_mean"] = result["means"][metric]
            row[f"{metric}_std"] = result["standard_deviations"][metric]
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["f1_mean", "recall_mean", "accuracy_mean"], ascending=False)
    summary.to_csv(OUTPUT_DIR / "tables" / "cross_validation_results.csv", index=False)
    save_comparison_plot(summary)

    report = {
        "data_used": "data/train_split.csv only; data/test_split.csv was not used for selection.",
        "train_samples": len(x_train),
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "preprocessing": {
            "numeric": "median imputation -> standard scaling",
            "categorical": "constant 'Missing' imputation -> one-hot encoding",
        },
        "cross_validation": {
            "method": "StratifiedKFold",
            "n_splits": arguments.cv_folds,
            "shuffle": True,
            "random_state": RANDOM_STATE,
        },
        "selection_rule": "highest mean F1 for Survived=1; ties broken by recall, then accuracy",
        "results": results,
        "selected_model": best_model_name,
        "selected_model_means": best_result["means"],
    }
    with (OUTPUT_DIR / "tables" / "model_selection.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print("训练集内部的 5 折交叉验证完成（未使用测试集）\n")
    display = summary.copy()
    for column in display.columns:
        if column != "model":
            display[column] = display[column].map(lambda value: f"{value:.3f}")
    print(display.to_string(index=False))
    print(f"\n按生存类 F1 选择的最佳模型：{best_model_name}")
    print(f"已将它使用全部 {len(x_train)} 条训练数据重新拟合并保存。")
    print("测试集仍未参与本次模型选择。")


if __name__ == "__main__":
    main()
