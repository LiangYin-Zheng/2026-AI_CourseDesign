from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.evaluation.metrics import evaluate_predictions
from src.features.preprocessor import TabularPreprocessor
from src.models.logistic_regression import SoftmaxLogisticRegression
from src.models.neural_network import SimpleNeuralNetwork
from src.utils.file_utils import write_json


# 将模型状态写入 NPZ 文件，便于后续服务加载

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


# 从 NPZ 文件恢复模型状态字典

def load_model_state(model_path: str | Path) -> Dict[str, Any]:
    state: Dict[str, Any] = {}
    with np.load(model_path, allow_pickle=True) as data:
        for key in data.files:
            value = data[key]
            if value.shape == ():
                state[key] = value.item()
            else:
                state[key] = value
    return state


# 构建逻辑回归模型实例

def build_logistic_model(parameters: Dict[str, Any], random_seed: int) -> SoftmaxLogisticRegression:
    return SoftmaxLogisticRegression(
        learning_rate=float(parameters["learning_rate"]),
        epochs=int(parameters["epochs"]),
        reg_strength=float(parameters["reg_strength"]),
        random_seed=random_seed,
    )


# 构建神经网络模型实例

def build_neural_network_model(parameters: Dict[str, Any], random_seed: int) -> SimpleNeuralNetwork:
    return SimpleNeuralNetwork(
        hidden_units=int(parameters["hidden_units"]),
        learning_rate=float(parameters["learning_rate"]),
        epochs=int(parameters["epochs"]),
        l2_strength=float(parameters["l2_strength"]),
        random_seed=random_seed,
    )


# 使用验证集评估候选参数组合

def tune_model(
    model_name: str,
    parameter_grid: Dict[str, list[Any]],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    random_seed: int,
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    best_parameters: Dict[str, Any] | None = None
    best_metrics: Dict[str, float] | None = None

    parameter_names = list(parameter_grid.keys())
    for parameter_values in product(*(parameter_grid[name] for name in parameter_names)):
        candidate_parameters = dict(zip(parameter_names, parameter_values))
        if model_name == "logistic_regression":
            model = build_logistic_model(candidate_parameters, random_seed)
        else:
            model = build_neural_network_model(candidate_parameters, random_seed)

        model.fit(X_train, y_train, X_validation, y_validation)
        predictions = model.predict(X_validation)
        metrics = evaluate_predictions(y_validation, predictions)
        if best_metrics is None or metrics["macro_f1"] > best_metrics["macro_f1"]:
            best_parameters = candidate_parameters
            best_metrics = metrics

    if best_parameters is None or best_metrics is None:
        raise ValueError("参数调优失败，未获得有效模型。")
    return best_parameters, best_metrics


# 训练、评估并保存全部模型产物

def train_all_models(
    datasets: Dict[str, pd.DataFrame],
    preprocessor: TabularPreprocessor,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    target_column = config["target_column"]
    random_seed = int(config["random_seed"])
    model_output_dir = Path(config["output_dirs"]["models"])
    evaluation_output_dir = Path(config["output_dirs"]["evaluation"])
    prediction_output_dir = Path(config["output_dirs"]["predictions"])

    X_train = preprocessor.transform(datasets["train"])
    y_train = preprocessor.encode_target(datasets["train"][target_column])
    X_validation = preprocessor.transform(datasets["validation"])
    y_validation = preprocessor.encode_target(datasets["validation"][target_column])
    X_test = preprocessor.transform(datasets["test"])
    y_test = preprocessor.encode_target(datasets["test"][target_column])

    baseline_logistic_parameters = config["baseline_models"]["logistic_regression"]
    baseline_logistic_model = build_logistic_model(baseline_logistic_parameters, random_seed)
    baseline_logistic_model.fit(X_train, y_train, X_validation, y_validation)
    baseline_logistic_metrics = evaluate_predictions(y_test, baseline_logistic_model.predict(X_test))

    best_logistic_parameters, logistic_validation_metrics = tune_model(
        "logistic_regression",
        config["optimization_grids"]["logistic_regression"],
        X_train,
        y_train,
        X_validation,
        y_validation,
        random_seed,
    )
    best_logistic_model = build_logistic_model(best_logistic_parameters, random_seed)
    best_logistic_model.fit(X_train, y_train, X_validation, y_validation)
    logistic_test_predictions = best_logistic_model.predict(X_test)
    logistic_test_probabilities = best_logistic_model.predict_proba(X_test)
    optimized_logistic_metrics = evaluate_predictions(y_test, logistic_test_predictions)

    baseline_neural_parameters = config["baseline_models"]["neural_network"]
    baseline_neural_model = build_neural_network_model(baseline_neural_parameters, random_seed)
    baseline_neural_model.fit(X_train, y_train, X_validation, y_validation)
    baseline_neural_metrics = evaluate_predictions(y_test, baseline_neural_model.predict(X_test))

    best_neural_parameters, neural_validation_metrics = tune_model(
        "neural_network",
        config["optimization_grids"]["neural_network"],
        X_train,
        y_train,
        X_validation,
        y_validation,
        random_seed,
    )
    best_neural_model = build_neural_network_model(best_neural_parameters, random_seed)
    best_neural_model.fit(X_train, y_train, X_validation, y_validation)
    neural_test_predictions = best_neural_model.predict(X_test)
    neural_test_probabilities = best_neural_model.predict_proba(X_test)
    optimized_neural_metrics = evaluate_predictions(y_test, neural_test_predictions)

    model_results = {
        "baseline": {
            "logistic_regression": {
                "parameters": baseline_logistic_parameters,
                "test_metrics": baseline_logistic_metrics,
            },
            "neural_network": {
                "parameters": baseline_neural_parameters,
                "test_metrics": baseline_neural_metrics,
            },
        },
        "optimized": {
            "logistic_regression": {
                "parameters": best_logistic_parameters,
                "validation_metrics": logistic_validation_metrics,
                "test_metrics": optimized_logistic_metrics,
            },
            "neural_network": {
                "parameters": best_neural_parameters,
                "validation_metrics": neural_validation_metrics,
                "test_metrics": optimized_neural_metrics,
            },
        },
    }

    save_model_state(model_output_dir / "logistic_regression_model.npz", best_logistic_model.to_state())
    save_model_state(model_output_dir / "neural_network_model.npz", best_neural_model.to_state())
    write_json(model_output_dir / "preprocessor.json", preprocessor.to_dict())
    write_json(evaluation_output_dir / "model_results.json", model_results)

    prediction_frame = pd.DataFrame(
        {
            "actual_label": preprocessor.decode_target(y_test),
            "logistic_prediction": preprocessor.decode_target(logistic_test_predictions),
            "neural_prediction": preprocessor.decode_target(neural_test_predictions),
        }
    )
    prediction_frame.to_csv(prediction_output_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")

    return {
        "model_results": model_results,
        "best_models": {
            "logistic_regression": best_logistic_model,
            "neural_network": best_neural_model,
        },
        "test_sets": {
            "X_test": X_test,
            "y_test": y_test,
            "logistic_probabilities": logistic_test_probabilities,
            "neural_probabilities": neural_test_probabilities,
            "logistic_predictions": logistic_test_predictions,
            "neural_predictions": neural_test_predictions,
        },
    }
