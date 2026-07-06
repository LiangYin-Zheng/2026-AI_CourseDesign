from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.metrics import confusion_matrix as sklearn_confusion_matrix
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.preprocessing import label_binarize


# 构建混淆矩阵

def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    return sklearn_confusion_matrix(y_true, y_pred)


# 计算分类评估指标

def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    probabilities: np.ndarray | None = None,
    class_names: List[str] | None = None,
) -> Dict[str, float | list[list[int]]]:
    matrix = confusion_matrix(y_true, y_pred)
    accuracy = float(np.trace(matrix) / np.sum(matrix)) if np.sum(matrix) else 0.0
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average=None,
        zero_division=0,
    )

    result: Dict[str, float | list[list[int]]] = {
        "accuracy": round(accuracy, 6),
        "macro_precision": round(float(np.mean(precision)), 6),
        "macro_recall": round(float(np.mean(recall)), 6),
        "macro_f1": round(float(np.mean(f1_score)), 6),
        "confusion_matrix": matrix.tolist(),
    }

    if probabilities is not None and class_names is not None and probabilities.ndim == 2 and probabilities.shape[1] == len(class_names):
        try:
            y_binary = label_binarize(y_true, classes=list(range(len(class_names))))
            auc_macro_ovr = roc_auc_score(y_binary, probabilities, average="macro", multi_class="ovr")
            result["macro_roc_auc_ovr"] = round(float(auc_macro_ovr), 6)
        except ValueError:
            result["macro_roc_auc_ovr"] = 0.0

    return result
