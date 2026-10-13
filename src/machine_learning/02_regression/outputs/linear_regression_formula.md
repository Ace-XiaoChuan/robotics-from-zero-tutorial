# 线性回归拟合公式

本文行数：49行，预期阅读时长：2分钟

本模型在预处理后的 341 个特征上拟合。完整系数请查看 `linear_regression_coefficients.csv`（`linear_regression_coefficients.csv`）。

## 精确形式

```text
预测房价 ŷ = -16,243.36 + Σ(系数ᵢ × 预处理后特征ᵢ)
```

这里的求和包含系数表中的全部 341 项。数值特征已经过中位数填补和标准化；类别特征已经变成 0/1 指示列。因此，该式中的数值变量不是原始单位，而是标准化后的数值。

## 最大正系数（前 10 个）

```text
 + 177,629.79 × BsmtFin SF 1
 + 161,825.07 × Bsmt Unf SF
 + 131,024.82 × Roof Matl_Membran
 + 124,166.99 × Misc Feature_Othr
 + 116,209.59 × Roof Matl_WdShngl
 + 112,474.15 × Roof Matl_Metal
 + 105,916.74 × Misc Feature_Missing
 + 105,878.14 × Misc Feature_Shed
 + 104,765.26 × Misc Feature_Gar2
 + 98,314.62 × Neighborhood_GrnHill
```

## 最大负系数（前 10 个）

```text
 - 624,108.11 × Roof Matl_ClyTile
 - 440,727.12 × Misc Feature_Elev
 - 152,404.98 × Total Bsmt SF
 - 70,455.55 × Functional_Sal
 - 59,716.53 × Mas Vnr Type_CBlock
 - 48,620.37 × Garage Cond_Ex
 - 47,695.85 × MS SubClass_150
 - 40,992.93 × Pool QC_Missing
 - 30,915.33 × Condition 2_RRAe
 - 27,210.49 × Exterior 2nd_Stone
```

## 阅读注意事项

- 系数为正表示在其他预处理后特征保持不变时，该项增大通常会推高预测房价；负系数则相反。
- 数值特征经过标准化，系数对应“该特征增加一个训练集标准差”的影响，不能直接理解为原始单位增加 1。
- 类别特征采用完整独热编码且模型包含截距，类别系数之间存在冗余；模型预测有效，但不应孤立地把某个类别系数当作严格的因果解释。
