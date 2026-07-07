from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


# 计算数值特征的类间区分度评分
def calculate_numeric_separation_scores(df: pd.DataFrame, numeric_features: list[str], target_column: str) -> Dict[str, float]:
    # 按特征逐个统计区分度
    scores: Dict[str, float] = {}
    for feature_name in numeric_features:
        overall_mean = float(df[feature_name].mean())
        total_variance = float(df[feature_name].var(ddof=0))
        if total_variance <= 1e-8:
            scores[feature_name] = 0.0
            continue
        between_group_variance = 0.0
        for _, group_df in df.groupby(target_column):
            weight = len(group_df) / len(df)
            group_mean = float(group_df[feature_name].mean())
            between_group_variance += weight * ((group_mean - overall_mean) ** 2)
        scores[feature_name] = round(between_group_variance / total_variance, 6)
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


# 生成区分度结论
def _build_key_findings(separation_scores: Dict[str, float], limit: int = 5) -> list[str]:
    findings: list[str] = []
    for index, (feature_name, score) in enumerate(list(separation_scores.items())[:limit], start=1):
        findings.append(f"{feature_name} 的类间区分度评分为 {score}，在当前样本中排名第 {index}。")
    return findings


# 构建探索性分析摘要
def build_analysis_summary(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    # 读取分析相关配置
    target_column = config["target_column"]
    analysis_numeric_features = config["analysis_numeric_features"]
    categorical_features = config["categorical_features"]

    # 汇总数值和类别特征信息
    numeric_summary = df[analysis_numeric_features].describe().round(4).to_dict()
    target_distribution = df[target_column].value_counts().to_dict()
    target_ratio = (df[target_column].value_counts(normalize=True) * 100).round(2).to_dict()
    group_means = df.groupby(target_column)[analysis_numeric_features].mean().round(4).to_dict()
    categorical_profiles: Dict[str, Any] = {}
    for feature_name in categorical_features:
        categorical_profiles[feature_name] = (
            pd.crosstab(df[feature_name], df[target_column], normalize="columns")
            .round(4)
            .to_dict()
        )

    # 计算相关性和区分度
    correlation_matrix = df[analysis_numeric_features].corr().round(4).to_dict()
    separation_scores = calculate_numeric_separation_scores(df, analysis_numeric_features, target_column)

    return {
        "overview": {
            "sample_count": int(len(df)),
            "feature_count": int(df.shape[1] - 1),
            "class_count": int(df[target_column].nunique()),
        },
        "target_distribution": target_distribution,
        "target_ratio_percent": target_ratio,
        "numeric_summary": numeric_summary,
        "group_means": group_means,
        "categorical_profiles": categorical_profiles,
        "correlation_matrix": correlation_matrix,
        "numeric_separation_scores": separation_scores,
        "key_findings": _build_key_findings(separation_scores),
    }


# 生成结论摘要
def _build_conclusion_lines(summary: Dict[str, Any]) -> list[str]:
    lines = ["## 5. 结论摘要"]

    separation_scores = list(summary.get("numeric_separation_scores", {}).items())
    if separation_scores:
        top_features = [feature_name for feature_name, _ in separation_scores[:3]]
        joined_features = "、".join(top_features)
        lines.append(f"- 当前区分度排名靠前的特征是 {joined_features}，后续建模应优先关注这些变量。")

    target_ratios = summary.get("target_ratio_percent", {})
    if target_ratios:
        ratios = [float(value) for value in target_ratios.values()]
        min_ratio = min(ratios)
        max_ratio = max(ratios)
        if max_ratio - min_ratio <= 10:
            balance_text = "整体较均衡"
        else:
            balance_text = "存在一定偏斜"
        lines.append(f"- 标签分布{balance_text}，占比范围为 {min_ratio:.2f}% 到 {max_ratio:.2f}%。")

    lines.append("- 以上结论均基于当前样本统计结果，数据或训练结果变化时会自动同步更新。")
    return lines


# 生成 Markdown 版 EDA 报告
def render_analysis_markdown(summary: Dict[str, Any]) -> str:
    # 逐段拼接报告内容
    lines = [
        "# 肥胖风险数据探索分析报告",
        "",
        "## 1. 数据概览",
        f"- 样本量：{summary['overview']['sample_count']}",
        f"- 特征数：{summary['overview']['feature_count']}",
        f"- 标签类别数：{summary['overview']['class_count']}",
        "",
        "## 2. 标签分布",
    ]
    for class_name, count in summary["target_distribution"].items():
        ratio = summary["target_ratio_percent"][class_name]
        lines.append(f"- {class_name}：{count} 条，占比 {ratio}%")

    lines.extend([
        "",
        "## 3. 关键影响因素",
    ])
    for finding in summary["key_findings"]:
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "## 4. 数值特征区分度排名",
        "| 特征 | 区分度评分 |",
        "| --- | --- |",
    ])
    for feature_name, score in summary["numeric_separation_scores"].items():
        lines.append(f"| {feature_name} | {score} |")

    lines.extend([
        "",
        *_build_conclusion_lines(summary),
    ])
    return "\n".join(lines)
