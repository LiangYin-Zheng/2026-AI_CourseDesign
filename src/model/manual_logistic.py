# NumPy 手写多分类逻辑回归。

from pathlib import Path

import numpy as np

from model.numerics import (
    cross_entropy,
    finite_matmul,
    stable_softmax,
    validate_features,
    validate_labels,
    validate_training_labels,
)


class ManualLogisticRegression:
    # 带 L2 正则、验证集早停和最佳参数恢复的手写逻辑回归。

    def __init__(
        self,
        learning_rate: float = 0.08,
        l2: float = 0.0005,
        max_epochs: int = 300,
        patience: int = 25,
        tolerance: float = 1e-5,
        random_seed: int = 42,
    ) -> None:
        if learning_rate <= 0 or l2 < 0 or max_epochs <= 0 or patience <= 0:
            raise ValueError("学习率、正则强度、轮数或耐心值不合法")
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.tolerance = float(tolerance)
        self.random_seed = int(random_seed)
        self.weights: np.ndarray | None = None
        self.bias: np.ndarray | None = None
        self.classes_: np.ndarray | None = None
        self.train_loss_history: list[float] = []
        self.validation_loss_history: list[float] = []

    def fit(
        self,
        train_features: np.ndarray,
        train_labels: np.ndarray,
        validation_features: np.ndarray | None = None,
        validation_labels: np.ndarray | None = None,
    ) -> "ManualLogisticRegression":
        # 拟合模型，可使用验证集早停并恢复最佳参数。
        features = validate_features(train_features)
        labels = validate_labels(train_labels, len(features))
        class_count = validate_training_labels(labels)
        validation = None
        validated_labels = None
        if validation_features is not None or validation_labels is not None:
            if validation_features is None or validation_labels is None:
                raise ValueError("验证特征和标签必须同时提供")
            validation = validate_features(validation_features, features.shape[1])
            validated_labels = validate_labels(validation_labels, len(validation))
            if np.any(validated_labels >= class_count):
                raise ValueError("验证标签超出训练类别范围")
        self.weights = np.zeros((features.shape[1], class_count), dtype=np.float64)
        self.bias = np.zeros(class_count, dtype=np.float64)
        self.classes_ = np.arange(class_count)
        self.train_loss_history = []
        self.validation_loss_history = []
        best_loss = np.inf
        best_parameters = (self.weights.copy(), self.bias.copy())
        stale_epochs = 0
        for _ in range(self.max_epochs):
            probabilities = stable_softmax(
                finite_matmul(features, self.weights, "手写逻辑回归前向传播")
                + self.bias
            )
            train_loss = cross_entropy(probabilities, labels, (self.weights,), self.l2)
            gradient = probabilities.copy()
            gradient[np.arange(len(labels)), labels] -= 1.0
            gradient /= len(labels)
            weight_gradient = (
                finite_matmul(features.T, gradient, "手写逻辑回归梯度")
                + self.l2 * self.weights
            )
            bias_gradient = gradient.sum(axis=0)
            self.weights -= self.learning_rate * weight_gradient
            self.bias -= self.learning_rate * bias_gradient
            self.train_loss_history.append(train_loss)
            monitored_loss = train_loss
            if validation is not None and validated_labels is not None:
                validation_probabilities = stable_softmax(
                    finite_matmul(validation, self.weights, "手写逻辑回归验证")
                    + self.bias
                )
                monitored_loss = cross_entropy(
                    validation_probabilities, validated_labels, (self.weights,), self.l2
                )
                self.validation_loss_history.append(monitored_loss)
            if not np.isfinite(monitored_loss):
                raise FloatingPointError("手写逻辑回归训练出现非有限损失")
            if monitored_loss < best_loss - self.tolerance:
                best_loss = monitored_loss
                best_parameters = (self.weights.copy(), self.bias.copy())
                stale_epochs = 0
            else:
                stale_epochs += 1
                if stale_epochs >= self.patience:
                    break
        self.weights, self.bias = best_parameters
        return self

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        # 计算类别概率。
        if self.weights is None or self.bias is None:
            raise ValueError("模型尚未拟合")
        matrix = validate_features(features, self.weights.shape[0])
        return stable_softmax(
            finite_matmul(matrix, self.weights, "手写逻辑回归推理") + self.bias
        )

    def predict(self, features: np.ndarray) -> np.ndarray:
        # 返回一维整数类别预测。
        return np.argmax(self.predict_proba(features), axis=1)

    def save(self, path: Path) -> Path:
        # 将已拟合模型保存为 NumPy 压缩文件。
        if self.weights is None or self.bias is None:
            raise ValueError("模型尚未拟合")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            weights=self.weights,
            bias=self.bias,
            learning_rate=self.learning_rate,
            l2=self.l2,
            max_epochs=self.max_epochs,
            patience=self.patience,
            tolerance=self.tolerance,
            random_seed=self.random_seed,
            train_history=np.asarray(self.train_loss_history),
            validation_history=np.asarray(self.validation_loss_history),
        )
        return path

    @classmethod
    def load(cls, path: Path) -> "ManualLogisticRegression":
        # 加载先前保存的手写逻辑回归。
        with np.load(path) as stored:
            model = cls(
                learning_rate=float(stored["learning_rate"]),
                l2=float(stored["l2"]),
                max_epochs=int(stored["max_epochs"]),
                patience=int(stored["patience"]),
                tolerance=float(stored["tolerance"]),
                random_seed=int(stored["random_seed"]),
            )
            model.weights = stored["weights"].copy()
            model.bias = stored["bias"].copy()
            model.classes_ = np.arange(model.bias.shape[0])
            model.train_loss_history = stored["train_history"].tolist()
            model.validation_loss_history = stored["validation_history"].tolist()
        return model
