from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .sample_schema import FIELD_DEFINITIONS


DEFAULT_TRAINING_MODE = 'train'
TRAINING_MODE_OPTIONS = [
    {'value': 'train', 'label': '全量训练', 'description': '同时运行 sklearn 与手搓训练链路。'},
    {'value': 'train-sklearn', 'label': 'sklearn 训练', 'description': '只运行 sklearn 训练链路。'},
    {'value': 'train-manual', 'label': '手搓模型训练', 'description': '只运行手搓模型训练链路。'},
    {'value': 'artifacts-only', 'label': '仅展示已有产物', 'description': '只加载已生成的摘要与产物。'},
]
TRAINING_MODE_LABELS = {item['value']: item['label'] for item in TRAINING_MODE_OPTIONS}
ARTIFACT_GROUP_NAMES = ('analysis', 'evaluation', 'figures', 'logs', 'models', 'predictions', 'reports')


# 获取训练路线标签
def get_training_mode_label(mode: str | None) -> str:
    return TRAINING_MODE_LABELS.get(mode or '', mode or '未知')


# 统一数值精度
def normalize_metric_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


# 规范化指标字典
def normalize_metric_dict(metrics: Dict[str, Any] | None) -> Dict[str, Any]:
    if not metrics:
        return {'accuracy': None, 'macro_precision': None, 'macro_recall': None, 'macro_f1': None}
    return {key: normalize_metric_value(metrics.get(key)) for key in ('accuracy', 'macro_precision', 'macro_recall', 'macro_f1')}


# 规范化对比行
def normalize_comparison_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({
            'family': row.get('family', '-'),
            'name': row.get('name', '-'),
            'metrics': normalize_metric_dict(row.get('metrics')),
        })
    return normalized_rows


# 规范化参数行
def normalize_parameter_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({
            'family': row.get('family', '-'),
            'name': row.get('name', '-'),
            'parameters': row.get('parameters', {}),
        })
    return normalized_rows


# 构建产物分组
def build_artifact_groups(artifacts: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    for group_name in ARTIFACT_GROUP_NAMES:
        files = list(artifacts.get(group_name, []))
        groups.append({
            'name': group_name,
            'label': group_name,
            'files': files,
            'file_count': len(files),
            'exists': bool(files),
            'preview_files': [path for path in files if path.lower().endswith(('.png', '.svg', '.jpg', '.jpeg'))][:6],
        })
    return groups


# 构建图表分组
def build_chart_groups(artifacts: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    figures = list(artifacts.get('figures', []))
    grouped: Dict[str, List[str]] = {}
    for file_path in figures:
        relative_path = Path(file_path)
        group_name = relative_path.parts[-2] if len(relative_path.parts) >= 2 else 'figures'
        grouped.setdefault(group_name, []).append(file_path)
    return [
        {
            'name': group_name,
            'files': files,
            'cover': next((path for path in files if path.lower().endswith('.png')), files[0]),
        }
        for group_name, files in sorted(grouped.items())
    ]


# 构建仪表盘总览
def build_overview(summary: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    dataset = summary.get('dataset', {})
    recommended = summary.get('recommended_model', {})
    return {
        'project_name': summary.get('project_name', config.get('project_name', '未知项目')),
        'sample_count': dataset.get('sample_count', '-'),
        'class_count': dataset.get('class_count', '-'),
        'target_column': dataset.get('target_column', config.get('target_column', '-')),
        'recommended_model': {
            'family': recommended.get('family', '-'),
            'name': recommended.get('name', '-'),
            'label': f"{recommended.get('family', '-')}/{recommended.get('name', '-')}",
            'macro_f1': normalize_metric_value(recommended.get('macro_f1')),
        },
        'best_macro_f1': normalize_metric_value(recommended.get('macro_f1')),
        'training_status': summary.get('status', 'ready'),
        'training_mode': summary.get('training_mode', DEFAULT_TRAINING_MODE),
        'training_mode_label': get_training_mode_label(summary.get('training_mode', DEFAULT_TRAINING_MODE)),
        'generated_at': summary.get('generated_at'),
        'message': summary.get('message', '训练摘要已加载。'),
        'split': dataset.get('split', {}),
    }


# 规范化仪表盘摘要
def normalize_dashboard_summary(summary: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = summary.get('artifacts', {})
    log_files = list(artifacts.get('logs', []))
    normalized = {
        'project_name': summary.get('project_name', config.get('project_name', '未知项目')),
        'generated_at': summary.get('generated_at'),
        'training_mode': summary.get('training_mode', DEFAULT_TRAINING_MODE),
        'status': summary.get('status', 'ready'),
        'message': summary.get('message', '训练摘要已加载。'),
        'overview': build_overview(summary, config),
        'dataset': summary.get('dataset', {}),
        'analysis_summary': summary.get('analysis_summary', {}),
        'families': summary.get('families', {}),
        'comparison_rows': normalize_comparison_rows(summary.get('comparison_rows', [])),
        'parameter_rows': normalize_parameter_rows(summary.get('parameter_tables', [])),
        'recommended_model': {
            'family': summary.get('recommended_model', {}).get('family', '-'),
            'name': summary.get('recommended_model', {}).get('name', '-'),
            'macro_f1': normalize_metric_value(summary.get('recommended_model', {}).get('macro_f1')),
        },
        'artifacts': artifacts,
        'artifact_groups': build_artifact_groups(artifacts),
        'chart_groups': build_chart_groups(artifacts),
        'artifact_status': {
            'models': bool(artifacts.get('models')),
            'figures': bool(artifacts.get('figures')),
            'reports': bool(artifacts.get('reports')),
            'logs': bool(artifacts.get('logs')),
            'analysis': bool(artifacts.get('analysis')),
            'log_path': log_files[0] if log_files else str(Path(config.get('output_dirs', {}).get('logs', 'output/logs')) / 'project.log'),
        },
        'available_training_modes': TRAINING_MODE_OPTIONS,
        'sample_fields': [
            {
                'name': field_name,
                'label': label_text,
                'default': default_value,
                'options': options,
            }
            for field_name, label_text, default_value, options in FIELD_DEFINITIONS
        ],
        'latest_artifact_time': summary.get('generated_at'),
    }
    if 'current_training_status' not in normalized:
        normalized['current_training_status'] = normalized['overview']['training_status']
    return normalized
