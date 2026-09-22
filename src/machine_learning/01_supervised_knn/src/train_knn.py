"""使用 KNN 完成鸢尾花分类，并输出模型评估结果。"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 允许在终端或无图形界面的环境中保存图表

import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a KNN classifier on the Iris dataset.")
    parser.add_argument("--test-size", type=float, default=0.2, help="测试集比例，默认 0.2。")
    parser.add_argument("--random-state", type=int, default=42, help="随机种子，默认 42。")
    parser.add_argument(
        "--k-values",
        default="1,3,5,7,9,11,13,15",
        help="交叉验证时尝试的 K 值，用逗号分隔。",
    )
    return parser.parse_args()


def parse_k_values(value: str) -> list[int]:
    k_values = [int(item.strip()) for item in value.split(",")]
    if not k_values or any(k < 1 for k in k_values):
        raise ValueError("K 值必须是正整数。")
    return k_values


def save_k_selection_plot(search: GridSearchCV, k_values: list[int]) -> None:
    """保存训练集交叉验证中不同 K 值的准确率。"""
    mean_scores = search.cv_results_["mean_test_score"]
    std_scores = search.cv_results_["std_test_score"]

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.errorbar(k_values, mean_scores, yerr=std_scores, marker="o", capsize=4)
    axis.set_title("K Selection with Cross-Validation")
    axis.set_xlabel("Number of neighbors (K)")
    axis.set_ylabel("Mean validation accuracy")
    axis.set_xticks(k_values)
    axis.set_ylim(0.7, 1.02)
    axis.grid(alpha=0.3)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "knn_k_selection.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_confusion_matrix(model: Pipeline, x_test, y_test, target_names) -> None:
    """保存最终测试集的混淆矩阵。"""
    figure, axis = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay.from_estimator(
        model,
        x_test,
        y_test,
        display_labels=target_names,
        cmap="Blues",
        colorbar=False,
        ax=axis,
    )
    axis.set_title("KNN Confusion Matrix (Test Set)")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "knn_confusion_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    k_values = parse_k_values(arguments.k_values)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # load_iris() 读取 scikit-learn 内置数据；X 是四个测量特征，y 是已知品种编号。
    iris = load_iris()

    # train_test_split() 将 X 和 y 用相同索引一起划分，保证“花的特征”和“品种标签”不脱节。
    # stratify=iris.target 让训练集、测试集尽量保持三个品种原有的相同比例。
    # random_state 固定后，每次运行都会得到相同的划分结果。
    x_train, x_test, y_train, y_test = train_test_split(
        iris.data,
        iris.target,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        stratify=iris.target,
    )

    # StandardScaler：用训练数据的均值和标准差标准化每个特征，避免量纲影响 KNN 的距离计算。
    # Pipeline（管道）：将“预处理 → 模型”按顺序绑成一个可复用流程。
    # 调用 fit() 时，它先拟合并转换 StandardScaler，再训练 KNN；调用 predict() 时，它会自动用
    # 同一套标准化规则转换新数据，再交给 KNN 预测，避免手动处理时遗漏步骤或前后规则不一致。
    # 在每一折中，标准化规则只从该折训练数据学习，从而防止验证数据或测试集的信息泄漏到模型中。
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            # KNeighborsClassifier：预测时寻找距离最近的 k 个训练样本，并按它们的类别投票。
            ("knn", KNeighborsClassifier()),
        ]
    )

    # StratifiedKFold：把训练集分为 5 折，并让每一折尽量保持三个品种的类别比例。
    # 每轮用 4 折训练、1 折验证；shuffle 和 random_state 使分折过程可复现。
    cross_validation = StratifiedKFold(n_splits=5, shuffle=True, random_state=arguments.random_state)

    # GridSearchCV：针对每个候选 k 执行上述 5 折交叉验证，比较平均 accuracy。
    # "knn__n_neighbors" 表示修改 Pipeline 中名为 "knn" 的步骤的 n_neighbors 参数。
    # n_jobs=-1 表示尽可能使用所有可用 CPU 核心并行执行这些临时训练。
    search = GridSearchCV(
        estimator=pipeline,
        param_grid={"knn__n_neighbors": k_values},
        scoring="accuracy",
        cv=cross_validation,
        n_jobs=-1,
    )

    # fit() 会完成所有候选 k 的交叉验证，并自动以最佳 k 在全部训练集上重新拟合 best_estimator_。
    search.fit(x_train, y_train)

    # predict() 对从未参与选型的测试集做预测；accuracy_score() 计算预测正确的比例。
    best_model = search.best_estimator_
    test_predictions = best_model.predict(x_test)
    test_accuracy = accuracy_score(y_test, test_predictions)

    save_k_selection_plot(search, k_values)
    save_confusion_matrix(best_model, x_test, y_test, iris.target_names)

    results = {
        "random_state": arguments.random_state,
        "train_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "candidate_k_values": k_values,
        "best_k": int(search.best_params_["knn__n_neighbors"]),
        "best_cross_validation_accuracy": float(search.best_score_),
        "test_accuracy": float(test_accuracy),
    }
    with (OUTPUT_DIR / "knn_results.json").open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("KNN 鸢尾花分类完成")
    print(f"训练集样本数：{len(x_train)}；测试集样本数：{len(x_test)}")
    print(f"交叉验证选出的最佳 K：{results['best_k']}")
    print(f"交叉验证平均准确率：{results['best_cross_validation_accuracy']:.3f}")
    print(f"最终测试集准确率：{results['test_accuracy']:.3f}")
    print("\n测试集分类报告：")
    print(classification_report(y_test, test_predictions, target_names=iris.target_names, digits=3))
    print(f"结果文件已保存到：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
