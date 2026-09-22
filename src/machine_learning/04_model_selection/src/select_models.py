"""仅使用 Digits 训练集，通过交叉验证选择模型与超参数。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate

from digits_utils import (
    BEST_PIPELINE_PATH,
    MODEL_SELECTION_PATH,
    RANDOM_STATE,
    TABLES_DIR,
    TRAIN_PATH,
    build_estimator,
    candidate_name,
    ensure_output_directories,
    load_split,
    write_json,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="只在 Digits 训练集上比较候选模型。")
    parser.add_argument("--train-path", type=str, default=str(TRAIN_PATH), help="训练集 CSV 路径。")
    parser.add_argument("--cv-folds", type=int, default=5, help="分层交叉验证折数，默认 5。")
    return parser.parse_args()


def create_candidates() -> list[dict[str, object]]:
    """返回用于比较模型类型和预处理方式的精简候选网格。"""
    candidates: list[dict[str, object]] = []
    for preprocessing in ("raw_pixels", "standard_scaler"):
        for neighbors in (1, 3, 5, 7, 9):
            for weights in ("uniform", "distance"):
                candidates.append(
                    {
                        "model_family": "knn",
                        "preprocessing": preprocessing,
                        "hyperparameters": {"n_neighbors": neighbors, "weights": weights},
                    }
                )
    for max_depth in (None, 5, 10, 15):
        for min_samples_leaf in (1, 2, 5):
            candidates.append(
                {
                    "model_family": "decision_tree",
                    "preprocessing": "raw_pixels",
                    "hyperparameters": {"max_depth": max_depth, "min_samples_leaf": min_samples_leaf},
                }
            )
    return candidates


def resolve_path(path_text: str) -> Path:
    """从项目根目录解析相对路径，无需在其他位置处理命令行细节。"""
    path = Path(path_text)
    return path if path.is_absolute() else (TRAIN_PATH.parent.parent / path)


def main() -> None:
    arguments = parse_arguments()
    if arguments.cv_folds < 2:
        raise ValueError("--cv-folds 至少为 2。")

    ensure_output_directories()
    train_path = resolve_path(arguments.train_path)
    features, target, _ = load_split(train_path)
    cross_validator = StratifiedKFold(n_splits=arguments.cv_folds, shuffle=True, random_state=RANDOM_STATE)
    scoring = {"accuracy": "accuracy", "f1_macro": "f1_macro"}

    rows: list[dict[str, object]] = []
    candidates = create_candidates()
    for candidate in candidates:
        estimator = build_estimator(candidate)
        scores = cross_validate(
            estimator,
            features,
            target,
            cv=cross_validator,
            scoring=scoring,
            return_train_score=True,
            n_jobs=1,
            error_score="raise",
        )
        row: dict[str, object] = {
            "model_name": candidate_name(candidate),
            "model_family": candidate["model_family"],
            "preprocessing": candidate["preprocessing"],
            "hyperparameters": json.dumps(candidate["hyperparameters"], ensure_ascii=False),
        }
        for metric in scoring:
            train_scores = scores[f"train_{metric}"]
            validation_scores = scores[f"test_{metric}"]
            row[f"train_{metric}_mean"] = float(np.mean(train_scores))
            row[f"train_{metric}_std"] = float(np.std(train_scores, ddof=1))
            row[f"validation_{metric}_mean"] = float(np.mean(validation_scores))
            row[f"validation_{metric}_std"] = float(np.std(validation_scores, ddof=1))
        row["accuracy_generalization_gap"] = float(row["train_accuracy_mean"] - row["validation_accuracy_mean"])
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values(
        ["validation_accuracy_mean", "validation_f1_macro_mean", "accuracy_generalization_gap"],
        ascending=[False, False, True],
    )
    summary.to_csv(TABLES_DIR / "cross_validation_results.csv", index=False)
    selected_row = summary.iloc[0]
    selected_candidate = candidates[int(selected_row.name)]
    best_pipeline = build_estimator(selected_candidate)
    best_pipeline.fit(features, target)
    joblib.dump(best_pipeline, BEST_PIPELINE_PATH)

    report = {
        "data_used": "data/train_split.csv only; data/test_split.csv was not read or used.",
        "test_data_used_for_selection": False,
        "train_samples": int(len(features)),
        "cross_validation": {
            "method": "StratifiedKFold",
            "n_splits": arguments.cv_folds,
            "shuffle": True,
            "random_state": RANDOM_STATE,
        },
        "selection_rule": "highest mean validation accuracy; ties: macro F1, then smaller train-validation accuracy gap",
        "candidate_count": len(candidates),
        "candidate_groups": {
            "knn_raw_pixels": "n_neighbors in [1, 3, 5, 7, 9]; weights in ['uniform', 'distance']",
            "knn_standard_scaler": "n_neighbors in [1, 3, 5, 7, 9]; weights in ['uniform', 'distance']",
            "decision_tree_raw_pixels": "max_depth in [None, 5, 10, 15]; min_samples_leaf in [1, 2, 5]",
        },
        "selected_candidate": selected_candidate,
        "selected_model_name": selected_row["model_name"],
        "selected_cross_validation_metrics": {
            key: float(selected_row[key])
            for key in summary.columns
            if key.startswith(("train_", "validation_", "accuracy_generalization_gap"))
        },
        "saved_pipeline": str(BEST_PIPELINE_PATH.relative_to(TRAIN_PATH.parent.parent)),
    }
    write_json(report, MODEL_SELECTION_PATH)

    display_columns = [
        "model_name",
        "validation_accuracy_mean",
        "validation_accuracy_std",
        "validation_f1_macro_mean",
        "accuracy_generalization_gap",
    ]
    display = summary[display_columns].head(10).copy()
    for column in display.columns[1:]:
        display[column] = display[column].map(lambda value: f"{value:.3f}")
    print("训练集内部交叉验证完成（测试集未读取）\n")
    print(display.to_string(index=False))
    print(f"\n选定模型：{report['selected_model_name']}")
    print(f"交叉验证准确率：{report['selected_cross_validation_metrics']['validation_accuracy_mean']:.3f}")
    print(f"完整训练集拟合后的 Pipeline：{BEST_PIPELINE_PATH}")


if __name__ == "__main__":
    main()
