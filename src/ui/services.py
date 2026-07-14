import copy
import json
import shutil
from pathlib import Path
from time import perf_counter

import joblib
import pandas as pd

from application.workflows import load_workflow_context, prepare_workflow_data
from core.io import write_json
from data.loader import load_csv_readonly
from model.predictor import load_predictor
from model.training import train_manual_model, train_sklearn_model
from ui.constants import MODEL_INFO


# 读取 JSON 产物，并将缺失或损坏转换为简洁错误。
def read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"缺少界面所需产物：{path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"产物无法读取：{path.name}") from error


# 将项目内路径转换为适合界面展示的相对路径。
def project_relative_path(path: Path, project_root: Path | None = None) -> str:
    root = project_root or Path(__file__).resolve().parents[2]
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


# 读取指定模型的完整评估结果。
def load_model_metrics(model_name: str, paths: dict[str, Path] | None = None) -> dict:
    if model_name not in MODEL_INFO:
        raise ValueError("不支持的模型名称")
    if paths is None:
        _, paths = load_workflow_context()
    return read_json(paths["metrics_dir"] / f"{model_name}_metrics.json")


# 汇总首页所需的真实数据、活动模型和四模型指标。
def load_dashboard_data() -> dict:
    config, paths = load_workflow_context()
    frame = load_csv_readonly(paths["raw_data"])
    active = read_json(paths["models_dir"] / "best_model.json")
    comparison = [
        load_model_metrics(model_name, paths)
        for model_name in MODEL_INFO
        if (paths["metrics_dir"] / f"{model_name}_metrics.json").is_file()
    ]
    target = config["data"]["target"]
    feature_count = len(config["data"]["numeric_columns"]) + len(
        config["data"]["categorical_columns"]
    )
    return {
        "sample_count": int(len(frame)),
        "feature_count": feature_count,
        "class_count": int(frame[target].nunique()),
        "active_model": active["model_name"],
        "active_metadata": active,
        "active_metrics": load_model_metrics(active["model_name"], paths),
        "comparison": comparison,
        "data_updated_at": paths["raw_data"].stat().st_mtime,
        "model_updated_at": (paths["models_dir"] / "best_model.joblib").stat().st_mtime,
    }


# 从只读真实 CSV 读取一条完整输入，供示例按钮使用。
def load_example_sample(row_index: int = 0) -> dict:
    config, paths = load_workflow_context()
    frame = load_csv_readonly(paths["raw_data"])
    input_columns = list(config["data"]["numeric_columns"]) + list(
        config["data"]["categorical_columns"]
    )
    if row_index < 0 or row_index >= len(frame):
        raise ValueError("示例行索引超出数据范围")
    return frame.loc[frame.index[row_index], input_columns].to_dict()


# 载入当前活动模型并完成单条预测与真实耗时测量。
def predict_sample(sample: dict) -> dict:
    _, paths = load_workflow_context()
    predictor = load_predictor(paths["models_dir"] / "best_model.joblib")
    started = perf_counter()
    result = predictor.predict_single(sample)
    result["elapsed_ms"] = (perf_counter() - started) * 1000
    result["implementation"] = MODEL_INFO[result["model_name"]]["implementation"]
    return result


# 返回活动模型 bundle 中的输入字段、范围和类别选项。
def load_input_metadata() -> dict:
    _, paths = load_workflow_context()
    model_path = paths["models_dir"] / "best_model.joblib"
    if not model_path.is_file():
        raise FileNotFoundError("活动模型文件不存在，请先完成训练并应用模型")
    bundle = joblib.load(model_path)
    keys = (
        "input_columns",
        "numeric_columns",
        "categorical_columns",
        "numeric_ranges",
        "categorical_options",
    )
    if not isinstance(bundle, dict) or any(key not in bundle for key in keys):
        raise ValueError("活动模型缺少输入字段元数据")
    return {key: bundle[key] for key in keys}


# 使用界面参数训练单个模型，并保留现有无泄漏划分与评估流程。
def train_selected_model(model_name: str, parameters: dict) -> dict:
    if model_name not in MODEL_INFO:
        raise ValueError("不支持的训练模型")
    config, paths = load_workflow_context()
    runtime_config = copy.deepcopy(config)
    if model_name == "sklearn_logistic":
        candidate = {
            "C": float(parameters["C"]),
            "class_weight": parameters["class_weight"],
            "solver": "lbfgs",
        }
        runtime_config["training"][model_name]["max_iter"] = int(parameters["max_iter"])
        runtime_config["training"][model_name]["candidates"] = [candidate]
    elif model_name == "sklearn_mlp":
        candidate = {
            "hidden_layer_sizes": tuple(parameters["hidden_layer_sizes"]),
            "activation": parameters["activation"],
            "alpha": float(parameters["alpha"]),
            "learning_rate_init": float(parameters["learning_rate_init"]),
        }
        runtime_config["training"][model_name]["max_iter"] = int(parameters["max_iter"])
        runtime_config["training"][model_name]["candidates"] = [candidate]
    else:
        runtime_config["training"][model_name].update(parameters)
    _, _, prepared = prepare_workflow_data(runtime_config, paths)
    if model_name.startswith("sklearn_"):
        return train_sklearn_model(
            model_name, prepared, runtime_config, paths["models_dir"], paths["metrics_dir"]
        )
    return train_manual_model(
        model_name, prepared, runtime_config, paths["models_dir"], paths["metrics_dir"]
    )


# 经用户明确操作后复制指定模型，并更新活动模型元数据。
def activate_model(model_name: str, paths: dict[str, Path] | None = None) -> dict:
    if model_name not in MODEL_INFO:
        raise ValueError("不支持的活动模型")
    if paths is None:
        _, paths = load_workflow_context()
    source = paths["models_dir"] / f"{model_name}.joblib"
    if not source.is_file():
        raise FileNotFoundError("所选模型文件不存在，请先完成该模型训练")
    metrics = load_model_metrics(model_name, paths)
    destination = paths["models_dir"] / "best_model.joblib"
    shutil.copyfile(source, destination)
    metadata = {
        "model_name": model_name,
        "path": destination.name,
        "selection_metric": "user_explicit_activation",
        "validation_macro_f1": float(metrics["validation_metrics"]["macro_f1"]),
        "test_set_used_for_selection": False,
    }
    write_json(paths["models_dir"] / "best_model.json", metadata)
    return metadata


# 将分类报告字典整理为适合界面表格展示的数据框。
def classification_report_frame(metrics: dict) -> pd.DataFrame:
    report = metrics["test_metrics"]["classification_report"]
    rows = []
    for label, values in report.items():
        if isinstance(values, dict):
            rows.append({"类别": label, **values})
    return pd.DataFrame(rows)
