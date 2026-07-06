from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import numpy as np
import pandas as pd

from src.evaluation.metrics import evaluate_predictions
from src.features.preprocessor import TabularPreprocessor
from src.models.logistic_regression import SoftmaxLogisticRegression
from src.models.neural_network import SimpleNeuralNetwork
from src.utils.file_utils import write_json, write_text
from src.utils.logger import get_logger
from src.visualization.training_plots import save_metric_comparison, save_named_metric_bars, save_training_curve

logger = get_logger('manual-trainer')
ProgressAdvanceCallback = Callable[[str, str], None]


def count_manual_training_units(config: Dict[str, Any]) -> int:
    logistic_grid = list(product(*config['optimization_grids']['logistic_regression'].values()))
    neural_grid = list(product(*config['optimization_grids']['neural_network'].values()))
    return 4 + len(logistic_grid) + len(neural_grid)


def _advance(progress_callback: ProgressAdvanceCallback | None, stage: str, detail: str = '') -> None:
    if progress_callback is not None:
        progress_callback(stage, detail)


def save_model_state(model_path: str | Path, state: Dict[str, Any]) -> None:
    serializable_state: Dict[str, Any] = {}
    for key, value in state.items():
        if isinstance(value, np.ndarray):
            serializable_state[key] = value
        elif isinstance(value, list):
            serializable_state[key] = np.array(value, dtype=object)
        else:
            serializable_state[key] = np.array(value, dtype=object)
    np.savez(model_path, **serializable_state)


def load_model_state(model_path: str | Path) -> Dict[str, Any]:
    state: Dict[str, Any] = {}
    with np.load(model_path, allow_pickle=True) as data:
        for key in data.files:
            value = data[key]
            state[key] = value.item() if value.shape == () else value
    return state


def build_logistic_model(parameters: Dict[str, Any], random_seed: int) -> SoftmaxLogisticRegression:
    return SoftmaxLogisticRegression(
        learning_rate=float(parameters['learning_rate']),
        epochs=int(parameters['epochs']),
        reg_strength=float(parameters['reg_strength']),
        random_seed=random_seed,
    )


def build_neural_network_model(parameters: Dict[str, Any], random_seed: int) -> SimpleNeuralNetwork:
    return SimpleNeuralNetwork(
        hidden_units=int(parameters['hidden_units']),
        learning_rate=float(parameters['learning_rate']),
        epochs=int(parameters['epochs']),
        l2_strength=float(parameters['l2_strength']),
        random_seed=random_seed,
    )


def _fit_candidate(
    model_name: str,
    parameters: Dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    random_seed: int,
    class_names: list[str],
):
    model = build_logistic_model(parameters, random_seed) if model_name == 'logistic_regression' else build_neural_network_model(parameters, random_seed)
    model.fit(X_train, y_train, X_validation, y_validation)
    predictions = model.predict(X_validation)
    probabilities = model.predict_proba(X_validation)
    metrics = evaluate_predictions(y_validation, predictions, probabilities=probabilities, class_names=class_names)
    return model, metrics


def tune_model(
    model_name: str,
    parameter_grid: Dict[str, list[Any]],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    random_seed: int,
    class_names: list[str],
    progress_callback: ProgressAdvanceCallback | None = None,
) -> Tuple[Dict[str, Any], Dict[str, float], list[Dict[str, Any]]]:
    best_parameters: Dict[str, Any] | None = None
    best_metrics: Dict[str, float] | None = None
    search_history: list[Dict[str, Any]] = []

    parameter_names = list(parameter_grid.keys())
    search_space = list(product(*(parameter_grid[name] for name in parameter_names)))
    for step_index, parameter_values in enumerate(search_space, start=1):
        candidate_parameters = dict(zip(parameter_names, parameter_values))
        _, metrics = _fit_candidate(
            model_name,
            candidate_parameters,
            X_train,
            y_train,
            X_validation,
            y_validation,
            random_seed,
            class_names,
        )
        search_history.append({
            'step': step_index,
            'parameters': candidate_parameters,
            'validation_macro_f1': float(metrics['macro_f1']),
            'validation_accuracy': float(metrics['accuracy']),
        })
        if best_metrics is None or float(metrics['macro_f1']) > float(best_metrics['macro_f1']):
            best_parameters = candidate_parameters
            best_metrics = metrics
        _advance(
            progress_callback,
            f'手搓 {model_name} 参数搜索',
            f'{step_index}/{len(search_space)} | 当前最佳 Macro F1={float(best_metrics["macro_f1"]):.4f}',
        )

    if best_parameters is None or best_metrics is None:
        raise ValueError('参数调优失败，未获得有效模型。')
    return best_parameters, best_metrics, search_history


def save_manual_visualizations(training_summary: Dict[str, Any], figure_root: Path) -> None:
    comparison_models = [
        {'name': 'Baseline Logistic', 'metrics': training_summary['model_results']['baseline']['logistic_regression']['test_metrics']},
        {'name': 'Optimized Logistic', 'metrics': training_summary['model_results']['optimized']['logistic_regression']['test_metrics']},
        {'name': 'Baseline Neural', 'metrics': training_summary['model_results']['baseline']['neural_network']['test_metrics']},
        {'name': 'Optimized Neural', 'metrics': training_summary['model_results']['optimized']['neural_network']['test_metrics']},
    ]
    save_metric_comparison(comparison_models, figure_root / 'comparison' / 'manual_model_comparison.png', '手搓模型优化前后对比图')
    save_named_metric_bars(comparison_models, figure_root / 'comparison' / 'manual_metric_bars.png', '手搓模型指标柱状图')
    histories = training_summary['histories']
    if histories.get('logistic_regression'):
        save_training_curve(histories['logistic_regression'], figure_root / 'training' / 'manual_logistic_training_curve.png', '手搓 Logistic 训练曲线')
    if histories.get('neural_network'):
        save_training_curve(histories['neural_network'], figure_root / 'training' / 'manual_neural_training_curve.png', '手搓 Neural Network 训练曲线')


def render_manual_report(training_summary: Dict[str, Any]) -> str:
    results = training_summary['model_results']
    return '\n'.join([
        '# 手搓模型训练摘要',
        '',
        '## 1. 优化后参数',
        f"- logistic_regression: {results['optimized']['logistic_regression']['parameters']}",
        f"- neural_network: {results['optimized']['neural_network']['parameters']}",
        '',
        '## 2. 测试集指标',
        f"- logistic_regression: {results['optimized']['logistic_regression']['test_metrics']}",
        f"- neural_network: {results['optimized']['neural_network']['test_metrics']}",
        '',
        f"- 推荐模型：{training_summary['best_model_name']}",
    ])


def train_all_models(
    datasets: Dict[str, pd.DataFrame],
    preprocessor: TabularPreprocessor,
    config: Dict[str, Any],
    progress_callback: ProgressAdvanceCallback | None = None,
) -> Dict[str, Any]:
    target_column = config['target_column']
    random_seed = int(config['random_seed'])
    model_output_dir = Path(config['output_dirs']['models'])
    evaluation_output_dir = Path(config['output_dirs']['evaluation'])
    prediction_output_dir = Path(config['output_dirs']['predictions'])
    figure_root = Path(config['output_dirs']['figures'])
    report_output_dir = Path(config['output_dirs']['reports'])

    X_train = preprocessor.transform(datasets['train'])
    y_train = preprocessor.encode_target(datasets['train'][target_column])
    X_validation = preprocessor.transform(datasets['validation'])
    y_validation = preprocessor.encode_target(datasets['validation'][target_column])
    X_test = preprocessor.transform(datasets['test'])
    y_test = preprocessor.encode_target(datasets['test'][target_column])
    X_train_validation = preprocessor.transform(pd.concat([datasets['train'], datasets['validation']], axis=0, ignore_index=True))
    y_train_validation = preprocessor.encode_target(pd.concat([datasets['train'][target_column], datasets['validation'][target_column]], axis=0, ignore_index=True))
    class_names = list(preprocessor.class_names)

    logger.info('手搓模型训练输入：train=%s | validation=%s | test=%s | feature_dim=%s | class_count=%s', len(datasets['train']), len(datasets['validation']), len(datasets['test']), X_train.shape[1], len(class_names))

    baseline_logistic_parameters = config['baseline_models']['logistic_regression']
    baseline_logistic_model, baseline_logistic_validation_metrics = _fit_candidate(
        'logistic_regression', baseline_logistic_parameters, X_train, y_train, X_validation, y_validation, random_seed, class_names
    )
    baseline_logistic_predictions = baseline_logistic_model.predict(X_test)
    baseline_logistic_probabilities = baseline_logistic_model.predict_proba(X_test)
    baseline_logistic_metrics = evaluate_predictions(y_test, baseline_logistic_predictions, probabilities=baseline_logistic_probabilities, class_names=class_names)
    _advance(progress_callback, '手搓 logistic baseline', f"Macro F1={float(baseline_logistic_metrics['macro_f1']):.4f}")

    best_logistic_parameters, logistic_validation_metrics, logistic_search_history = tune_model(
        'logistic_regression', config['optimization_grids']['logistic_regression'], X_train, y_train, X_validation, y_validation, random_seed, class_names, progress_callback
    )
    best_logistic_model = build_logistic_model(best_logistic_parameters, random_seed)
    best_logistic_model.fit(X_train_validation, y_train_validation, X_validation, y_validation)
    logistic_test_predictions = best_logistic_model.predict(X_test)
    logistic_test_probabilities = best_logistic_model.predict_proba(X_test)
    optimized_logistic_metrics = evaluate_predictions(y_test, logistic_test_predictions, probabilities=logistic_test_probabilities, class_names=class_names)
    _advance(progress_callback, '手搓 logistic 最终训练', f"Macro F1={float(optimized_logistic_metrics['macro_f1']):.4f}")

    baseline_neural_parameters = config['baseline_models']['neural_network']
    baseline_neural_model, baseline_neural_validation_metrics = _fit_candidate(
        'neural_network', baseline_neural_parameters, X_train, y_train, X_validation, y_validation, random_seed, class_names
    )
    baseline_neural_predictions = baseline_neural_model.predict(X_test)
    baseline_neural_probabilities = baseline_neural_model.predict_proba(X_test)
    baseline_neural_metrics = evaluate_predictions(y_test, baseline_neural_predictions, probabilities=baseline_neural_probabilities, class_names=class_names)
    _advance(progress_callback, '手搓 neural baseline', f"Macro F1={float(baseline_neural_metrics['macro_f1']):.4f}")

    best_neural_parameters, neural_validation_metrics, neural_search_history = tune_model(
        'neural_network', config['optimization_grids']['neural_network'], X_train, y_train, X_validation, y_validation, random_seed, class_names, progress_callback
    )
    best_neural_model = build_neural_network_model(best_neural_parameters, random_seed)
    best_neural_model.fit(X_train_validation, y_train_validation, X_validation, y_validation)
    neural_test_predictions = best_neural_model.predict(X_test)
    neural_test_probabilities = best_neural_model.predict_proba(X_test)
    optimized_neural_metrics = evaluate_predictions(y_test, neural_test_predictions, probabilities=neural_test_probabilities, class_names=class_names)
    _advance(progress_callback, '手搓 neural 最终训练', f"Macro F1={float(optimized_neural_metrics['macro_f1']):.4f}")

    model_results = {
        'baseline': {
            'logistic_regression': {'parameters': baseline_logistic_parameters, 'validation_metrics': baseline_logistic_validation_metrics, 'test_metrics': baseline_logistic_metrics},
            'neural_network': {'parameters': baseline_neural_parameters, 'validation_metrics': baseline_neural_validation_metrics, 'test_metrics': baseline_neural_metrics},
        },
        'optimized': {
            'logistic_regression': {'parameters': best_logistic_parameters, 'validation_metrics': logistic_validation_metrics, 'test_metrics': optimized_logistic_metrics},
            'neural_network': {'parameters': best_neural_parameters, 'validation_metrics': neural_validation_metrics, 'test_metrics': optimized_neural_metrics},
        },
    }

    best_model_name = 'neural_network'
    if float(optimized_logistic_metrics['macro_f1']) >= float(optimized_neural_metrics['macro_f1']):
        best_model_name = 'logistic_regression'

    save_model_state(model_output_dir / 'logistic_regression_model.npz', best_logistic_model.to_state())
    save_model_state(model_output_dir / 'neural_network_model.npz', best_neural_model.to_state())
    write_json(model_output_dir / 'preprocessor.json', preprocessor.to_dict())
    write_json(evaluation_output_dir / 'manual_model_results.json', model_results)
    write_json(evaluation_output_dir / 'model_results.json', model_results)

    prediction_frame = pd.DataFrame({
        'actual_label': preprocessor.decode_target(y_test),
        'logistic_prediction': preprocessor.decode_target(logistic_test_predictions),
        'neural_prediction': preprocessor.decode_target(neural_test_predictions),
    })
    prediction_frame.to_csv(prediction_output_dir / 'test_predictions.csv', index=False, encoding='utf-8-sig')

    training_summary = {
        'family': 'manual',
        'class_names': class_names,
        'best_model_name': best_model_name,
        'model_results': model_results,
        'search_history': {
            'logistic_regression': logistic_search_history,
            'neural_network': neural_search_history,
        },
        'histories': {
            'baseline_logistic_regression': baseline_logistic_model.history,
            'baseline_neural_network': baseline_neural_model.history,
            'logistic_regression': best_logistic_model.history,
            'neural_network': best_neural_model.history,
        },
        'test_sets': {
            'y_test': y_test.tolist(),
            'logistic_probabilities': logistic_test_probabilities.tolist(),
            'neural_probabilities': neural_test_probabilities.tolist(),
            'logistic_predictions': logistic_test_predictions.tolist(),
            'neural_predictions': neural_test_predictions.tolist(),
        },
        'parameter_summary': [
            {'family': 'manual', 'name': 'logistic_regression', 'parameters': best_logistic_parameters},
            {'family': 'manual', 'name': 'neural_network', 'parameters': best_neural_parameters},
        ],
    }

    save_manual_visualizations(training_summary, figure_root)
    write_text(report_output_dir / 'manual_model_summary.md', render_manual_report(training_summary))
    logger.info('手搓模型训练完成：best_model=%s | best_macro_f1=%s', best_model_name, model_results['optimized'][best_model_name]['test_metrics']['macro_f1'])
    return training_summary
