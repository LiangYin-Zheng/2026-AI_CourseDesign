from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config import load_project_config


def load_ui_catalog() -> Dict[str, Any]:
    ui_catalog = dict(load_project_config().get('ui', {}))
    if ui_catalog:
        return ui_catalog
    raise ValueError('未找到 UI 配置：config/project.yaml')


def get_training_mode_options(ui_catalog: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    catalog = ui_catalog or load_ui_catalog()
    return list(catalog.get('training_modes', []))


def get_default_training_mode(ui_catalog: Dict[str, Any] | None = None) -> str:
    catalog = ui_catalog or load_ui_catalog()
    return str(catalog.get('app', {}).get('default_training_mode', 'train'))


def get_form_fields(ui_catalog: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    catalog = ui_catalog or load_ui_catalog()
    return list(catalog.get('form_fields', []))


def get_artifact_groups(ui_catalog: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    catalog = ui_catalog or load_ui_catalog()
    return list(catalog.get('artifact_groups', []))


def get_navigation_items(ui_catalog: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    catalog = ui_catalog or load_ui_catalog()
    return list(catalog.get('navigation', []))


def get_page_copy(ui_catalog: Dict[str, Any] | None = None) -> Dict[str, Any]:
    catalog = ui_catalog or load_ui_catalog()
    return dict(catalog.get('page_copy', {}))


def get_status_messages(ui_catalog: Dict[str, Any] | None = None) -> Dict[str, str]:
    catalog = ui_catalog or load_ui_catalog()
    return dict(catalog.get('status_messages', {}))


def build_field_definitions(ui_catalog: Dict[str, Any] | None = None) -> List[tuple[Any, ...]]:
    fields = []
    for field in get_form_fields(ui_catalog):
        fields.append((field['name'], field['label'], field.get('default'), field.get('options')))
    return fields


_UI_CATALOG = load_ui_catalog()
DEFAULT_TRAINING_MODE = get_default_training_mode(_UI_CATALOG)
TRAINING_MODE_OPTIONS = get_training_mode_options(_UI_CATALOG)
TRAINING_MODE_LABELS = {item['value']: item['label'] for item in TRAINING_MODE_OPTIONS}
ARTIFACT_GROUP_NAMES = [item['key'] for item in get_artifact_groups(_UI_CATALOG)]
FIELD_DEFINITIONS = build_field_definitions(_UI_CATALOG)


def get_training_mode_label(mode: str | None) -> str:
    return TRAINING_MODE_LABELS.get(mode or '', mode or '未知')


def normalize_metric_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def normalize_metric_dict(metrics: Dict[str, Any] | None) -> Dict[str, Any]:
    if not metrics:
        return {'accuracy': None, 'macro_precision': None, 'macro_recall': None, 'macro_f1': None}
    return {key: normalize_metric_value(metrics.get(key)) for key in ('accuracy', 'macro_precision', 'macro_recall', 'macro_f1')}


def normalize_comparison_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({
            'family': row.get('family', '-'),
            'name': row.get('name', '-'),
            'metrics': normalize_metric_dict(row.get('metrics')),
        })
    return normalized_rows


def normalize_parameter_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({
            'family': row.get('family', '-'),
            'name': row.get('name', '-'),
            'parameters': row.get('parameters', {}),
        })
    return normalized_rows


def build_artifact_groups(artifacts: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    group_catalog = {item['key']: item for item in get_artifact_groups(_UI_CATALOG)}
    for group_name in ARTIFACT_GROUP_NAMES:
        files = list(artifacts.get(group_name, []))
        meta = group_catalog.get(group_name, {})
        groups.append({
            'name': group_name,
            'label': meta.get('label', group_name),
            'description': meta.get('description', ''),
            'files': files,
            'file_count': len(files),
            'exists': bool(files),
            'preview_files': [path for path in files if path.lower().endswith(('.png', '.svg', '.jpg', '.jpeg'))][:6],
        })
    return groups


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
        'ui_copy': {
            'page_copy': _UI_CATALOG.get('page_copy', {}),
            'buttons': _UI_CATALOG.get('buttons', {}),
            'status_messages': get_status_messages(_UI_CATALOG),
        },
        'latest_artifact_time': summary.get('generated_at'),
    }
    if 'current_training_status' not in normalized:
        normalized['current_training_status'] = normalized['overview']['training_status']
    return normalized


_FIELD_META = {field['name']: field for field in _UI_CATALOG.get('form_fields', [])}
INTEGER_FIELDS = {name for name, meta in _FIELD_META.items() if meta.get('value_type') == 'int'}
FLOAT_FIELDS = {name for name, meta in _FIELD_META.items() if meta.get('value_type') == 'float'}
SAMPLE_FIELD_NAMES = {field_name for field_name, *_ in FIELD_DEFINITIONS}


def coerce_value(field_name: str, raw_value: str) -> Any:
    if field_name in INTEGER_FIELDS:
        return int(float(raw_value))
    if field_name in FLOAT_FIELDS:
        return float(raw_value)
    return raw_value


def coerce_sample_value(field_name: str, raw_value: str) -> Any:
    return coerce_value(field_name, raw_value)


def build_sample_payload(field_values: dict[str, str]) -> dict[str, Any]:
    return {field_name: coerce_value(field_name, raw_value) for field_name, raw_value in field_values.items()}


def coerce_prediction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload: dict[str, Any] = {}
    for field_name, raw_value in payload.items():
        if field_name in SAMPLE_FIELD_NAMES:
            normalized_payload[field_name] = coerce_value(field_name, str(raw_value))
        else:
            normalized_payload[field_name] = raw_value
    return normalized_payload


def format_probability_map(probabilities: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {'label': label, 'probability': round(float(value), 6)}
        for label, value in sorted(probabilities.items(), key=lambda item: float(item[1]), reverse=True)
    ]


def _normalize_branch(branch: Dict[str, Any]) -> Dict[str, Any]:
    model_rows = []
    for model_name, payload in branch.items():
        if model_name in {'recommended_model', 'recommended_result'}:
            continue
        if not isinstance(payload, dict):
            continue
        model_rows.append({
            'name': model_name,
            'prediction': payload.get('prediction'),
            'probabilities': format_probability_map(payload.get('probabilities', {})),
            'best_parameters': payload.get('best_parameters', {}),
        })
    return {
        'models': model_rows,
        'recommended_model': branch.get('recommended_model'),
        'recommended_result': branch.get('recommended_result'),
    }


def normalize_prediction_result(result: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        'success': bool(result.get('success', True)),
        'message': result.get('message'),
    }
    if 'sklearn' in result and isinstance(result['sklearn'], dict):
        normalized['sklearn'] = _normalize_branch(result['sklearn'])
    if 'manual' in result and isinstance(result['manual'], dict):
        normalized['manual'] = _normalize_branch(result['manual'])
    if 'recommended_result' in result:
        normalized['recommended_result'] = result['recommended_result']
    if 'recommended_model' in result:
        normalized['recommended_model'] = result['recommended_model']
    if not normalized['success'] and 'error' in result:
        normalized['error'] = result['error']
    return normalized
