from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.interfaces.shared.dashboard_schema import get_training_mode_label, normalize_dashboard_summary
from src.utils.file_utils import write_text


DEFAULT_METRIC_KEYS = ('accuracy', 'macro_precision', 'macro_recall', 'macro_f1')
DEFAULT_RESULT_SECTIONS = ('baseline', 'optimized')


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
    # 生成表头和每行指标
    headers = [model_header, *metric_keys]
    rows = []
    for model_name, result in result_group.items():
        metrics = result['test_metrics']
        rows.append([model_name, *[metrics.get(metric_key, '-') for metric_key in metric_keys]])
    return render_markdown_table(headers, rows)


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
        conclusion_lines = (
            '## 结果解读',
            '- 基线模型用于展示未经系统调参与优化时的效果。',
            '- 优化模型优先比较测试集 Macro F1，用于反映多分类整体均衡能力。',
            '- 汇报时建议同时说明准确率、Macro F1 与模型参数配置。',
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
        '- 工程化路线更适合展示标准化训练、参数搜索和可重复实验流程。',
        '- 手写实现更适合展示算法原理、梯度下降过程和课程设计实现能力。',
        '- 桌面 GUI 与 Web GUI 分离后，答辩时可分别展示“本地应用模式”和“网页演示模式”。',
    ]
    return '\n'.join(lines)


# 保存模型报告到文件
def save_model_report(output_path: str, model_results: Mapping[str, Mapping[str, Any]], family_name: str = '模型') -> None:
    write_text(output_path, render_model_report(model_results, family_name=family_name))
