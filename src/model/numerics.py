# 手写模型共享的数值校验和损失函数。

import numpy as np


def stable_softmax(scores: np.ndarray) -> np.ndarray:
    # 返回逐行归一化的稳定 Softmax 概率。
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0:
        raise ValueError("Softmax 输入必须是非空二维数组")
    shifted = values - np.max(values, axis=1, keepdims=True)
    exponential = np.exp(shifted)
    return exponential / exponential.sum(axis=1, keepdims=True)


def finite_matmul(left: np.ndarray, right: np.ndarray, context: str) -> np.ndarray:
    # 执行矩阵乘法并拒绝非有限结果。
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        product = left @ right
    if not np.isfinite(product).all():
        raise FloatingPointError(f"{context}出现非有限矩阵结果")
    return product


def validate_features(
    features: np.ndarray, expected_columns: int | None = None
) -> np.ndarray:
    # 校验并转换训练或推理特征矩阵。
    matrix = np.asarray(features, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("输入特征必须是非空二维数组")
    if expected_columns is not None and matrix.shape[1] != expected_columns:
        raise ValueError("输入特征维度与模型不一致")
    if not np.isfinite(matrix).all():
        raise ValueError("输入特征包含 NaN 或无穷值")
    return matrix


def validate_labels(labels: np.ndarray, sample_count: int) -> np.ndarray:
    # 校验非负连续整数标签。
    vector = np.asarray(labels)
    if vector.ndim != 1 or len(vector) != sample_count:
        raise ValueError("标签必须是一维数组且与样本数一致")
    if not np.issubdtype(vector.dtype, np.integer) or np.any(vector < 0):
        raise ValueError("标签必须是从 0 开始的非负整数")
    return vector.astype(np.int64)


def cross_entropy(
    probabilities: np.ndarray,
    labels: np.ndarray,
    weights: tuple[np.ndarray, ...],
    l2: float,
) -> float:
    # 计算多分类交叉熵并加入 L2 正则项。
    clipped = np.clip(probabilities[np.arange(len(labels)), labels], 1e-12, 1.0)
    penalty = 0.5 * l2 * sum(float(np.sum(weight * weight)) for weight in weights)
    return float(-np.mean(np.log(clipped)) + penalty)


def validate_training_labels(labels: np.ndarray) -> int:
    # 确认训练标签连续覆盖 0 到类别数减 1，并返回类别数。
    class_count = int(labels.max()) + 1
    if set(np.unique(labels)) != set(range(class_count)):
        raise ValueError("训练标签必须连续覆盖 0 到类别数减 1")
    return class_count
