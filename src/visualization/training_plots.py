from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "codex-matplotlib-cache"))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc, confusion_matrix, roc_curve
from sklearn.preprocessing import label_binarize

from src.utils.file_utils import ensure_directory

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 统一保存图像的函数
def save_figure(path: str | Path) -> None:
    # 统一保存图像并关闭画布
    target_path = Path(path)
    ensure_directory(target_path.parent)
    plt.tight_layout()
    plt.savefig(target_path, dpi=160, bbox_inches="tight")
    plt.close()

# 保存训练曲线
def save_training_curve(history: List[Dict[str, Any]], output_path: str | Path, title: str) -> None:
    # 绘制训练损失和验证指标曲线
    if not history:
        return
    epochs = [int(item["epoch"]) for item in history]
    train_loss = [float(item.get("train_loss", 0.0)) for item in history]
    validation_loss = [item.get("validation_loss") for item in history]
    validation_f1 = [item.get("validation_macro_f1") for item in history]

    plt.figure(figsize=(10, 5))
    plt.plot(epochs, train_loss, label="训练损失", linewidth=2)
    if any(value is not None for value in validation_loss):
        plt.plot(epochs, [float(value) if value is not None else np.nan for value in validation_loss], label="验证损失", linewidth=2)
    if any(value is not None for value in validation_f1):
        plt.plot(epochs, [float(value) if value is not None else np.nan for value in validation_f1], label="验证 Macro F1", linewidth=2)
    plt.title(title)
    plt.xlabel("Epoch")
    plt.ylabel("指标值")
    plt.grid(alpha=0.3)
    plt.legend()
    save_figure(output_path)

# 保存参数搜索进度
def save_search_progress(search_history: List[Dict[str, Any]], output_path: str | Path, title: str) -> None:
    # 绘制参数搜索过程
    if not search_history:
        return
    steps = [int(item["step"]) for item in search_history]
    macro_f1 = [float(item["validation_macro_f1"]) for item in search_history]
    best_so_far = np.maximum.accumulate(np.asarray(macro_f1, dtype=float))

    plt.figure(figsize=(10, 5))
    plt.plot(steps, macro_f1, marker="o", label="当前参数组合验证 Macro F1")
    plt.plot(steps, best_so_far, linestyle="--", linewidth=2, label="当前最优 Macro F1")
    plt.title(title)
    plt.xlabel("参数组合序号")
    plt.ylabel("Macro F1")
    plt.grid(alpha=0.3)
    plt.legend()
    save_figure(output_path)

# 保存混淆矩阵
def save_confusion_matrix(
    matrix_or_y_true: List[List[int]] | np.ndarray,
    predictions_or_class_names: List[int] | List[str] | np.ndarray,
    class_names_or_output_path: List[str] | str | Path,
    output_path_or_title: str | Path,
    title: str | None = None,
) -> None:
    # 支持直接传入混淆矩阵或原始标签
    if title is None:
        matrix = np.asarray(matrix_or_y_true, dtype=float)
        class_names = predictions_or_class_names  # type: ignore[assignment]
        output_path = class_names_or_output_path  # type: ignore[assignment]
        chart_title = output_path_or_title
    else:
        matrix = confusion_matrix(np.asarray(matrix_or_y_true), np.asarray(predictions_or_class_names)).astype(float)
        class_names = class_names_or_output_path  # type: ignore[assignment]
        output_path = output_path_or_title
        chart_title = title

    plt.figure(figsize=(9, 7))
    plt.imshow(matrix, cmap="Blues")
    plt.title(chart_title)
    plt.xlabel("预测类别")
    plt.ylabel("真实类别")
    plt.xticks(range(len(class_names)), class_names, rotation=45, ha="right")
    plt.yticks(range(len(class_names)), class_names)
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            plt.text(col_index, row_index, int(matrix[row_index, col_index]), ha="center", va="center", color="black")
    plt.colorbar(fraction=0.046, pad=0.04)
    save_figure(output_path)

# 保存多分类 ROC 曲线
def save_multiclass_roc_curve(y_true: np.ndarray, probabilities: np.ndarray, class_names: List[str], output_path: str | Path, title: str) -> None:
    # 绘制多分类 ROC 曲线
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        return
    y_binary = label_binarize(y_true, classes=list(range(len(class_names))))
    plt.figure(figsize=(10, 7))
    for class_index, class_name in enumerate(class_names):
        false_positive_rate, true_positive_rate, _ = roc_curve(y_binary[:, class_index], probabilities[:, class_index])
        roc_auc = auc(false_positive_rate, true_positive_rate)
        plt.plot(false_positive_rate, true_positive_rate, linewidth=2, label=f"{class_name} (AUC={roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.title(title)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.grid(alpha=0.3)
    plt.legend(fontsize=8)
    save_figure(output_path)

# 保存指标对比图
def save_metric_comparison(model_results: Dict[str, Any] | List[Dict[str, Any]], output_path: str | Path, title: str) -> None:
    # 将模型结果统一转成交叉对比图数据
    if isinstance(model_results, list):
        rows = model_results
    else:
        optimized_results = model_results["optimized"]
        rows = []
        for model_name, result in optimized_results.items():
            rows.append({"name": model_name, "metrics": result["test_metrics"]})
    save_named_metric_bars(rows, output_path, title)

# 保存命名指标柱状图
def save_named_metric_bars(rows: List[Dict[str, Any]], output_path: str | Path, title: str) -> None:
    # 按模型对比多个指标柱状图
    if not rows:
        return
    metric_names = ["accuracy", "macro_precision", "macro_recall", "macro_f1"]
    x_axis = np.arange(len(metric_names))
    bar_width = max(0.18, min(0.8 / max(len(rows), 1), 0.32))

    plt.figure(figsize=(11, 6))
    start_offset = -((len(rows) - 1) * bar_width / 2)
    for index, row in enumerate(rows):
        metrics = row["metrics"]
        values = [float(metrics[metric_name]) for metric_name in metric_names]
        plt.bar(x_axis + start_offset + index * bar_width, values, width=bar_width, label=row["name"])

    plt.title(title)
    plt.xlabel("指标")
    plt.ylabel("分数")
    plt.xticks(x_axis, ["Accuracy", "Macro Precision", "Macro Recall", "Macro F1"])
    plt.ylim(0.0, 1.05)
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    save_figure(output_path)
