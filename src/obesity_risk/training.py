import json
import warnings
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from obesity_risk.evaluation import (
    evaluate_predictions,
    save_evaluation_artifacts,
    save_loss_curve,
)
from obesity_risk.manual_models import ManualLogisticRegression, ManualMLPClassifier
from obesity_risk.preparation import PreparedData


MODEL_DISPLAY_NAMES = {
    "sklearn_logistic": "sklearn 逻辑回归",
    "sklearn_mlp": "sklearn 神经网络",
    "manual_logistic": "NumPy 手写逻辑回归",
    "manual_mlp": "NumPy 手写神经网络",
}


# 规范化 YAML 中需要元组的 sklearn 参数
def _normalize_candidate(model_name: str, candidate: dict) -> dict:
    normalized = dict(candidate)
    if model_name == "sklearn_mlp" and isinstance(normalized.get("hidden_layer_sizes"), list):
        normalized["hidden_layer_sizes"] = tuple(normalized["hidden_layer_sizes"])
    return normalized


# 按模型类型创建 sklearn 分类器
def _build_sklearn_classifier(model_name: str, parameters: dict, config: dict) -> object:
    seed = int(config["split"]["random_seed"])
    if model_name == "sklearn_logistic":
        return LogisticRegression(
            **parameters,
            max_iter=int(config["training"][model_name]["max_iter"]),
            random_state=seed,
        )
    if model_name == "sklearn_mlp":
        model_config = config["training"][model_name]
        return MLPClassifier(
            **parameters,
            max_iter=int(model_config["max_iter"]),
            early_stopping=bool(model_config["early_stopping"]),
            validation_fraction=float(model_config["validation_fraction"]),
            random_state=seed,
        )
    raise ValueError(f"不支持的 sklearn 模型：{model_name}")


def train_sklearn_model(
    model_name: str,
    prepared: PreparedData,
    config: dict,
    models_dir: Path,
    metrics_dir: Path,
) -> dict:
    """训练 sklearn Pipeline，以验证集 macro F1 选择参数并评估测试集。"""
    candidates = config["training"][model_name]["candidates"]
    candidate_results = []
    best_pipeline: Pipeline | None = None
    best_parameters: dict | None = None
    best_validation: dict | None = None
    best_score = -np.inf
    best_training_time = 0.0
    for raw_candidate in candidates:
        parameters = _normalize_candidate(model_name, raw_candidate)
        pipeline = Pipeline(
            [
                ("preprocessor", clone(prepared.preprocessor)),
                ("classifier", _build_sklearn_classifier(model_name, parameters, config)),
            ]
        )
        started = perf_counter()
        # Apple Accelerate 会让 sklearn 的有限矩阵乘法继承浮点状态；随后以概率有限性做实质校验
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            pipeline.fit(prepared.train_features, prepared.train_labels)
            validation_predictions = pipeline.predict(prepared.validation_features)
            validation_probabilities = pipeline.predict_proba(prepared.validation_features)
        training_time = perf_counter() - started
        if not np.isfinite(validation_probabilities).all():
            raise FloatingPointError(f"{model_name} 验证概率包含非有限值")
        validation_metrics = evaluate_predictions(
            prepared.validation_labels,
            validation_predictions,
            prepared.label_encoder.classes_.tolist(),
        )
        candidate_results.append(
            {
                "parameters": parameters,
                "validation_macro_f1": validation_metrics["macro_f1"],
                "validation_accuracy": validation_metrics["accuracy"],
                "training_time_seconds": training_time,
            }
        )
        if validation_metrics["macro_f1"] > best_score:
            best_score = validation_metrics["macro_f1"]
            best_pipeline = pipeline
            best_parameters = parameters
            best_validation = validation_metrics
            best_training_time = training_time
    if best_pipeline is None or best_parameters is None or best_validation is None:
        raise RuntimeError("没有可用的 sklearn 参数候选")
    started = perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        test_predictions = best_pipeline.predict(prepared.test_features)
        test_probabilities = best_pipeline.predict_proba(prepared.test_features)
    if not np.isfinite(test_probabilities).all():
        raise FloatingPointError(f"{model_name} 测试概率包含非有限值")
    inference_time = perf_counter() - started
    class_names = prepared.label_encoder.classes_.tolist()
    result = {
        "model_name": model_name,
        "display_name": MODEL_DISPLAY_NAMES[model_name],
        "parameters": best_parameters,
        "parameters_json": json.dumps(best_parameters, ensure_ascii=False, indent=2),
        "selection_metric": "validation_macro_f1",
        "selection_reason": "验证集 macro F1 最高；测试集未参与候选选择",
        "candidate_results": candidate_results,
        "validation_metrics": best_validation,
        "test_metrics": evaluate_predictions(
            prepared.test_labels, test_predictions, class_names
        ),
        "training_time_seconds": best_training_time,
        "inference_time_seconds": inference_time,
        "class_names": class_names,
    }
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model_name": model_name,
            "mode": "sklearn_pipeline",
            "model": best_pipeline,
            "label_encoder": prepared.label_encoder,
            **prepared.input_metadata,
        },
        models_dir / f"{model_name}.joblib",
    )
    save_evaluation_artifacts(result, class_names, metrics_dir)
    return result


# 按配置创建一个 NumPy 手写模型
def _build_manual_model(model_name: str, config: dict) -> object:
    parameters = dict(config["training"][model_name])
    parameters["random_seed"] = int(config["split"]["random_seed"])
    if model_name == "manual_logistic":
        return ManualLogisticRegression(**parameters)
    if model_name == "manual_mlp":
        return ManualMLPClassifier(**parameters)
    raise ValueError(f"不支持的手写模型：{model_name}")


def train_manual_model(
    model_name: str,
    prepared: PreparedData,
    config: dict,
    models_dir: Path,
    metrics_dir: Path,
) -> dict:
    """在共享预处理矩阵上训练手写模型并保存统一评估产物。"""
    model = _build_manual_model(model_name, config)
    started = perf_counter()
    model.fit(
        prepared.transformed_train,
        prepared.train_labels,
        prepared.transformed_validation,
        prepared.validation_labels,
    )
    training_time = perf_counter() - started
    validation_predictions = model.predict(prepared.transformed_validation)
    started = perf_counter()
    test_predictions = model.predict(prepared.transformed_test)
    inference_time = perf_counter() - started
    class_names = prepared.label_encoder.classes_.tolist()
    parameters = dict(config["training"][model_name])
    result = {
        "model_name": model_name,
        "display_name": MODEL_DISPLAY_NAMES[model_name],
        "parameters": parameters,
        "parameters_json": json.dumps(parameters, ensure_ascii=False, indent=2),
        "selection_metric": "validation_cross_entropy_early_stopping",
        "selection_reason": "固定课程配置，并使用验证损失早停；测试集未参与训练",
        "candidate_results": [],
        "validation_metrics": evaluate_predictions(
            prepared.validation_labels, validation_predictions, class_names
        ),
        "test_metrics": evaluate_predictions(
            prepared.test_labels, test_predictions, class_names
        ),
        "training_time_seconds": training_time,
        "inference_time_seconds": inference_time,
        "epochs_trained": len(model.train_loss_history),
        "class_names": class_names,
    }
    models_dir.mkdir(parents=True, exist_ok=True)
    model.save(models_dir / f"{model_name}.npz")
    joblib.dump(
        {
            "model_name": model_name,
            "mode": "manual",
            "model": model,
            "preprocessor": prepared.preprocessor,
            "label_encoder": prepared.label_encoder,
            **prepared.input_metadata,
        },
        models_dir / f"{model_name}.joblib",
    )
    save_loss_curve(
        model.train_loss_history,
        model.validation_loss_history,
        metrics_dir / f"{model_name}_loss_curve.png",
        f"{model_name} - Loss",
    )
    save_evaluation_artifacts(result, class_names, metrics_dir)
    return result


def train_sklearn_models(
    prepared: PreparedData,
    config: dict,
    models_dir: Path,
    metrics_dir: Path,
    selected_model: str | None = None,
) -> list[dict]:
    """训练逻辑回归和神经网络，或仅训练指定模型。"""
    names = ["sklearn_logistic", "sklearn_mlp"]
    if selected_model:
        aliases = {"logistic": "sklearn_logistic", "mlp": "sklearn_mlp"}
        if selected_model not in aliases:
            raise ValueError("sklearn --model 仅支持 logistic 或 mlp")
        names = [aliases[selected_model]]
    return [
        train_sklearn_model(name, prepared, config, models_dir, metrics_dir)
        for name in names
    ]


def train_manual_models(
    prepared: PreparedData,
    config: dict,
    models_dir: Path,
    metrics_dir: Path,
    selected_model: str | None = None,
) -> list[dict]:
    """训练手写逻辑回归和神经网络，或仅训练指定模型。"""
    names = ["manual_logistic", "manual_mlp"]
    if selected_model:
        aliases = {"logistic": "manual_logistic", "mlp": "manual_mlp"}
        if selected_model not in aliases:
            raise ValueError("manual --model 仅支持 logistic 或 mlp")
        names = [aliases[selected_model]]
    return [
        train_manual_model(name, prepared, config, models_dir, metrics_dir)
        for name in names
    ]
