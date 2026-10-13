# 客户聚类输出说明

本文行数：43行，预期阅读时长：2分钟

这里说明分析流程使用或生成的文件。仓库收录小型图表与 JSON 指标；原始数据、预处理中间 CSV 和完整模型需要在运行时准备。候选比较脚本读取缩放后的 CSV，最终保存脚本还会用它核对预处理结果。

## 最终成果：优先阅读

| 文件 | 用途 |
| --- | --- |
| `tables/final_k2_customer_assignments.csv` | 440 位客户的原始字段、最终 C0/C1 归属和描述性簇名 |
| `tables/final_k2_cluster_profiles.csv` | 最终簇规模、Channel 事后构成和原始消费金额画像 |
| `tables/final_k2_metadata.json` | 数据、预处理、模型参数、评价指标、软件版本和标签映射 |
| `models/final_k2_model.joblib` | 可重新加载的 `log1p → 保留六位小数 → RobustScaler → K-Means(K=2)` 模型包 |

## 选择 K 的证据

| 文件 | 用途 |
| --- | --- |
| `tables/k_candidate_comparison.csv` | K=2～6 的 inertia、轮廓系数和簇规模 |
| `figures/k_candidate_diagnostics.png` | 肘部曲线与平均轮廓系数曲线 |
| `tables/k2_k3_cluster_profiles.csv` | K=2、K=3 的原始金额簇画像对比 |
| `figures/k2_k3_pca_comparison.png` | 同一 PCA 坐标下比较 K=2 与 K=3 |
| `figures/k2_k3_profile_heatmap.png` | K=2、K=3 的消费画像热力图 |
| `tables/k2_k3_channel_comparison.csv` | 两种 K 与 Channel 的事后对照 |
| `figures/k2_k3_channel_comparison.png` | Channel 簇内占比图 |

## 数据理解与预处理证据

| 文件 | 用途 |
| --- | --- |
| `tables/feature_summary.csv` | 六个原始消费字段的描述统计 |
| `tables/iqr_outlier_report.csv` | IQR 异常值诊断；本项目据此决定不截断客户 |
| `figures/feature_distributions.png` | 原始字段分布 |
| `tables/wholesale_customers_log1p.csv` | 保留全部客户的 log1p 中间结果 |
| `tables/wholesale_customers_log1p_robust_scaled.csv` | K-Means 实际使用的六个缩放特征 |
| `tables/robust_scaler_parameters.csv` | 每列 RobustScaler 的中位数和 IQR 参数 |
| `figures/preprocessing_distribution_comparison.png` | 原始、log1p、log1p+缩放的直方图对照 |
| `figures/preprocessing_boxplot_comparison.png` | 三阶段箱线图对照 |
| `tables/scaled_feature_correlation.csv` | 六个缩放特征的 Pearson 相关系数 |
| `figures/scaled_feature_correlation_heatmap.png` | 相关系数热力图 |

[本章入口](../README.md) · [实验结果](../results.md)
