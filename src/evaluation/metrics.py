from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from core.io import write_json, write_text


def evaluate_predictions(
    true_labels: np.ndarray, predicted_labels: np.ndarray, class_names: list[str]
) -> dict:
    # 计算准确率、宏/加权指标、混淆矩阵和分类报告。
    labels = np.arange(len(class_names))
    macro = precision_recall_fscore_support(
        true_labels, predicted_labels, labels=labels, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        true_labels, predicted_labels, labels=labels, average="weighted", zero_division=0
    )
    report = classification_report(
        true_labels,
        predicted_labels,
        labels=labels,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "macro_precision": float(macro[0]),
        "macro_recall": float(macro[1]),
        "macro_f1": float(macro[2]),
        "weighted_precision": float(weighted[0]),
        "weighted_recall": float(weighted[1]),
        "weighted_f1": float(weighted[2]),
        "confusion_matrix": confusion_matrix(
            true_labels, predicted_labels, labels=labels
        ).tolist(),
        "classification_report": report,
    }


def save_confusion_matrix(
    matrix: list[list[int]], class_names: list[str], path: Path, title: str
) -> Path:
    # 保存带类别标签和计数的混淆矩阵 PNG。
    values = np.asarray(matrix)
    figure, axis = plt.subplots(figsize=(9, 7))
    image = axis.imshow(values, cmap="Blues")
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    axis.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        xlabel="Predicted label",
        ylabel="True label",
        title=title,
    )
    plt.setp(axis.get_xticklabels(), rotation=35, ha="right")
    threshold = values.max() / 2 if values.size else 0
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            axis.text(
                column,
                row,
                str(values[row, column]),
                ha="center",
                va="center",
                color="white" if values[row, column] > threshold else "black",
                fontsize=8,
            )
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return path


def save_loss_curve(
    train_history: list[float], validation_history: list[float], path: Path, title: str
) -> Path:
    # 保存训练损失及可选验证损失曲线。
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(train_history, label="Train loss")
    if validation_history:
        axis.plot(validation_history, label="Validation loss")
    axis.set(title=title, xlabel="Epoch", ylabel="Cross-entropy loss")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return path


# 将单模型分类报告转换为课程材料可用的 Markdown
def _classification_markdown(model_result: dict, class_names: list[str]) -> str:
    metrics = model_result["test_metrics"]
    report = metrics["classification_report"]
    lines = [
        f"# {model_result['display_name']} 分类评估",
        "",
        f"- Accuracy: {metrics['accuracy']:.6f}",
        f"- Macro precision: {metrics['macro_precision']:.6f}",
        f"- Macro recall: {metrics['macro_recall']:.6f}",
        f"- Macro F1: {metrics['macro_f1']:.6f}",
        f"- Weighted F1: {metrics['weighted_f1']:.6f}",
        f"- 训练耗时: {model_result['training_time_seconds']:.6f} 秒",
        f"- 测试推理耗时: {model_result['inference_time_seconds']:.6f} 秒",
        "",
        "| 类别 | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for class_name in class_names:
        values = report[class_name]
        lines.append(
            f"| `{class_name}` | {values['precision']:.6f} | {values['recall']:.6f} | "
            f"{values['f1-score']:.6f} | {int(values['support'])} |"
        )
    lines.extend(
        [
            "",
            "参数：",
            "",
            f"```json\n{model_result['parameters_json']}\n```",
            "",
        ]
    )
    return "\n".join(lines)


def save_evaluation_artifacts(
    model_result: dict, class_names: list[str], metrics_dir: Path
) -> dict[str, Path]:
    # 写出一个模型的完整评估证据。
    model_name = model_result["model_name"]
    paths = {
        "json": write_json(metrics_dir / f"{model_name}_metrics.json", model_result),
        "markdown": write_text(
            metrics_dir / f"{model_name}_classification_report.md",
            _classification_markdown(model_result, class_names),
        ),
        "confusion_matrix": save_confusion_matrix(
            model_result["test_metrics"]["confusion_matrix"],
            class_names,
            metrics_dir / f"{model_name}_confusion_matrix.png",
            f"{model_name} - Confusion Matrix",
        ),
    }
    return paths
