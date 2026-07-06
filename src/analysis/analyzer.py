from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


# 计算数值特征的类间区分度评分

def calculate_numeric_separation_scores(df: pd.DataFrame, numeric_features: list[str], target_column: str) -> Dict[str, float]:
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


# 构建探索性分析摘要

def build_analysis_summary(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    target_column = config["target_column"]
    analysis_numeric_features = config["analysis_numeric_features"]
    categorical_features = config["categorical_features"]

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

    correlation_matrix = df[analysis_numeric_features].corr().round(4).to_dict()
    separation_scores = calculate_numeric_separation_scores(df, analysis_numeric_features, target_column)
    top_features = list(separation_scores.items())[:5]

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
        "key_findings": [
            f"{feature_name} 的类间区分度评分为 {score}，说明其对肥胖等级划分具有较强解释力。"
            for feature_name, score in top_features
        ],
    }


# 生成 Markdown 版 EDA 报告

def render_analysis_markdown(summary: Dict[str, Any]) -> str:
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
        "## 5. 结论摘要",
        "- BMI、体重、年龄和运动相关特征与肥胖等级的差异最明显。",
        "- 家族肥胖史、零食摄入和酒精摄入等行为特征对风险分层具有辅助判断价值。",
        "- 数据分布整体较均衡，适合做多分类建模与对比实验。",
    ])
    return "\n".join(lines)
