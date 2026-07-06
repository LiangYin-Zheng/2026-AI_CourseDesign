from __future__ import annotations

from typing import Any, Dict, Iterable, List


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

