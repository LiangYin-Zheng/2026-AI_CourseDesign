from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict

import pandas as pd

from src.core.contracts import get_training_mode_label, normalize_dashboard_summary
from src.utils.file_utils import write_text


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


# 生成区分度结论
def _build_key_findings(separation_scores: Dict[str, float], limit: int = 5) -> list[str]:
    findings: list[str] = []
    for index, (feature_name, score) in enumerate(list(separation_scores.items())[:limit], start=1):
        findings.append(f"{feature_name} 的类间区分度评分为 {score}，在当前样本中排名第 {index}。")
    return findings


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


DEFAULT_METRIC_KEYS = ('accuracy', 'macro_precision', 'macro_recall', 'macro_f1')


# 将空值格式化为短横线
def _format_cell(value: Any) -> str:
    if value is None:
        return '-'
    return str(value)


# 渲染 Markdown 表格
def render_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    if not headers:
        raise ValueError('表头不能为空。')
    header_line = '| ' + ' | '.join(headers) + ' |'
    separator_line = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
    body_lines = ['| ' + ' | '.join(_format_cell(cell) for cell in row) + ' |' for row in rows]
    return '\n'.join([header_line, separator_line, *body_lines])


# 渲染模型指标表
def render_metrics_table(result_group: Mapping[str, Any], metric_keys: Sequence[str] = DEFAULT_METRIC_KEYS, model_header: str = '模型') -> str:
    headers = [model_header, *metric_keys]
    rows = []
    for model_name, result in result_group.items():
        metrics = result['test_metrics']
        rows.append([model_name, *[metrics.get(metric_key, '-') for metric_key in metric_keys]])
    return render_markdown_table(headers, rows)


# 取优先用于解读的指标
def _primary_metric_key(metric_keys: Sequence[str]) -> str:
    return 'macro_f1' if 'macro_f1' in metric_keys else metric_keys[0]


# 安全转换为浮点数
def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# 计算指标变化
def _metric_delta(current: float, baseline: Any) -> float | None:
    baseline_value = _as_float(baseline)
    if baseline_value is None:
        return None
    return current - baseline_value


# 生成默认章节标题
def _default_section_title(section_name: str, family_name: str) -> str:
    if section_name == 'baseline':
        return f'{family_name}基线模型结果'
    if section_name == 'optimized':
        return f'{family_name}优化后模型结果'
    return f'{section_name}结果'


# 渲染模型训练报告
def render_model_report(
    model_results: Mapping[str, Mapping[str, Any]],
    family_name: str = '模型',
    report_title: str | None = None,
    section_titles: Mapping[str, str] | None = None,
    metric_keys: Sequence[str] = DEFAULT_METRIC_KEYS,
    conclusion_lines: Sequence[str] | None = None,
) -> str:
    report_title = report_title or f'{family_name}训练与评估报告'
    lines = [f'# {report_title}', '']

    ordered_sections = list(model_results.keys())
    for index, section_name in enumerate(ordered_sections, start=1):
        section_title = section_titles.get(section_name) if section_titles else None
        section_title = section_title or _default_section_title(section_name, family_name)
        lines.extend([
            f'## {index}. {section_title}',
            render_metrics_table(model_results[section_name], metric_keys=metric_keys),
            '',
        ])

    if conclusion_lines is None:
        primary_metric = _primary_metric_key(metric_keys)
        baseline_results = model_results.get('baseline', {})
        optimized_results = model_results.get('optimized', {})
        ranked_models = []
        for model_name, result in optimized_results.items():
            metric_value = _as_float(result['test_metrics'].get(primary_metric))
            if metric_value is not None:
                ranked_models.append((model_name, metric_value))
        ranked_models.sort(key=lambda item: item[1], reverse=True)
        best_model_name = ranked_models[0][0] if ranked_models else None
        best_metric_value = ranked_models[0][1] if ranked_models else None
        conclusion_lines = (
            '## 结果解读',
            '- 基线模型用于展示未经系统调参与优化时的效果。',
            *(
                [
                    f"- 当前优化后表现最好的模型是 {best_model_name}，测试集 {primary_metric}={best_metric_value:.4f}。"
                ]
                if best_model_name is not None and best_metric_value is not None
                else ['- 当前没有可用于解读的优化结果。']
            ),
            *(
                [
                    f"- 相比基线，{best_model_name} 的 {primary_metric} 变化为 {_metric_delta(best_metric_value, baseline_results.get(best_model_name, {}).get('test_metrics', {}).get(primary_metric)):+.4f}。"
                ]
                if best_model_name is not None and best_metric_value is not None and _metric_delta(best_metric_value, baseline_results.get(best_model_name, {}).get('test_metrics', {}).get(primary_metric)) is not None
                else []
            ),
            f"- 汇报时建议同时说明 Accuracy、Macro Precision、Macro Recall 与 {primary_metric.replace('_', ' ').title()}，便于解释差异来源。",
        )
    lines.extend(conclusion_lines)
    return '\n'.join(lines)


# 渲染家族对比报告
def render_family_comparison_report(
    summary: Mapping[str, Any],
    title: str = '模型对比报告',
    metric_keys: Sequence[str] = DEFAULT_METRIC_KEYS,
) -> str:
    normalized = normalize_dashboard_summary(dict(summary), {'project_name': summary.get('project_name', '未知项目')})
    rows = normalized['comparison_rows']
    overview = normalized['overview']
    headers = ['家族', '模型', *[key.replace('_', ' ').title() for key in metric_keys]]
    table_rows = [
        [
            row['family'],
            row['name'],
            *[row['metrics'].get(metric_key, '-') for metric_key in metric_keys],
        ]
        for row in rows
    ]
    primary_metric = _primary_metric_key(metric_keys)
    ranked_rows = [
        (row['family'], row['name'], _as_float(row['metrics'].get(primary_metric)))
        for row in rows
        if _as_float(row['metrics'].get(primary_metric)) is not None
    ]
    ranked_rows.sort(key=lambda item: item[2], reverse=True)
    best_row = ranked_rows[0] if ranked_rows else None
    runner_up = ranked_rows[1] if len(ranked_rows) > 1 else None
    metric_label = primary_metric.replace('_', ' ').title()
    lines = [
        f'# {title}',
        '',
        '## 1. 总览',
        f"- 项目名称：{overview['project_name']}",
        f"- 训练路线：{get_training_mode_label(overview['training_mode'])}",
        f"- 数据集样本量：{overview['sample_count']}",
        f"- 标签类别数：{overview['class_count']}",
        f"- 推荐部署模型：{overview['recommended_model']['family']} / {overview['recommended_model']['name']}",
        f"- 最优 Macro F1：{overview['best_macro_f1']}",
        '',
        '## 2. 核心模型横向对比',
        render_markdown_table(headers, table_rows),
        '',
        '## 3. 建议',
        *(
            [
                f"- 当前最优模型是 {best_row[0]} / {best_row[1]}，{metric_label}={best_row[2]:.4f}。"
            ]
            if best_row
            else ['- 当前没有足够的模型对比结果。']
        ),
        *(
            [
                f"- 与第二名相比，领先幅度为 {best_row[2] - runner_up[2]:.4f}，展示时应说明这个差距是否具有实际意义。"
            ]
            if best_row and runner_up
            else []
        ),
        *(
            [
                '- 当前结果更适合优先展示 sklearn 路线的标准化训练与调参流程。'
                if best_row and best_row[0] == 'sklearn'
                else '- 当前结果更适合优先展示手搓路线的实现细节与原理说明。'
            ]
            if best_row
            else []
        ),
        '- 桌面 GUI 与命令行预测分离后，答辩时可分别展示“本地应用模式”和“脚本预测模式”。',
    ]
    return '\n'.join(lines)


# 保存模型报告到文件
def save_model_report(output_path: str, model_results: Mapping[str, Mapping[str, Any]], family_name: str = '模型') -> None:
    write_text(output_path, render_model_report(model_results, family_name=family_name))
