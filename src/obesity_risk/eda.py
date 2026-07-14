from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from obesity_risk.io_utils import write_json, write_text
from obesity_risk.schema import DatasetSchema


# 保存图形并及时释放 Matplotlib 资源
def _save_figure(figure: plt.Figure, path: Path, dpi: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return path


# 绘制所有数值特征的单变量直方图
def _plot_numeric_distributions(
    frame: pd.DataFrame, numeric_columns: list[str], path: Path, dpi: int
) -> Path:
    columns = 3
    rows = int(np.ceil(len(numeric_columns) / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(15, 4 * rows))
    for axis, column in zip(np.asarray(axes).reshape(-1), numeric_columns):
        axis.hist(frame[column].dropna(), bins=30, color="#4C78A8", alpha=0.85)
        axis.set(title=f"Distribution of {column}", xlabel=column, ylabel="Count")
        axis.grid(alpha=0.2)
    for axis in np.asarray(axes).reshape(-1)[len(numeric_columns) :]:
        axis.axis("off")
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 绘制类别特征频数
def _plot_categorical_frequencies(
    frame: pd.DataFrame, categorical_columns: list[str], path: Path, dpi: int
) -> Path:
    figure, axes = plt.subplots(4, 2, figsize=(15, 18))
    for axis, column in zip(np.asarray(axes).reshape(-1), categorical_columns):
        counts = frame[column].astype(str).value_counts()
        axis.bar(counts.index, counts.values, color="#72B7B2")
        axis.set(title=f"Frequency of {column}", ylabel="Count")
        axis.tick_params(axis="x", rotation=30)
        axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 绘制目标类别分布
def _plot_target_distribution(frame: pd.DataFrame, target: str, path: Path, dpi: int) -> Path:
    counts = frame[target].value_counts().sort_index()
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(counts.index, counts.values, color="#F58518")
    axis.set(title="Obesity Level Distribution", xlabel="Class", ylabel="Count")
    axis.tick_params(axis="x", rotation=30)
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 绘制年龄、身高、体重按目标分组的箱线图
def _plot_key_feature_boxplots(
    frame: pd.DataFrame, target: str, path: Path, dpi: int
) -> Path:
    classes = sorted(frame[target].unique())
    figure, axes = plt.subplots(3, 1, figsize=(14, 15))
    for axis, column in zip(axes, ("Age", "Height", "Weight")):
        grouped = [frame.loc[frame[target] == class_name, column].dropna() for class_name in classes]
        axis.boxplot(grouped, tick_labels=classes, showfliers=False)
        axis.set(title=f"{column} by Obesity Level", xlabel="Class", ylabel=column)
        axis.tick_params(axis="x", rotation=25)
        axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 绘制数值特征相关性热力图
def _plot_correlation_heatmap(
    correlations: pd.DataFrame, path: Path, dpi: int
) -> Path:
    figure, axis = plt.subplots(figsize=(10, 8))
    image = axis.imshow(correlations.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1)
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    axis.set(
        xticks=np.arange(len(correlations.columns)),
        yticks=np.arange(len(correlations.index)),
        xticklabels=correlations.columns,
        yticklabels=correlations.index,
        title="Numeric Feature Correlation Heatmap",
    )
    plt.setp(axis.get_xticklabels(), rotation=35, ha="right")
    for row in range(len(correlations.index)):
        for column in range(len(correlations.columns)):
            axis.text(
                column,
                row,
                f"{correlations.iat[row, column]:.2f}",
                ha="center",
                va="center",
                fontsize=7,
            )
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 绘制年龄、身高和体重的抽样联合关系
def _plot_multivariable_scatter(
    frame: pd.DataFrame, target: str, sample_size: int, seed: int, path: Path, dpi: int
) -> Path:
    sample = frame.sample(min(sample_size, len(frame)), random_state=seed)
    classes = sorted(sample[target].unique())
    color_map = plt.get_cmap("tab10")
    figure, axis = plt.subplots(figsize=(10, 7))
    for index, class_name in enumerate(classes):
        group = sample[sample[target] == class_name]
        sizes = 15 + 1.8 * (group["Age"] - group["Age"].min()).fillna(0)
        axis.scatter(
            group["Height"],
            group["Weight"],
            s=sizes,
            alpha=0.45,
            color=color_map(index),
            label=class_name,
        )
    axis.set(
        title="Height-Weight Relationship (marker size represents Age)",
        xlabel="Height",
        ylabel="Weight",
    )
    axis.legend(fontsize=8, loc="best")
    axis.grid(alpha=0.2)
    figure.tight_layout()
    return _save_figure(figure, path, dpi)


# 生成 EDA 结构化摘要
def build_eda_summary(frame: pd.DataFrame, schema: DatasetSchema) -> dict:
    # 汇总单变量、双变量和多变量分析所需统计量。
    numeric_columns = list(schema.numeric_columns)
    target = schema.target_column
    numeric_description = frame[numeric_columns].describe().round(6).to_dict()
    correlations = frame[numeric_columns].corr().round(6)
    grouped_means = frame.groupby(target, observed=True)[numeric_columns].mean().round(6)
    grouped_medians = frame.groupby(target, observed=True)[numeric_columns].median().round(6)
    target_counts = frame[target].value_counts().sort_index()
    categorical_target = {}
    for column in schema.categorical_columns:
        table = pd.crosstab(frame[column], frame[target], normalize="columns").round(6)
        categorical_target[column] = table.to_dict()
    key_ranges = {
        column: float(grouped_means[column].max() - grouped_means[column].min())
        for column in ("Age", "Height", "Weight")
    }
    return {
        "row_count": len(frame),
        "numeric_description": numeric_description,
        "target_distribution": {
            str(name): {"count": int(count), "ratio": float(count / len(frame))}
            for name, count in target_counts.items()
        },
        "grouped_numeric_means": grouped_means.to_dict(orient="index"),
        "grouped_numeric_medians": grouped_medians.to_dict(orient="index"),
        "numeric_correlations": correlations.to_dict(),
        "categorical_target_column_ratios": categorical_target,
        "key_group_mean_ranges": key_ranges,
    }


# 根据真实统计量生成 EDA 文字分析
def _eda_markdown(summary: dict, figure_names: list[str]) -> str:
    correlations = pd.DataFrame(summary["numeric_correlations"])
    pairs = correlations.where(np.triu(np.ones(correlations.shape), k=1).astype(bool)).stack()
    strongest_pair = pairs.abs().idxmax()
    strongest_value = float(correlations.loc[strongest_pair[0], strongest_pair[1]])
    ranges = summary["key_group_mean_ranges"]
    largest_key_feature = max(ranges, key=ranges.get)
    lines = [
        "# 探索性数据分析报告",
        "",
        "## 数据与目标概况",
        "",
        f"- 分析样本数：{summary['row_count']}。",
        f"- 目标类别数：{len(summary['target_distribution'])}。",
        "- 年龄、身高、体重及其余数值字段均保留原始量纲用于描述；模型阶段单独标准化。",
        "",
        "## 单变量分析",
        "",
        "数值直方图展示 Age、Height、Weight、FCVC、NCP、CH2O、FAF、TUE 的集中趋势与偏态；类别频数图展示所有配置确认的类别字段。审查阶段标记的 IQR 极端值未被自动删除，因为它们仍位于配置的合理范围内。",
        "",
        "## 双变量分析",
        "",
        f"按肥胖等级比较 Age、Height、Weight 的组均值跨度时，`{largest_key_feature}` 的跨度最大（{ranges[largest_key_feature]:.6f}），说明其对类别分离具有较强描述价值。箱线图同时显示类内离散程度，不能仅依据单一特征作医学判断。",
        "",
        "## 多变量与相关性",
        "",
        f"绝对 Pearson 相关性最高的数值特征对为 `{strongest_pair[0]}` 与 `{strongest_pair[1]}`（r={strongest_value:.4f}）。热力图只描述线性相关，不代表因果关系。Height-Weight-Age 联合图显示类别在多特征空间中存在重叠，因此需要多分类模型综合判断。",
        "",
        "## 类别特征与目标",
        "",
        "报告 JSON 保存了每个类别特征在各目标类别中的列归一化交叉比例，可用于后续报告讨论饮食、活动和出行字段与目标之间的关联；字段缩写和编码含义仍以课程数据说明为准。",
        "",
        "## 图表清单",
        "",
    ]
    lines.extend(f"- `figures/{name}`" for name in figure_names)
    lines.extend(
        [
            "",
            "> 本分析用于课程项目，相关性与模型预测均不构成医学诊断或健康建议。",
            "",
        ]
    )
    return "\n".join(lines)


# 运行完整 EDA 并保存图片、JSON 和 Markdown
def run_eda(
    frame: pd.DataFrame,
    schema: DatasetSchema,
    figures_dir: Path,
    eda_dir: Path,
    eda_config: dict,
    random_seed: int,
) -> dict[str, Path]:
    # 生成课程要求的单变量、双变量和多变量 EDA 产物。
    dpi = int(eda_config["dpi"])
    figure_paths = [
        _plot_numeric_distributions(
            frame, list(schema.numeric_columns), figures_dir / "numeric_distributions.png", dpi
        ),
        _plot_categorical_frequencies(
            frame, list(schema.categorical_columns), figures_dir / "categorical_frequencies.png", dpi
        ),
        _plot_target_distribution(
            frame, schema.target_column, figures_dir / "target_distribution.png", dpi
        ),
        _plot_key_feature_boxplots(
            frame, schema.target_column, figures_dir / "key_features_by_target.png", dpi
        ),
        _plot_correlation_heatmap(
            frame[list(schema.numeric_columns)].corr(),
            figures_dir / "correlation_heatmap.png",
            dpi,
        ),
        _plot_multivariable_scatter(
            frame,
            schema.target_column,
            int(eda_config["scatter_sample_size"]),
            random_seed,
            figures_dir / "age_height_weight_relationship.png",
            dpi,
        ),
    ]
    summary = build_eda_summary(frame, schema)
    names = [path.name for path in figure_paths]
    return {
        "summary": write_json(eda_dir / "eda_summary.json", summary),
        "report": write_text(eda_dir / "eda_report.md", _eda_markdown(summary, names)),
        **{f"figure_{index + 1}": path for index, path in enumerate(figure_paths)},
    }
