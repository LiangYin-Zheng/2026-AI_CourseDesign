import numpy as np

from evaluation import evaluate_predictions


# 验证统一评估包含课程要求的宏平均、加权平均和混淆矩阵
def test_evaluate_predictions_returns_complete_multiclass_metrics() -> None:
    metrics = evaluate_predictions(
        np.array([0, 0, 1, 1, 2, 2]),
        np.array([0, 1, 1, 1, 2, 0]),
        ["A", "B", "C"],
    )
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["macro_precision"] <= 1
    assert 0 <= metrics["macro_recall"] <= 1
    assert 0 <= metrics["macro_f1"] <= 1
    assert 0 <= metrics["weighted_f1"] <= 1
    assert np.asarray(metrics["confusion_matrix"]).shape == (3, 3)
    assert set(("A", "B", "C")).issubset(metrics["classification_report"])
