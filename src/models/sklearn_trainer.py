from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import ParameterGrid
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings('ignore', category=RuntimeWarning, module=r'sklearn\..*')
warnings.filterwarnings('ignore', category=RuntimeWarning, module=r'sklearn\.utils\.extmath')
np.seterr(over='ignore', divide='ignore', invalid='ignore')

from src.evaluation.metrics import evaluate_predictions
from src.features.sklearn_pipeline import build_sklearn_preprocessor, select_feature_frame
from src.utils.file_utils import ensure_directory, write_json, write_text
from src.log.project import get_logger
from src.visualization import (
    save_confusion_matrix,
    save_metric_comparison,
    save_multiclass_roc_curve,
    save_named_metric_bars,
    save_search_progress,
    save_training_curve,
)

logger = get_logger('sklearn-trainer')
ProgressAdvanceCallback = Callable[[str, str], None]


# 统计 sklearn 训练总步骤
def count_sklearn_training_units(config: Dict[str, Any]) -> int:
    logistic_units = len(list(ParameterGrid(config['sklearn_models']['optimization_grids']['logistic_regression'])))
    mlp_units = len(list(ParameterGrid(config['sklearn_models']['optimization_grids']['mlp_classifier'])))
    return 4 + logistic_units + mlp_units


# 触发训练进度回调
def _advance(progress_callback: ProgressAdvanceCallback | None, stage: str, detail: str = '') -> None:
    if progress_callback is not None:
        progress_callback(stage, detail)


# 保存 pickle 文件
def save_pickle(path: str | Path, payload: Any) -> None:
    target_path = Path(path)
    ensure_directory(target_path.parent)
    with target_path.open('wb') as file:
        pickle.dump(payload, file)


# 读取 pickle 文件
def load_pickle(path: str | Path) -> Any:
    with Path(path).open('rb') as file:
        return pickle.load(file)


# 训练 sklearn 逻辑回归
def fit_logistic_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    y_eval: np.ndarray,
    parameters: Dict[str, Any],
    random_seed: int,
    class_names: List[str],
) -> Tuple[LogisticRegression, Dict[str, Any]]:
    model = LogisticRegression(
        C=float(parameters['C']),
        max_iter=int(parameters['max_iter']),
        class_weight=parameters.get('class_weight'),
        solver='saga',
        random_state=random_seed,
    )
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        warnings.simplefilter('ignore', RuntimeWarning)
        model.fit(X_train, y_train)
        predictions = model.predict(X_eval)
        probabilities = model.predict_proba(X_eval)
    metrics = evaluate_predictions(y_eval, predictions, probabilities=probabilities, class_names=class_names)
    return model, metrics


# 训练 sklearn MLP
def fit_mlp_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    y_eval: np.ndarray,
    parameters: Dict[str, Any],
    random_seed: int,
    class_names: List[str],
) -> Tuple[MLPClassifier, Dict[str, Any], List[Dict[str, Any]]]:
    epochs = int(parameters['epochs'])
    model = MLPClassifier(
        hidden_layer_sizes=(int(parameters['hidden_units']),),
        learning_rate_init=float(parameters['learning_rate_init']),
        alpha=float(parameters['alpha']),
        batch_size=min(256, max(32, len(X_train) // 4)),
        activation='relu',
        solver='adam',
        max_iter=1,
        warm_start=True,
        random_state=random_seed,
    )
    history: List[Dict[str, Any]] = []
    best_validation_f1 = -1.0

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        warnings.simplefilter('ignore', RuntimeWarning)
        for epoch_index in range(1, epochs + 1):
            with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                model.fit(X_train, y_train)
                train_probabilities = model.predict_proba(X_train)
                validation_probabilities = model.predict_proba(X_eval)
                validation_predictions = np.argmax(validation_probabilities, axis=1)
                validation_metrics = evaluate_predictions(y_eval, validation_predictions, probabilities=validation_probabilities, class_names=class_names)
                best_validation_f1 = max(best_validation_f1, float(validation_metrics['macro_f1']))
                history.append({
                    'epoch': epoch_index,
                    'train_loss': float(log_loss(y_train, train_probabilities, labels=list(range(len(class_names))))),
                    'validation_loss': float(log_loss(y_eval, validation_probabilities, labels=list(range(len(class_names))))),
                    'validation_macro_f1': float(validation_metrics['macro_f1']),
                    'best_validation_macro_f1': round(best_validation_f1, 6),
                })
    final_record = history[-1]
    return model, {
        'accuracy': float(validation_metrics['accuracy']),
        'macro_precision': float(validation_metrics['macro_precision']),
        'macro_recall': float(validation_metrics['macro_recall']),
        'macro_f1': float(validation_metrics['macro_f1']),
        'macro_roc_auc_ovr': float(validation_metrics.get('macro_roc_auc_ovr', 0.0)),
        'log_loss': float(final_record['validation_loss']),
    }, history


# 提取逻辑回归特征重要性
def summarize_logistic_feature_importance(model: LogisticRegression, feature_names: List[str]) -> List[Dict[str, Any]]:
    coefficients = np.mean(np.abs(model.coef_), axis=0)
    top_indices = np.argsort(coefficients)[::-1][:12]
    return [{'feature': feature_names[index], 'importance': round(float(coefficients[index]), 6)} for index in top_indices]


# 保存 sklearn 训练图表
def save_sklearn_visualizations(training_summary: Dict[str, Any], training_figure_dir: Path, comparison_figure_dir: Path) -> None:
    comparison_models = [
        {'name': 'Baseline Logistic', 'metrics': training_summary['model_results']['baseline']['logistic_regression']['test_metrics']},
        {'name': 'Optimized Logistic', 'metrics': training_summary['model_results']['optimized']['logistic_regression']['test_metrics']},
        {'name': 'Baseline MLP', 'metrics': training_summary['model_results']['baseline']['mlp_classifier']['test_metrics']},
        {'name': 'Optimized MLP', 'metrics': training_summary['model_results']['optimized']['mlp_classifier']['test_metrics']},
    ]
    save_metric_comparison(comparison_models, comparison_figure_dir / 'sklearn_model_comparison.png', 'sklearn 模型优化前后对比图')
    save_named_metric_bars(comparison_models, comparison_figure_dir / 'sklearn_metric_bars.png', 'sklearn 模型指标柱状图')
    save_search_progress(training_summary['search_history']['logistic_regression'], comparison_figure_dir / 'sklearn_logistic_search_progress.png', 'sklearn Logistic 参数搜索过程')
    save_search_progress(training_summary['search_history']['mlp_classifier'], comparison_figure_dir / 'sklearn_mlp_search_progress.png', 'sklearn MLP 参数搜索过程')
    save_training_curve(training_summary['histories']['mlp_classifier'], training_figure_dir / 'sklearn_mlp_training_curve.png', 'sklearn MLP 训练曲线')
    y_test = np.array(training_summary['test_sets']['y_test'])
    logistic_probabilities = np.array(training_summary['test_sets']['logistic_probabilities'])
    mlp_probabilities = np.array(training_summary['test_sets']['mlp_probabilities'])
    save_confusion_matrix(y_test, np.argmax(logistic_probabilities, axis=1), training_summary['class_names'], training_figure_dir / 'sklearn_logistic_confusion_matrix.png', 'sklearn Logistic 混淆矩阵')
    save_confusion_matrix(y_test, np.argmax(mlp_probabilities, axis=1), training_summary['class_names'], training_figure_dir / 'sklearn_mlp_confusion_matrix.png', 'sklearn MLP 混淆矩阵')
    save_multiclass_roc_curve(y_test, logistic_probabilities, training_summary['class_names'], training_figure_dir / 'sklearn_logistic_roc_curve.png', 'sklearn Logistic ROC 曲线')
    save_multiclass_roc_curve(y_test, mlp_probabilities, training_summary['class_names'], training_figure_dir / 'sklearn_mlp_roc_curve.png', 'sklearn MLP ROC 曲线')


# 生成 sklearn 训练摘要文本
def render_sklearn_report(training_summary: Dict[str, Any]) -> str:
    results = training_summary['model_results']
    return '\n'.join([
        '# sklearn 模型训练摘要',
        '',
        '## 1. 优化后参数',
        f"- logistic_regression: {results['optimized']['logistic_regression']['parameters']}",
        f"- mlp_classifier: {results['optimized']['mlp_classifier']['parameters']}",
        '',
        '## 2. 测试集指标',
        f"- logistic_regression: {results['optimized']['logistic_regression']['test_metrics']}",
        f"- mlp_classifier: {results['optimized']['mlp_classifier']['test_metrics']}",
        '',
        f"- 推荐模型：{training_summary['best_model_name']}",
    ])


# 训练全部 sklearn 模型
def train_sklearn_models(
    datasets: Dict[str, pd.DataFrame],
    config: Dict[str, Any],
    progress_callback: ProgressAdvanceCallback | None = None,
) -> Dict[str, Any]:
    target_column = config['target_column']
    random_seed = int(config['random_seed'])
    sklearn_model_dir = Path(config['output_dirs']['models']) / 'sklearn'
    evaluation_output_dir = Path(config['output_dirs']['evaluation'])
    prediction_output_dir = Path(config['output_dirs']['predictions'])
    report_output_dir = Path(config['output_dirs']['reports'])
    training_figure_dir = Path(config['output_dirs']['figures']) / 'training'
    comparison_figure_dir = Path(config['output_dirs']['figures']) / 'comparison'

    feature_columns = select_feature_frame(datasets['train'], config).columns.tolist()
    search_preprocessor = build_sklearn_preprocessor(config)
    X_train = search_preprocessor.fit_transform(select_feature_frame(datasets['train'], config))
    X_validation = search_preprocessor.transform(select_feature_frame(datasets['validation'], config))
    X_test = search_preprocessor.transform(select_feature_frame(datasets['test'], config))

    final_preprocessor = build_sklearn_preprocessor(config)
    X_train_validation = final_preprocessor.fit_transform(
        pd.concat([select_feature_frame(datasets['train'], config), select_feature_frame(datasets['validation'], config)], axis=0, ignore_index=True)
    )
    X_test_final = final_preprocessor.transform(select_feature_frame(datasets['test'], config))

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(datasets['train'][target_column].astype(str))
    y_validation = label_encoder.transform(datasets['validation'][target_column].astype(str))
    y_test = label_encoder.transform(datasets['test'][target_column].astype(str))
    y_train_validation = label_encoder.fit_transform(pd.concat([datasets['train'][target_column], datasets['validation'][target_column]], axis=0, ignore_index=True).astype(str))
    class_names = label_encoder.classes_.tolist()

    logger.info(
        'sklearn 训练输入：train={} | validation={} | test={} | feature_dim={} | class_count={}',
        len(datasets['train']),
        len(datasets['validation']),
        len(datasets['test']),
        X_train.shape[1],
        len(class_names),
    )

    baseline_config = config['sklearn_models']['baseline']
    logistic_grid = list(ParameterGrid(config['sklearn_models']['optimization_grids']['logistic_regression']))
    mlp_grid = list(ParameterGrid(config['sklearn_models']['optimization_grids']['mlp_classifier']))

    baseline_logistic_model, baseline_logistic_metrics = fit_logistic_model(X_train, y_train, X_test, y_test, baseline_config['logistic_regression'], random_seed, class_names)
    _advance(progress_callback, 'sklearn logistic baseline', f"Macro F1={float(baseline_logistic_metrics['macro_f1']):.4f}")

    best_logistic_score = -1.0
    best_logistic_parameters: Dict[str, Any] | None = None
    best_logistic_validation_metrics: Dict[str, Any] | None = None
    logistic_search_history: List[Dict[str, Any]] = []

    for step_index, parameter_set in enumerate(logistic_grid, start=1):
        _, validation_metrics = fit_logistic_model(X_train, y_train, X_validation, y_validation, parameter_set, random_seed, class_names)
        logistic_search_history.append({'step': step_index, 'parameters': parameter_set, 'validation_macro_f1': float(validation_metrics['macro_f1']), 'validation_accuracy': float(validation_metrics['accuracy'])})
        if float(validation_metrics['macro_f1']) > best_logistic_score:
            best_logistic_score = float(validation_metrics['macro_f1'])
            best_logistic_parameters = dict(parameter_set)
            best_logistic_validation_metrics = validation_metrics
        _advance(progress_callback, 'sklearn logistic 参数搜索', f'{step_index}/{len(logistic_grid)} | 当前最佳 Macro F1={best_logistic_score:.4f}')

    if best_logistic_parameters is None or best_logistic_validation_metrics is None:
        raise ValueError('LogisticRegression 调参失败，未找到有效参数组合。')

    optimized_logistic_model, optimized_logistic_test_metrics = fit_logistic_model(X_train_validation, y_train_validation, X_test_final, y_test, best_logistic_parameters, random_seed, class_names)
    logistic_probabilities = optimized_logistic_model.predict_proba(X_test_final)
    _advance(progress_callback, 'sklearn logistic 最终训练', f"Macro F1={float(optimized_logistic_test_metrics['macro_f1']):.4f}")

    baseline_mlp_model, baseline_mlp_metrics, baseline_mlp_history = fit_mlp_model(X_train, y_train, X_test, y_test, baseline_config['mlp_classifier'], random_seed, class_names)
    _advance(progress_callback, 'sklearn mlp baseline', f"Macro F1={float(baseline_mlp_metrics['macro_f1']):.4f}")

    best_mlp_score = -1.0
    best_mlp_parameters: Dict[str, Any] | None = None
    best_mlp_validation_metrics: Dict[str, Any] | None = None
    best_mlp_history: List[Dict[str, Any]] = []
    mlp_search_history: List[Dict[str, Any]] = []

    for step_index, parameter_set in enumerate(mlp_grid, start=1):
        _, validation_metrics, history = fit_mlp_model(X_train, y_train, X_validation, y_validation, parameter_set, random_seed, class_names)
        mlp_search_history.append({'step': step_index, 'parameters': parameter_set, 'validation_macro_f1': float(validation_metrics['macro_f1']), 'validation_accuracy': float(validation_metrics['accuracy'])})
        if float(validation_metrics['macro_f1']) > best_mlp_score:
            best_mlp_score = float(validation_metrics['macro_f1'])
            best_mlp_parameters = dict(parameter_set)
            best_mlp_validation_metrics = validation_metrics
            best_mlp_history = history
        _advance(progress_callback, 'sklearn mlp 参数搜索', f'{step_index}/{len(mlp_grid)} | 当前最佳 Macro F1={best_mlp_score:.4f}')

    if best_mlp_parameters is None or best_mlp_validation_metrics is None:
        raise ValueError('MLPClassifier 调参失败，未找到有效参数组合。')

    optimized_mlp_model, optimized_mlp_test_metrics, optimized_mlp_history = fit_mlp_model(X_train_validation, y_train_validation, X_test_final, y_test, best_mlp_parameters, random_seed, class_names)
    mlp_probabilities = optimized_mlp_model.predict_proba(X_test_final)
    _advance(progress_callback, 'sklearn mlp 最终训练', f"Macro F1={float(optimized_mlp_test_metrics['macro_f1']):.4f}")

    feature_names = final_preprocessor.get_feature_names_out(feature_columns).tolist()
    feature_importance = summarize_logistic_feature_importance(optimized_logistic_model, feature_names)

    model_results = {
        'baseline': {
            'logistic_regression': {'parameters': baseline_config['logistic_regression'], 'test_metrics': baseline_logistic_metrics},
            'mlp_classifier': {'parameters': baseline_config['mlp_classifier'], 'test_metrics': baseline_mlp_metrics},
        },
        'optimized': {
            'logistic_regression': {'parameters': best_logistic_parameters, 'validation_metrics': best_logistic_validation_metrics, 'test_metrics': optimized_logistic_test_metrics},
            'mlp_classifier': {'parameters': best_mlp_parameters, 'validation_metrics': best_mlp_validation_metrics, 'test_metrics': optimized_mlp_test_metrics},
        },
    }

    best_model_name = 'mlp_classifier'
    if float(optimized_logistic_test_metrics['macro_f1']) >= float(optimized_mlp_test_metrics['macro_f1']):
        best_model_name = 'logistic_regression'

    sklearn_logistic_bundle = {'model_type': 'sklearn', 'name': 'logistic_regression', 'preprocessor': final_preprocessor, 'classifier': optimized_logistic_model, 'feature_columns': feature_columns, 'class_names': class_names, 'best_parameters': best_logistic_parameters}
    sklearn_mlp_bundle = {'model_type': 'sklearn', 'name': 'mlp_classifier', 'preprocessor': final_preprocessor, 'classifier': optimized_mlp_model, 'feature_columns': feature_columns, 'class_names': class_names, 'best_parameters': best_mlp_parameters}
    best_model_bundle = sklearn_mlp_bundle if best_model_name == 'mlp_classifier' else sklearn_logistic_bundle

    save_pickle(sklearn_model_dir / 'logistic_regression.pkl', sklearn_logistic_bundle)
    save_pickle(sklearn_model_dir / 'mlp_classifier.pkl', sklearn_mlp_bundle)
    save_pickle(sklearn_model_dir / 'best_model.pkl', best_model_bundle)
    write_json(evaluation_output_dir / 'sklearn_model_results.json', model_results)

    prediction_frame = pd.DataFrame({
        'actual_label': label_encoder.inverse_transform(y_test),
        'logistic_regression_prediction': [class_names[index] for index in optimized_logistic_model.predict(X_test_final)],
        'mlp_classifier_prediction': [class_names[index] for index in optimized_mlp_model.predict(X_test_final)],
    })
    prediction_frame.to_csv(prediction_output_dir / 'sklearn_test_predictions.csv', index=False, encoding='utf-8-sig')

    training_summary = {
        'family': 'sklearn',
        'class_names': class_names,
        'best_model_name': best_model_name,
        'feature_importance': feature_importance,
        'model_results': model_results,
        'search_history': {'logistic_regression': logistic_search_history, 'mlp_classifier': mlp_search_history},
        'histories': {'baseline_mlp_classifier': baseline_mlp_history, 'mlp_classifier': best_mlp_history if best_mlp_history else optimized_mlp_history},
        'test_sets': {'y_test': y_test.tolist(), 'logistic_probabilities': logistic_probabilities.tolist(), 'mlp_probabilities': mlp_probabilities.tolist()},
        'parameter_summary': [
            {'family': 'sklearn', 'name': 'logistic_regression', 'parameters': best_logistic_parameters},
            {'family': 'sklearn', 'name': 'mlp_classifier', 'parameters': best_mlp_parameters},
        ],
    }

    save_sklearn_visualizations(training_summary, training_figure_dir, comparison_figure_dir)
    write_text(report_output_dir / 'sklearn_model_report.md', render_sklearn_report(training_summary))
    logger.info('sklearn 模型训练完成：best_model={} | best_macro_f1={}', best_model_name, model_results['optimized'][best_model_name]['test_metrics']['macro_f1'])
    return training_summary
