from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.data_processing.cleaner import clean_dataset
from src.features.preprocessor import TabularPreprocessor
from src.interfaces.shared.dashboard_schema import normalize_dashboard_summary
from src.interfaces.shared.formatters import normalize_prediction_result
from src.interfaces.shared.sample_schema import coerce_prediction_payload
from src.models.logistic_regression import SoftmaxLogisticRegression
from src.models.manual_trainer import load_model_state
from src.models.neural_network import SimpleNeuralNetwork
from src.models.sklearn_trainer import load_pickle
from src.utils.file_utils import read_json
from src.log import get_logger

logger = get_logger('serving-inference')


# 加载 sklearn 推理产物
def load_sklearn_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    sklearn_model_dir = Path(config['output_dirs']['models']) / 'sklearn'
    logistic_bundle = load_pickle(sklearn_model_dir / 'logistic_regression.pkl')
    mlp_bundle = load_pickle(sklearn_model_dir / 'mlp_classifier.pkl')
    best_model_bundle = load_pickle(sklearn_model_dir / 'best_model.pkl')
    return {'logistic_regression': logistic_bundle, 'mlp_classifier': mlp_bundle, 'best_model_name': best_model_bundle['name']}


# 加载手搓推理产物
def load_manual_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any] | None:
    model_dir = Path(config['output_dirs']['models'])
    preprocessor_path = model_dir / 'preprocessor.json'
    logistic_path = model_dir / 'logistic_regression_model.npz'
    neural_path = model_dir / 'neural_network_model.npz'
    if not (preprocessor_path.exists() and logistic_path.exists() and neural_path.exists()):
        return None
    preprocessor = TabularPreprocessor.from_dict(read_json(preprocessor_path))
    logistic_state = load_model_state(logistic_path)
    neural_state = load_model_state(neural_path)
    return {
        'preprocessor': preprocessor,
        'logistic_regression': SoftmaxLogisticRegression.from_state(logistic_state),
        'neural_network': SimpleNeuralNetwork.from_state(neural_state),
    }


# 合并加载可用推理产物
def load_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    sklearn_bundle = None
    try:
        sklearn_bundle = load_sklearn_inference_bundle(config)
    except FileNotFoundError:
        logger.warning('未检测到 sklearn 推理模型文件。')
    return {'sklearn': sklearn_bundle, 'manual': load_manual_inference_bundle(config)}


# 加载仪表盘摘要
def load_dashboard_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    dashboard_path = Path(config['output_dirs']['evaluation']) / 'training_dashboard.json'
    if dashboard_path.exists():
        return normalize_dashboard_summary(read_json(dashboard_path), config)
    return normalize_dashboard_summary({
        'project_name': config['project_name'],
        'message': '尚未检测到训练摘要，请先执行 train / train-sklearn / train-manual。',
        'training_mode': 'artifacts-only',
        'status': 'no_dashboard',
        'generated_at': None,
        'families': {'sklearn': None, 'manual': None},
        'dataset': {
            'sample_count': '-',
            'class_count': '-',
            'split': {},
        },
        'comparison_rows': [],
        'parameter_tables': [],
        'artifacts': {},
        'recommended_model': {'family': '-', 'name': '-', 'macro_f1': None},
    }, config)


# 使用 sklearn 模型预测
def predict_with_sklearn(payload: Dict[str, Any], config: Dict[str, Any], sklearn_bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw_frame = pd.DataFrame([payload])
    raw_frame[config['raw_target_column']] = 'Normal_Weight'
    prepared_frame = clean_dataset(raw_frame, config)
    prediction_result: Dict[str, Any] = {}
    for model_name in ['logistic_regression', 'mlp_classifier']:
        bundle = sklearn_bundle[model_name]
        feature_frame = prepared_frame[bundle['feature_columns']].copy()
        transformed_features = bundle['preprocessor'].transform(feature_frame)
        probabilities = bundle['classifier'].predict_proba(transformed_features)[0]
        prediction_index = int(np.argmax(probabilities))
        class_names = bundle['class_names']
        prediction_result[model_name] = {
            'prediction': class_names[prediction_index],
            'probabilities': {class_name: round(float(probability), 6) for class_name, probability in zip(class_names, probabilities)},
            'best_parameters': bundle.get('best_parameters', {}),
        }
    recommended_model_name = sklearn_bundle['best_model_name']
    prediction_result['recommended_result'] = prediction_result[recommended_model_name]['prediction']
    prediction_result['recommended_model'] = recommended_model_name
    return prediction_result


# 使用手搓模型预测
def predict_with_manual(payload: Dict[str, Any], config: Dict[str, Any], manual_bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw_frame = pd.DataFrame([payload])
    raw_frame[config['raw_target_column']] = 'Normal_Weight'
    prepared_frame = clean_dataset(raw_frame, config)
    feature_frame = prepared_frame.drop(columns=[config['target_column']], errors='ignore')
    preprocessor: TabularPreprocessor = manual_bundle['preprocessor']
    X = preprocessor.transform(feature_frame)
    logistic_model: SoftmaxLogisticRegression = manual_bundle['logistic_regression']
    neural_model: SimpleNeuralNetwork = manual_bundle['neural_network']
    logistic_probabilities = logistic_model.predict_proba(X)
    neural_probabilities = neural_model.predict_proba(X)
    logistic_prediction = preprocessor.decode_target(np.argmax(logistic_probabilities, axis=1))[0]
    neural_prediction = preprocessor.decode_target(np.argmax(neural_probabilities, axis=1))[0]
    return {
        'logistic_regression': {'prediction': logistic_prediction, 'probabilities': preprocessor.probabilities_to_dict(logistic_probabilities)[0]},
        'neural_network': {'prediction': neural_prediction, 'probabilities': preprocessor.probabilities_to_dict(neural_probabilities)[0]},
    }


# 执行单样本预测分发
def predict_single(payload: Dict[str, Any], config: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    payload = coerce_prediction_payload(payload)
    result: Dict[str, Any] = {'success': True}
    if bundle.get('sklearn') is not None:
        result['sklearn'] = predict_with_sklearn(payload, config, bundle['sklearn'])
    if bundle.get('manual') is not None:
        result['manual'] = predict_with_manual(payload, config, bundle['manual'])
    if 'sklearn' not in result and 'manual' not in result:
        raise ValueError('未检测到可用模型，请先执行训练。')
    return normalize_prediction_result(result)
