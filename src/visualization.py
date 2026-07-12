from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

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


# 写入 SVG 文本到目标文件
def write_svg(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


# 生成条形图 SVG
def save_bar_chart(labels: Sequence[str], values: Sequence[float], title: str, output_path: str | Path) -> None:
    width, height = 960, 560
    left_margin, right_margin, top_margin, bottom_margin = 120, 40, 90, 150
    chart_width = width - left_margin - right_margin
    chart_height = height - top_margin - bottom_margin
    max_value = max(values) if values else 1
    bar_count = max(len(values), 1)
    bar_width = chart_width / bar_count * 0.72
    gap = chart_width / bar_count * 0.28

    bars = []
    for index, (label, value) in enumerate(zip(labels, values)):
        x_position = left_margin + index * (bar_width + gap) + gap / 2
        bar_height = 0 if max_value == 0 else (value / max_value) * chart_height
        y_position = top_margin + (chart_height - bar_height)
        bars.append(
            f'<rect x="{x_position:.2f}" y="{y_position:.2f}" width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" fill="#4F81BD" rx="6" />'
        )
        bars.append(
            f'<text x="{x_position + bar_width / 2:.2f}" y="{y_position - 8:.2f}" text-anchor="middle" '
            f'font-size="13" fill="#1F2937">{value:.2f}</text>'
        )
        bars.append(
            f'<text x="{x_position + bar_width / 2:.2f}" y="{height - 50}" text-anchor="end" '
            f'transform="rotate(-35 {x_position + bar_width / 2:.2f} {height - 50})" '
            f'font-size="12" fill="#374151">{escape(str(label))}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="#FFFFFF" />
    <text x="{width / 2}" y="45" text-anchor="middle" font-size="24" fill="#111827">{escape(title)}</text>
    <line x1="{left_margin}" y1="{top_margin}" x2="{left_margin}" y2="{top_margin + chart_height}" stroke="#6B7280" stroke-width="2" />
    <line x1="{left_margin}" y1="{top_margin + chart_height}" x2="{width - right_margin}" y2="{top_margin + chart_height}" stroke="#6B7280" stroke-width="2" />
    {''.join(bars)}
    </svg>'''
    write_svg(output_path, svg)


# 生成直方图 SVG
def save_histogram(values: Iterable[float], bins: int, title: str, output_path: str | Path) -> None:
    array = np.asarray(list(values), dtype=float)
    counts, edges = np.histogram(array, bins=bins)
    labels = [f"{edges[index]:.1f}-{edges[index + 1]:.1f}" for index in range(len(edges) - 1)]
    save_bar_chart(labels, counts.astype(float).tolist(), title, output_path)


# 生成热力图 SVG
def save_heatmap(matrix: np.ndarray, row_labels: Sequence[str], col_labels: Sequence[str], title: str, output_path: str | Path) -> None:
    width, height = 980, 760
    cell_size = 70
    left_margin, top_margin = 180, 140
    max_abs_value = float(np.max(np.abs(matrix))) if matrix.size else 1.0
    max_abs_value = max(max_abs_value, 1e-8)
    cells = []

    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = float(matrix[row_index, col_index])
            intensity = int(255 - abs(value) / max_abs_value * 155)
            color = f"rgb(255,{intensity},{intensity})" if value >= 0 else f"rgb({intensity},{intensity},255)"
            x_position = left_margin + col_index * cell_size
            y_position = top_margin + row_index * cell_size
            cells.append(
                f'<rect x="{x_position}" y="{y_position}" width="{cell_size}" height="{cell_size}" fill="{color}" stroke="#D1D5DB" />'
            )
            cells.append(
                f'<text x="{x_position + cell_size / 2}" y="{y_position + cell_size / 2 + 5}" text-anchor="middle" font-size="12" fill="#111827">{value:.2f}</text>'
            )

    row_text = []
    for row_index, label in enumerate(row_labels):
        y_position = top_margin + row_index * cell_size + cell_size / 2 + 5
        row_text.append(f'<text x="{left_margin - 10}" y="{y_position}" text-anchor="end" font-size="12">{escape(str(label))}</text>')

    col_text = []
    for col_index, label in enumerate(col_labels):
        x_position = left_margin + col_index * cell_size + cell_size / 2
        col_text.append(
            f'<text x="{x_position}" y="{top_margin - 15}" text-anchor="end" transform="rotate(-35 {x_position} {top_margin - 15})" font-size="12">{escape(str(label))}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="#FFFFFF" />
    <text x="{width / 2}" y="45" text-anchor="middle" font-size="24" fill="#111827">{escape(title)}</text>
    {''.join(cells)}
    {''.join(row_text)}
    {''.join(col_text)}
    </svg>'''
    write_svg(output_path, svg)


# 统一保存图像的函数
def save_figure(path: str | Path) -> None:
    target_path = Path(path)
    ensure_directory(target_path.parent)
    plt.tight_layout()
    plt.savefig(target_path, dpi=160, bbox_inches="tight")
    plt.close()


# 保存训练曲线
def save_training_curve(history: List[Dict[str, Any]], output_path: str | Path, title: str) -> None:
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
