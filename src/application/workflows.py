import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from core.config import load_config
from core.io import write_json, write_text
from core.paths import get_project_paths, get_project_root
from core.schema import DatasetSchema, build_schema
from data.audit import audit_dataframe
from data.eda import run_eda
from data.loader import DataLoadError, load_csv_readonly, snapshot_file
from data.preparation import (
    PreparedData,
    clean_dataframe,
    prepare_dataframe,
    save_prepared_artifacts,
)
from evaluation.reports import write_audit_reports
from model.training import train_manual_models, train_sklearn_models

MODEL_NAMES = (
    "sklearn_logistic",
    "sklearn_mlp",
    "manual_logistic",
    "manual_mlp",
)


def load_workflow_context(
    config_path: Path | None = None,
) -> tuple[dict, dict[str, Path]]:
    # 返回工作流共享的配置和已校验路径。
    project_root = get_project_root()
    selected_path = config_path or project_root / "config" / "default.yaml"
    if not selected_path.is_absolute():
        selected_path = project_root / selected_path
    config = load_config(selected_path.resolve())
    return config, get_project_paths(project_root, config)


def run_audit_workflow(config: dict, paths: dict[str, Path]) -> dict[str, Path]:
    # 生成 JSON 和 Markdown 数据审查报告。
    before = snapshot_file(paths["raw_data"])
    frame = load_csv_readonly(paths["raw_data"])
    result = audit_dataframe(
        frame,
        build_schema(config),
        imbalance_ratio_warning=float(config["audit"]["imbalance_ratio_warning"]),
    )
    after = snapshot_file(paths["raw_data"])
    if before != after:
        raise DataLoadError("原始 CSV 在审查过程中发生变化，已停止输出报告")
    result["file_snapshot"] = before
    return write_audit_reports(result, paths["audit_report_dir"], paths["raw_data"])


def prepare_workflow_data(
    config: dict, paths: dict[str, Path]
) -> tuple[pd.DataFrame, DatasetSchema, PreparedData]:
    # 清洗、分层划分和预处理真实数据，并保存准备产物。
    before = snapshot_file(paths["raw_data"])
    frame = load_csv_readonly(paths["raw_data"])
    schema = build_schema(config)
    prepared = prepare_dataframe(frame, schema, config)
    save_prepared_artifacts(prepared, paths["processed_dir"])
    if snapshot_file(paths["raw_data"]) != before:
        raise DataLoadError("原始 CSV 在数据准备过程中发生变化")
    cleaned, _ = clean_dataframe(frame, schema)
    return cleaned, schema, prepared


def build_model_comparison(paths: dict[str, Path]) -> tuple[pd.DataFrame, dict]:
    # 生成测试集展示排名，并按验证集指标选择部署模型。
    results = []
    for model_name in MODEL_NAMES:
        metric_path = paths["metrics_dir"] / f"{model_name}_metrics.json"
        if not metric_path.is_file():
            raise FileNotFoundError(f"缺少模型指标文件：{metric_path.name}")
        results.append(json.loads(metric_path.read_text(encoding="utf-8")))
    rows = []
    for result in results:
        test_metrics = result["test_metrics"]
        validation_metrics = result["validation_metrics"]
        rows.append(
            {
                "model_name": result["model_name"],
                "display_name": result["display_name"],
                "validation_accuracy": validation_metrics["accuracy"],
                "validation_macro_f1": validation_metrics["macro_f1"],
                "accuracy": test_metrics["accuracy"],
                "macro_precision": test_metrics["macro_precision"],
                "macro_recall": test_metrics["macro_recall"],
                "macro_f1": test_metrics["macro_f1"],
                "weighted_f1": test_metrics["weighted_f1"],
                "training_time_seconds": result["training_time_seconds"],
                "inference_time_seconds": result["inference_time_seconds"],
            }
        )
    model_order = {name: index for index, name in enumerate(MODEL_NAMES)}
    selected_result = min(
        results,
        key=lambda result: (
            -float(result["validation_metrics"]["macro_f1"]),
            -float(result["validation_metrics"]["accuracy"]),
            float(result["training_time_seconds"]),
            model_order[result["model_name"]],
        ),
    )
    selected_name = selected_result["model_name"]
    comparison = (
        pd.DataFrame(rows)
        .sort_values(
            ["macro_f1", "accuracy", "model_name"], ascending=[False, False, True]
        )
        .reset_index(drop=True)
    )
    comparison.insert(0, "rank", np.arange(1, len(comparison) + 1))
    comparison["selected_for_deployment"] = comparison["model_name"].eq(selected_name)
    paths["metrics_dir"].mkdir(parents=True, exist_ok=True)
    comparison.to_csv(paths["metrics_dir"] / "model_comparison.csv", index=False)
    tie_breakers = [
        "validation_accuracy",
        "training_time_seconds",
        "fixed_model_order",
    ]
    summary = {
        "deployment_selection_metric": "validation_macro_f1",
        "deployment_tie_breakers": tie_breakers,
        "selected_model": selected_name,
        "selected_validation_macro_f1": float(
            selected_result["validation_metrics"]["macro_f1"]
        ),
        "selection_reason": "按验证集 macro F1 选择；测试集仅用于最终评估展示",
        "test_ranking_metric": "test_macro_f1",
        "test_ranking": comparison.to_dict(orient="records"),
    }
    write_json(paths["metrics_dir"] / "model_comparison.json", summary)
    source_model = paths["models_dir"] / f"{selected_name}.joblib"
    best_model = paths["models_dir"] / "best_model.joblib"
    shutil.copyfile(source_model, best_model)
    write_json(
        paths["models_dir"] / "best_model.json",
        {
            "model_name": selected_name,
            "path": "best_model.joblib",
            "selection_metric": "validation_macro_f1",
            "validation_macro_f1": float(
                selected_result["validation_metrics"]["macro_f1"]
            ),
            "tie_breakers": tie_breakers,
            "test_set_used_for_selection": False,
        },
    )
    return comparison, summary


# 找出混淆矩阵中最多的非对角误分类
def _largest_confusion(result: dict) -> dict:
    matrix = np.asarray(result["test_metrics"]["confusion_matrix"])
    without_diagonal = matrix.copy()
    np.fill_diagonal(without_diagonal, 0)
    row, column = np.unravel_index(np.argmax(without_diagonal), without_diagonal.shape)
    classes = result["class_names"]
    return {
        "true_class": classes[int(row)],
        "predicted_class": classes[int(column)],
        "count": int(without_diagonal[row, column]),
    }


def write_experiment_summary(paths: dict[str, Path], comparison_summary: dict) -> Path:
    # 根据真实审查、EDA 和模型指标生成 Markdown 实验总结。
    audit = json.loads(
        (paths["audit_report_dir"] / "data_audit.json").read_text(encoding="utf-8")
    )
    split = json.loads(
        (paths["processed_dir"] / "split_summary.json").read_text(encoding="utf-8")
    )
    eda = json.loads(
        (paths["figures_dir"].parent / "eda_summary.json").read_text(encoding="utf-8")
    )
    results = {
        name: json.loads(
            (paths["metrics_dir"] / f"{name}_metrics.json").read_text(encoding="utf-8")
        )
        for name in MODEL_NAMES
    }
    selected_name = comparison_summary["selected_model"]
    test_leader_name = comparison_summary["test_ranking"][0]["model_name"]
    confusion = _largest_confusion(results[selected_name])
    table_lines = [
        "| 模型 | Accuracy | Macro Precision | Macro Recall | Macro F1 | 训练秒数 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model in comparison_summary["test_ranking"]:
        table_lines.append(
            f"| {model['display_name']} | {model['accuracy']:.6f} | "
            f"{model['macro_precision']:.6f} | {model['macro_recall']:.6f} | "
            f"{model['macro_f1']:.6f} | {model['training_time_seconds']:.6f} |"
        )
    ranges = eda["key_group_mean_ranges"]
    key_feature = max(ranges, key=ranges.get)
    binning = split["preprocessing"]["numeric_binning"]
    binning_description = ""
    if binning["enabled"]:
        binning_description = (
            f"并行增加仅在训练集拟合的 {binning['n_bins']} 箱 "
            f"{binning['strategy']} 数值分箱独热特征；"
        )
    lines = [
        "# 非 UI 核心实验总结",
        "",
        "## 1. 数据集概况与质量",
        "",
        f"原始数据共 {audit['dataset_summary']['row_count']} 行、{audit['dataset_summary']['column_count']} 列，目标字段包含 {audit['target_summary']['class_count']} 类。缺失单元格 {audit['missing_summary']['total_missing']} 个，完全重复行 {audit['duplicate_summary']['duplicate_row_count']} 行。原始 CSV SHA-256 为 `{audit['file_snapshot']['sha256']}`。",
        "",
        "## 2. 清洗、预处理与划分",
        "",
        f"{split['cleaning']['rule']}。BMI 未加入模型：{split['cleaning']['bmi_reason']}。数值列使用训练集 median 填补并标准化，{binning_description}类别列使用训练集众数填补与未知类别安全独热编码。训练/验证/测试样本数分别为 {split['splits']['train']['sample_count']}、{split['splits']['validation']['sample_count']}、{split['splits']['test']['sample_count']}，三者按目标分层且索引互斥。",
        "",
        "## 3. EDA 主要结论",
        "",
        f"Age、Height、Weight 的目标组均值跨度中 `{key_feature}` 最大（{ranges[key_feature]:.6f}）。图表和 `eda_summary.json` 同时保存了数值相关性、类别交叉比例及分组统计。相关性用于描述而非因果或医学结论。",
        "",
        "## 4. 四模型参数与指标",
        "",
        *table_lines,
        "",
        "各模型具体候选、最佳参数、验证指标和分类报告见 `outputs/metrics/*_metrics.json` 及对应 Markdown。sklearn 模型由验证集 macro F1 选参；手写模型使用验证损失早停。",
        "",
        "## 5. 部署模型、测试排名与误分类",
        "",
        f"部署模型为 `{selected_name}`，由验证集 macro F1 选择，验证集相同时依次比较 validation accuracy、训练时间和固定模型顺序；测试集未参与部署选择。测试集 macro F1 排名第一为 `{test_leader_name}`。部署模型在测试集最多的非对角误分类为真实 `{confusion['true_class']}` 被预测成 `{confusion['predicted_class']}`，共 {confusion['count']} 条。",
        "",
        "## 6. sklearn 与手写实现",
        "",
        "sklearn 实现使用成熟的数值优化、收敛控制和 Pipeline；NumPy 手写实现完整展示 Softmax、交叉熵、梯度/反向传播、L2、mini-batch 和早停。性能差距可能来自优化器、初始化、学习率调度、收敛判定及实现成熟度。",
        "",
        "| 模型 | 主要计算复杂度（每轮） | 优点 | 局限与适用场景 |",
        "|---|---|---|---|",
        "| sklearn 逻辑回归 | 约 O(n·d·k) | 稳定、较易解释、训练快 | 线性决策边界；适合作为可靠基线 |",
        "| sklearn MLP | 约 O(n·(d·h+h·k)) | 非线性表达和成熟优化 | 可解释性较弱；适合当前最佳预测模型 |",
        "| 手写逻辑回归 | 约 O(n·d·k) | 数学过程透明、便于教学 | 朴素全批量梯度下降收敛较慢；适合算法演示 |",
        "| 手写神经网络 | 约 O(n·(d·h+h·k)) | 展示完整前后向与 mini-batch | 优化策略较简单；适合教学和与成熟库对照 |",
        "",
        "## 7. 局限",
        "",
        "字段缩写、单位和部分 0/1 编码缺少官方说明；数据相关性不代表因果；模型仅在当前 CSV 固定划分上验证；类别有温和不均衡；未增加可能直接关联标签定义的 BMI 派生特征。预测仅用于课程演示。",
        "",
        "## 8. 后续 UI 接入",
        "",
        "使用 `load_predictor(outputs/models/best_model.joblib)` 后调用 `predict_single(sample)` 或 `predict_batch(dataframe)`，返回预测类别、全类别概率、最高概率、模型名和非医学声明。",
        "",
    ]
    return write_text(paths["reports_dir"] / "experiment_summary.md", "\n".join(lines))


def run_all(config: dict, paths: dict[str, Path]) -> dict:
    # 按审查、准备、EDA、sklearn、手写、比较顺序执行完整流程。
    before = snapshot_file(paths["raw_data"])
    audit_paths = run_audit_workflow(config, paths)
    cleaned, schema, prepared = prepare_workflow_data(config, paths)
    eda_paths = run_eda(
        cleaned,
        schema,
        paths["figures_dir"],
        paths["figures_dir"].parent,
        config["eda"],
        int(config["split"]["random_seed"]),
    )
    sklearn_results = train_sklearn_models(
        prepared, config, paths["models_dir"], paths["metrics_dir"]
    )
    manual_results = train_manual_models(
        prepared, config, paths["models_dir"], paths["metrics_dir"]
    )
    comparison, comparison_summary = build_model_comparison(paths)
    report_path = write_experiment_summary(paths, comparison_summary)
    after = snapshot_file(paths["raw_data"])
    if before != after:
        raise DataLoadError("完整流程运行前后原始 CSV 快照不一致")
    return {
        "audit": audit_paths,
        "eda": eda_paths,
        "models": sklearn_results + manual_results,
        "comparison": comparison.to_dict(orient="records"),
        "selected_model": comparison_summary["selected_model"],
        "report": report_path,
        "raw_snapshot": after,
    }
