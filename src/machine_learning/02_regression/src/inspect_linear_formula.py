"""导出已训练线性回归 Pipeline 的公式说明和完整系数表。"""

import argparse
from pathlib import Path

import joblib
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_DIR / "outputs" / "linear_regression_pipeline.joblib"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the fitted linear regression formula.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH, help="已拟合 Pipeline 路径。")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="系数表与公式说明输出目录。")
    parser.add_argument("--top-n", type=int, default=15, help="公式说明中展示的最大正/负系数数量。")
    return parser.parse_args()


def format_term(feature_name: str, coefficient: float) -> str:
    sign = "+" if coefficient >= 0 else "-"
    return f" {sign} {abs(coefficient):,.2f} × {feature_name}"


def main() -> None:
    arguments = parse_arguments()
    if arguments.top_n < 1:
        raise ValueError("--top-n 必须至少为 1。")
    if not arguments.model_path.is_file():
        raise FileNotFoundError(f"未找到已训练模型：{arguments.model_path}")

    pipeline = joblib.load(arguments.model_path)
    preprocessor = pipeline.named_steps["preprocessor"]
    linear_model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out().tolist()
    coefficients = linear_model.coef_.ravel()
    if len(feature_names) != len(coefficients):
        raise ValueError("特征名称数量与系数数量不一致。")

    numeric_columns = set(preprocessor.transformers_[0][2])
    coefficient_table = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "feature_type": ["numeric_standardized" if name in numeric_columns else "one_hot_category" for name in feature_names],
        }
    )
    coefficient_table["absolute_coefficient"] = coefficient_table["coefficient"].abs()
    coefficient_table = coefficient_table.sort_values("absolute_coefficient", ascending=False)

    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    coefficient_path = arguments.output_dir / "linear_regression_coefficients.csv"
    formula_path = arguments.output_dir / "linear_regression_formula.md"
    coefficient_table.to_csv(coefficient_path, index=False)

    largest_positive = coefficient_table.sort_values("coefficient", ascending=False).head(arguments.top_n)
    largest_negative = coefficient_table.sort_values("coefficient", ascending=True).head(arguments.top_n)
    intercept = float(linear_model.intercept_)

    with formula_path.open("w", encoding="utf-8") as file:
        file.write("# 线性回归拟合公式\n\n")
        file.write("本模型在预处理后的 341 个特征上拟合。完整系数请查看 "
                   "[`linear_regression_coefficients.csv`](linear_regression_coefficients.csv)。\n\n")
        file.write("## 精确形式\n\n")
        file.write("```text\n")
        file.write(f"预测房价 ŷ = {intercept:,.2f}")
        file.write(" + Σ(系数ᵢ × 预处理后特征ᵢ)\n")
        file.write("```\n\n")
        file.write("这里的求和包含系数表中的全部 341 项。数值特征已经过中位数填补和标准化；"
                   "类别特征已经变成 0/1 指示列。因此，该式中的数值变量不是原始单位，"
                   "而是标准化后的数值。\n\n")
        file.write("## 最大正系数（前 %d 个）\n\n" % arguments.top_n)
        file.write("```text\n")
        for row in largest_positive.itertuples(index=False):
            file.write(format_term(row.feature, row.coefficient) + "\n")
        file.write("```\n\n")
        file.write("## 最大负系数（前 %d 个）\n\n" % arguments.top_n)
        file.write("```text\n")
        for row in largest_negative.itertuples(index=False):
            file.write(format_term(row.feature, row.coefficient) + "\n")
        file.write("```\n\n")
        file.write("## 阅读注意事项\n\n")
        file.write("- 系数为正表示在其他预处理后特征保持不变时，该项增大通常会推高预测房价；"
                   "负系数则相反。\n")
        file.write("- 数值特征经过标准化，系数对应“该特征增加一个训练集标准差”的影响，"
                   "不能直接理解为原始单位增加 1。\n")
        file.write("- 类别特征采用完整独热编码且模型包含截距，类别系数之间存在冗余；"
                   "模型预测有效，但不应孤立地把某个类别系数当作严格的因果解释。\n")

    print("线性回归公式已导出")
    print(f"截距：{intercept:,.2f}")
    print(f"预处理后特征数：{len(feature_names)}")
    print(f"完整系数表：{coefficient_path}")
    print(f"公式说明：{formula_path}")
    print("\n最大正系数：")
    print(largest_positive[["feature", "coefficient"]].to_string(index=False, formatters={"coefficient": "{:+,.2f}".format}))
    print("\n最大负系数：")
    print(largest_negative[["feature", "coefficient"]].to_string(index=False, formatters={"coefficient": "{:+,.2f}".format}))


if __name__ == "__main__":
    main()
