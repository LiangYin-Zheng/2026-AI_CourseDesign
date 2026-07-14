# 探索性数据分析报告

## 数据与目标概况

- 分析样本数：20758。
- 目标类别数：7。
- 年龄、身高、体重及其余数值字段均保留原始量纲用于描述；模型阶段单独标准化。

## 单变量分析

数值直方图展示 Age、Height、Weight、FCVC、NCP、CH2O、FAF、TUE 的集中趋势与偏态；类别频数图展示所有配置确认的类别字段。审查阶段标记的 IQR 极端值未被自动删除，因为它们仍位于配置的合理范围内。

## 双变量分析

按肥胖等级比较 Age、Height、Weight 的组均值跨度时，`Weight` 的跨度最大（67.836679），说明其对类别分离具有较强描述价值。箱线图同时显示类内离散程度，不能仅依据单一特征作医学判断。

## 多变量与相关性

绝对 Pearson 相关性最高的数值特征对为 `Height` 与 `Weight`（r=0.4167）。热力图只描述线性相关，不代表因果关系。Height-Weight-Age 联合图显示类别在多特征空间中存在重叠，因此需要多分类模型综合判断。

## 类别特征与目标

报告 JSON 保存了每个类别特征在各目标类别中的列归一化交叉比例，可用于后续报告讨论饮食、活动和出行字段与目标之间的关联；字段缩写和编码含义仍以课程数据说明为准。

## 图表清单

- `figures/numeric_distributions.png`
- `figures/categorical_frequencies.png`
- `figures/target_distribution.png`
- `figures/key_features_by_target.png`
- `figures/correlation_heatmap.png`
- `figures/age_height_weight_relationship.png`

> 本分析用于课程项目，相关性与模型预测均不构成医学诊断或健康建议。
