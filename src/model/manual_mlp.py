# NumPy 手写单隐藏层神经网络。

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


class ManualMLPClassifier:
    # 带 ReLU、mini-batch、L2 和验证损失早停的手写 MLP。

    def __init__(
        self,
        hidden_size: int = 48,
        learning_rate: float = 0.01,
        l2: float = 0.0005,
        max_epochs: int = 220,
        batch_size: int = 256,
        patience: int = 25,
        tolerance: float = 1e-5,
        random_seed: int = 42,
    ) -> None:
        if hidden_size <= 0 or learning_rate <= 0 or l2 < 0:
            raise ValueError("隐藏层、学习率或正则强度不合法")
        if max_epochs <= 0 or batch_size <= 0 or patience <= 0:
            raise ValueError("轮数、批大小或耐心值必须大于 0")
        self.hidden_size = int(hidden_size)
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        self.max_epochs = int(max_epochs)
        self.batch_size = int(batch_size)
        self.patience = int(patience)
        self.tolerance = float(tolerance)
        self.random_seed = int(random_seed)
        self.input_weights: np.ndarray | None = None
        self.hidden_bias: np.ndarray | None = None
        self.output_weights: np.ndarray | None = None
        self.output_bias: np.ndarray | None = None
        self.classes_: np.ndarray | None = None
        self.train_loss_history: list[float] = []
        self.validation_loss_history: list[float] = []

    def _forward(
        self, features: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if any(
            parameter is None
            for parameter in (
                self.input_weights,
                self.hidden_bias,
                self.output_weights,
                self.output_bias,
            )
        ):
            raise ValueError("模型尚未拟合")
        hidden_linear = (
            finite_matmul(features, self.input_weights, "手写神经网络隐藏层")
            + self.hidden_bias
        )
        hidden_activation = np.maximum(hidden_linear, 0.0)
        probabilities = stable_softmax(
            finite_matmul(
                hidden_activation,
                self.output_weights,
                "手写神经网络输出层",
            )
            + self.output_bias
        )
        return hidden_linear, hidden_activation, probabilities

    def _loss(self, features: np.ndarray, labels: np.ndarray) -> float:
        probabilities = self._forward(features)[2]
        return cross_entropy(
            probabilities, labels, (self.input_weights, self.output_weights), self.l2
        )

    def fit(
        self,
        train_features: np.ndarray,
        train_labels: np.ndarray,
        validation_features: np.ndarray | None = None,
        validation_labels: np.ndarray | None = None,
    ) -> "ManualMLPClassifier":
        # 拟合神经网络并根据验证损失恢复最佳参数。
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
        generator = np.random.default_rng(self.random_seed)
        self.input_weights = generator.normal(
            0.0, np.sqrt(2.0 / features.shape[1]), (features.shape[1], self.hidden_size)
        )
        self.hidden_bias = np.zeros(self.hidden_size)
        self.output_weights = generator.normal(
            0.0, np.sqrt(2.0 / self.hidden_size), (self.hidden_size, class_count)
        )
        self.output_bias = np.zeros(class_count)
        self.classes_ = np.arange(class_count)
        self.train_loss_history = []
        self.validation_loss_history = []
        best_loss = np.inf
        best_parameters = self._copy_parameters()
        stale_epochs = 0
        for _ in range(self.max_epochs):
            shuffled = generator.permutation(len(features))
            for start in range(0, len(features), self.batch_size):
                indices = shuffled[start : start + self.batch_size]
                batch_features = features[indices]
                batch_labels = labels[indices]
                hidden_linear, hidden_activation, probabilities = self._forward(
                    batch_features
                )
                output_gradient = probabilities.copy()
                output_gradient[np.arange(len(batch_labels)), batch_labels] -= 1.0
                output_gradient /= len(batch_labels)
                output_weight_gradient = (
                    finite_matmul(
                        hidden_activation.T,
                        output_gradient,
                        "手写神经网络输出层梯度",
                    )
                    + self.l2 * self.output_weights
                )
                output_bias_gradient = output_gradient.sum(axis=0)
                hidden_gradient = finite_matmul(
                    output_gradient,
                    self.output_weights.T,
                    "手写神经网络反向传播",
                )
                hidden_gradient[hidden_linear <= 0] = 0.0
                input_weight_gradient = (
                    finite_matmul(
                        batch_features.T,
                        hidden_gradient,
                        "手写神经网络输入层梯度",
                    )
                    + self.l2 * self.input_weights
                )
                hidden_bias_gradient = hidden_gradient.sum(axis=0)
                self.output_weights -= self.learning_rate * output_weight_gradient
                self.output_bias -= self.learning_rate * output_bias_gradient
                self.input_weights -= self.learning_rate * input_weight_gradient
                self.hidden_bias -= self.learning_rate * hidden_bias_gradient
            train_loss = self._loss(features, labels)
            self.train_loss_history.append(train_loss)
            monitored_loss = train_loss
            if validation is not None and validated_labels is not None:
                monitored_loss = self._loss(validation, validated_labels)
                self.validation_loss_history.append(monitored_loss)
            if not np.isfinite(monitored_loss):
                raise FloatingPointError("手写神经网络训练出现非有限损失")
            if monitored_loss < best_loss - self.tolerance:
                best_loss = monitored_loss
                best_parameters = self._copy_parameters()
                stale_epochs = 0
            else:
                stale_epochs += 1
                if stale_epochs >= self.patience:
                    break
        self._restore_parameters(best_parameters)
        return self

    def _copy_parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return (
            self.input_weights.copy(),
            self.hidden_bias.copy(),
            self.output_weights.copy(),
            self.output_bias.copy(),
        )

    def _restore_parameters(
        self, parameters: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    ) -> None:
        self.input_weights, self.hidden_bias, self.output_weights, self.output_bias = (
            parameters
        )

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        # 计算各目标类别概率。
        if self.input_weights is None:
            raise ValueError("模型尚未拟合")
        matrix = validate_features(features, self.input_weights.shape[0])
        return self._forward(matrix)[2]

    def predict(self, features: np.ndarray) -> np.ndarray:
        # 返回一维整数类别预测。
        return np.argmax(self.predict_proba(features), axis=1)

    def save(self, path: Path) -> Path:
        # 将已拟合网络保存为 NumPy 压缩文件。
        if self.input_weights is None:
            raise ValueError("模型尚未拟合")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            input_weights=self.input_weights,
            hidden_bias=self.hidden_bias,
            output_weights=self.output_weights,
            output_bias=self.output_bias,
            hidden_size=self.hidden_size,
            learning_rate=self.learning_rate,
            l2=self.l2,
            max_epochs=self.max_epochs,
            batch_size=self.batch_size,
            patience=self.patience,
            tolerance=self.tolerance,
            random_seed=self.random_seed,
            train_history=np.asarray(self.train_loss_history),
            validation_history=np.asarray(self.validation_loss_history),
        )
        return path

    @classmethod
    def load(cls, path: Path) -> "ManualMLPClassifier":
        # 加载先前保存的手写神经网络。
        with np.load(path) as stored:
            model = cls(
                hidden_size=int(stored["hidden_size"]),
                learning_rate=float(stored["learning_rate"]),
                l2=float(stored["l2"]),
                max_epochs=int(stored["max_epochs"]),
                batch_size=int(stored["batch_size"]),
                patience=int(stored["patience"]),
                tolerance=float(stored["tolerance"]),
                random_seed=int(stored["random_seed"]),
            )
            model.input_weights = stored["input_weights"].copy()
            model.hidden_bias = stored["hidden_bias"].copy()
            model.output_weights = stored["output_weights"].copy()
            model.output_bias = stored["output_bias"].copy()
            model.classes_ = np.arange(model.output_bias.shape[0])
            model.train_loss_history = stored["train_history"].tolist()
            model.validation_loss_history = stored["validation_history"].tolist()
        return model
