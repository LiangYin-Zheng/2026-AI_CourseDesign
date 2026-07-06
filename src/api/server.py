from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.config import load_project_config
from src.data_processing.cleaner import clean_dataset
from src.features.preprocessor import TabularPreprocessor
from src.models.logistic_regression import SoftmaxLogisticRegression
from src.models.neural_network import SimpleNeuralNetwork
from src.models.sklearn_trainer import load_pickle
from src.models.trainer import load_model_state
from src.ui.templates import build_index_page
from src.utils.file_utils import read_json


# 加载 sklearn 推理模型

def load_sklearn_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    sklearn_model_dir = Path(config["output_dirs"]["models"]) / "sklearn"
    logistic_bundle = load_pickle(sklearn_model_dir / "logistic_regression.pkl")
    mlp_bundle = load_pickle(sklearn_model_dir / "mlp_classifier.pkl")
    best_model_bundle = load_pickle(sklearn_model_dir / "best_model.pkl")
    return {
        "logistic_regression": logistic_bundle,
        "mlp_classifier": mlp_bundle,
        "best_model_name": best_model_bundle["name"],
    }


# 尝试加载手搓模型，便于后续对照展示

def load_manual_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any] | None:
    model_dir = Path(config["output_dirs"]["models"])
    preprocessor_path = model_dir / "preprocessor.json"
    logistic_path = model_dir / "logistic_regression_model.npz"
    neural_path = model_dir / "neural_network_model.npz"
    if not (preprocessor_path.exists() and logistic_path.exists() and neural_path.exists()):
        return None
    preprocessor = TabularPreprocessor.from_dict(read_json(preprocessor_path))
    logistic_state = load_model_state(logistic_path)
    neural_state = load_model_state(neural_path)
    return {
        "preprocessor": preprocessor,
        "logistic_regression": SoftmaxLogisticRegression.from_state(logistic_state),
        "neural_network": SimpleNeuralNetwork.from_state(neural_state),
    }


# 加载默认推理模型与预处理器

def load_inference_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sklearn": load_sklearn_inference_bundle(config),
        "manual": load_manual_inference_bundle(config),
    }


# 使用 sklearn 模型执行单样本预测

def predict_with_sklearn(payload: Dict[str, Any], config: Dict[str, Any], sklearn_bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw_frame = pd.DataFrame([payload])
    raw_frame[config["raw_target_column"]] = "Normal_Weight"
    prepared_frame = clean_dataset(raw_frame, config)

    prediction_result: Dict[str, Any] = {}
    for model_name in ["logistic_regression", "mlp_classifier"]:
        bundle = sklearn_bundle[model_name]
        feature_frame = prepared_frame[bundle["feature_columns"]].copy()
        transformed_features = bundle["preprocessor"].transform(feature_frame)
        probabilities = bundle["classifier"].predict_proba(transformed_features)[0]
        prediction_index = int(np.argmax(probabilities))
        class_names = bundle["class_names"]
        prediction_result[model_name] = {
            "prediction": class_names[prediction_index],
            "probabilities": {class_name: round(float(probability), 6) for class_name, probability in zip(class_names, probabilities)},
        }

    recommended_model_name = sklearn_bundle["best_model_name"]
    prediction_result["recommended_result"] = prediction_result[recommended_model_name]["prediction"]
    prediction_result["recommended_model"] = recommended_model_name
    return prediction_result


# 使用手搓模型执行单样本预测

def predict_with_manual(payload: Dict[str, Any], config: Dict[str, Any], manual_bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw_frame = pd.DataFrame([payload])
    raw_frame[config["raw_target_column"]] = "Normal_Weight"
    prepared_frame = clean_dataset(raw_frame, config)
    feature_frame = prepared_frame.drop(columns=[config["target_column"]], errors="ignore")

    preprocessor: TabularPreprocessor = manual_bundle["preprocessor"]
    X = preprocessor.transform(feature_frame)
    logistic_model: SoftmaxLogisticRegression = manual_bundle["logistic_regression"]
    neural_model: SimpleNeuralNetwork = manual_bundle["neural_network"]

    logistic_probabilities = logistic_model.predict_proba(X)
    neural_probabilities = neural_model.predict_proba(X)
    logistic_prediction = preprocessor.decode_target(np.argmax(logistic_probabilities, axis=1))[0]
    neural_prediction = preprocessor.decode_target(np.argmax(neural_probabilities, axis=1))[0]

    return {
        "logistic_regression": {
            "prediction": logistic_prediction,
            "probabilities": preprocessor.probabilities_to_dict(logistic_probabilities)[0],
        },
        "neural_network": {
            "prediction": neural_prediction,
            "probabilities": preprocessor.probabilities_to_dict(neural_probabilities)[0],
        },
    }


# 对外提供单样本预测能力

def predict_single(payload: Dict[str, Any], config: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"success": True}
    result["sklearn"] = predict_with_sklearn(payload, config, bundle["sklearn"])
    if bundle.get("manual") is not None:
        result["manual"] = predict_with_manual(payload, config, bundle["manual"])
    return result


# 创建可复用的 HTTP 请求处理器

def create_request_handler(config: Dict[str, Any], bundle: Dict[str, Any]) -> type[BaseHTTPRequestHandler]:
    class PredictionHandler(BaseHTTPRequestHandler):
        # 返回统一 JSON 响应
        def send_json(self, payload: Dict[str, Any], status_code: int = 200) -> None:
            response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        # 返回 HTML 页面
        def send_html(self, html_content: str) -> None:
            body = html_content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # 处理 GET 请求
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                self.send_html(build_index_page())
                return
            if self.path == "/health":
                self.send_json({"success": True, "message": "service is running"})
                return
            self.send_json({"success": False, "message": "未找到请求资源"}, status_code=404)

        # 处理 POST 请求
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/v1/predict":
                self.send_json({"success": False, "message": "未找到请求资源"}, status_code=404)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            request_body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(request_body)
                result = predict_single(payload, config, bundle)
                self.send_json(result)
            except Exception as error:  # noqa: BLE001
                self.send_json({"success": False, "message": f"预测失败：{error}"}, status_code=400)

        # 关闭默认访问日志，避免演示界面输出过杂
        def log_message(self, format_string: str, *args: Any) -> None:
            return

    return PredictionHandler


# 启动本地 HTTP 演示服务

def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    config = load_project_config()
    bundle = load_inference_bundle(config)
    handler = create_request_handler(config, bundle)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"服务已启动：http://{host}:{port}")
    server.serve_forever()
