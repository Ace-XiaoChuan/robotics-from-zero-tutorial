# Week 5 输出资产索引

本文行数：43行，预期阅读时长：2分钟

本目录只保留 Wholesale Customers 正式学习流程产生的成果与必要过程证据。早期通用演示流程生成的旧模型和重复结果已清理；通用脚本仍保留在 `../src/`，需要时可以重新运行。

## 最终成果：优先阅读

| 文件 | 用途 |
| --- | --- |
| `tables/final_k2_customer_assignments.csv` | 440 位客户的原始字段、最终 C0/C1 归属和描述性簇名 |
| `tables/final_k2_cluster_profiles.csv` | 最终簇规模、Channel 事后构成和原始消费金额画像 |
| `tables/final_k2_metadata.json` | 数据、预处理、模型参数、评价指标、软件版本和标签映射 |
| `models/final_k2_model.joblib` | 可重新加载的 `log1p → RobustScaler → K-Means(K=2)` 模型包 |

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

`.gitkeep` 仅用于保证空目录结构可被 Git 保存，不是分析结果。
