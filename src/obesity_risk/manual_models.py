from pathlib import Path

import numpy as np


def stable_softmax(scores: np.ndarray) -> np.ndarray:
    """返回逐行归一化的稳定 Softmax 概率。"""
    shifted = scores - np.max(scores, axis=1, keepdims=True)
    exponential = np.exp(shifted)
    return exponential / exponential.sum(axis=1, keepdims=True)


# 在 Apple Accelerate 环境隔离浮点状态，并对矩阵乘法结果做实质有限性校验
def _finite_matmul(left: np.ndarray, right: np.ndarray, context: str) -> np.ndarray:
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        product = left @ right
    if not np.isfinite(product).all():
        raise FloatingPointError(f"{context}出现非有限矩阵结果")
    return product


# 校验训练或推理矩阵为有限二维浮点数组
def _validate_features(features: np.ndarray, expected_columns: int | None = None) -> np.ndarray:
    matrix = np.asarray(features, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("输入特征必须是非空二维数组")
    if expected_columns is not None and matrix.shape[1] != expected_columns:
        raise ValueError("输入特征维度与模型不一致")
    if not np.isfinite(matrix).all():
        raise ValueError("输入特征包含 NaN 或无穷值")
    return matrix


# 校验整数标签并确认与样本数一致
def _validate_labels(labels: np.ndarray, sample_count: int) -> np.ndarray:
    vector = np.asarray(labels)
    if vector.ndim != 1 or len(vector) != sample_count:
        raise ValueError("标签必须是一维数组且与样本数一致")
    if not np.issubdtype(vector.dtype, np.integer) or np.any(vector < 0):
        raise ValueError("标签必须是从 0 开始的非负整数")
    return vector.astype(np.int64)


# 计算多分类交叉熵并加入 L2 正则项
def _cross_entropy(
    probabilities: np.ndarray, labels: np.ndarray, weights: tuple[np.ndarray, ...], l2: float
) -> float:
    clipped = np.clip(probabilities[np.arange(len(labels)), labels], 1e-12, 1.0)
    penalty = 0.5 * l2 * sum(float(np.sum(weight * weight)) for weight in weights)
    return float(-np.mean(np.log(clipped)) + penalty)


class ManualLogisticRegression:
    def __init__(
        self,
        learning_rate: float = 0.08,
        l2: float = 0.0005,
        max_epochs: int = 300,
        patience: int = 25,
        tolerance: float = 1e-5,
        random_seed: int = 42,
    ) -> None:
        """创建带 L2 正则与早停的手写多分类逻辑回归。"""
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
        """拟合模型，可使用验证集早停并恢复最佳参数。"""
        features = _validate_features(train_features)
        labels = _validate_labels(train_labels, len(features))
        class_count = int(labels.max()) + 1
        if set(np.unique(labels)) != set(range(class_count)):
            raise ValueError("训练标签必须连续覆盖 0 到类别数减 1")
        validation = None
        validated_labels = None
        if validation_features is not None or validation_labels is not None:
            if validation_features is None or validation_labels is None:
                raise ValueError("验证特征和标签必须同时提供")
            validation = _validate_features(validation_features, features.shape[1])
            validated_labels = _validate_labels(validation_labels, len(validation))
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
                _finite_matmul(features, self.weights, "手写逻辑回归前向传播") + self.bias
            )
            train_loss = _cross_entropy(probabilities, labels, (self.weights,), self.l2)
            gradient = probabilities.copy()
            gradient[np.arange(len(labels)), labels] -= 1.0
            gradient /= len(labels)
            weight_gradient = (
                _finite_matmul(features.T, gradient, "手写逻辑回归梯度")
                + self.l2 * self.weights
            )
            bias_gradient = gradient.sum(axis=0)
            self.weights -= self.learning_rate * weight_gradient
            self.bias -= self.learning_rate * bias_gradient
            self.train_loss_history.append(train_loss)
            monitored_loss = train_loss
            if validation is not None and validated_labels is not None:
                validation_probabilities = stable_softmax(
                    _finite_matmul(validation, self.weights, "手写逻辑回归验证") + self.bias
                )
                monitored_loss = _cross_entropy(
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
        """计算类别概率，模型未拟合时抛出错误。"""
        if self.weights is None or self.bias is None:
            raise ValueError("模型尚未拟合")
        matrix = _validate_features(features, self.weights.shape[0])
        return stable_softmax(
            _finite_matmul(matrix, self.weights, "手写逻辑回归推理") + self.bias
        )

    def predict(self, features: np.ndarray) -> np.ndarray:
        """返回一维整数类别预测。"""
        return np.argmax(self.predict_proba(features), axis=1)

    def save(self, path: Path) -> Path:
        """将已拟合模型保存为 NumPy 压缩文件。"""
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
        """加载先前保存的手写逻辑回归。"""
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


class ManualMLPClassifier:
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
        """创建单隐藏层 ReLU 手写神经网络。"""
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

    # 执行一次前向传播并返回中间激活和概率
    def _forward(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if any(
            parameter is None
            for parameter in (
                self.input_weights, self.hidden_bias, self.output_weights, self.output_bias
            )
        ):
            raise ValueError("模型尚未拟合")
        hidden_linear = (
            _finite_matmul(features, self.input_weights, "手写神经网络隐藏层")
            + self.hidden_bias
        )
        hidden_activation = np.maximum(hidden_linear, 0.0)
        probabilities = stable_softmax(
            _finite_matmul(hidden_activation, self.output_weights, "手写神经网络输出层")
            + self.output_bias
        )
        return hidden_linear, hidden_activation, probabilities

    # 计算当前完整数据损失
    def _loss(self, features: np.ndarray, labels: np.ndarray) -> float:
        probabilities = self._forward(features)[2]
        return _cross_entropy(
            probabilities,
            labels,
            (self.input_weights, self.output_weights),
            self.l2,
        )

    def fit(
        self,
        train_features: np.ndarray,
        train_labels: np.ndarray,
        validation_features: np.ndarray | None = None,
        validation_labels: np.ndarray | None = None,
    ) -> "ManualMLPClassifier":
        """拟合神经网络，可使用验证损失早停。"""
        features = _validate_features(train_features)
        labels = _validate_labels(train_labels, len(features))
        class_count = int(labels.max()) + 1
        if set(np.unique(labels)) != set(range(class_count)):
            raise ValueError("训练标签必须连续覆盖 0 到类别数减 1")
        validation = None
        validated_labels = None
        if validation_features is not None or validation_labels is not None:
            if validation_features is None or validation_labels is None:
                raise ValueError("验证特征和标签必须同时提供")
            validation = _validate_features(validation_features, features.shape[1])
            validated_labels = _validate_labels(validation_labels, len(validation))
            if np.any(validated_labels >= class_count):
                raise ValueError("验证标签超出训练类别范围")
        random_generator = np.random.default_rng(self.random_seed)
        input_scale = np.sqrt(2.0 / features.shape[1])
        output_scale = np.sqrt(2.0 / self.hidden_size)
        self.input_weights = random_generator.normal(
            0.0, input_scale, (features.shape[1], self.hidden_size)
        )
        self.hidden_bias = np.zeros(self.hidden_size)
        self.output_weights = random_generator.normal(
            0.0, output_scale, (self.hidden_size, class_count)
        )
        self.output_bias = np.zeros(class_count)
        self.classes_ = np.arange(class_count)
        self.train_loss_history = []
        self.validation_loss_history = []
        best_loss = np.inf
        best_parameters = self._copy_parameters()
        stale_epochs = 0
        for _ in range(self.max_epochs):
            shuffled = random_generator.permutation(len(features))
            for start in range(0, len(features), self.batch_size):
                batch_indices = shuffled[start : start + self.batch_size]
                batch_features = features[batch_indices]
                batch_labels = labels[batch_indices]
                hidden_linear, hidden_activation, probabilities = self._forward(batch_features)
                output_gradient = probabilities.copy()
                output_gradient[np.arange(len(batch_labels)), batch_labels] -= 1.0
                output_gradient /= len(batch_labels)
                output_weight_gradient = (
                    _finite_matmul(
                        hidden_activation.T, output_gradient, "手写神经网络输出层梯度"
                    )
                    + self.l2 * self.output_weights
                )
                output_bias_gradient = output_gradient.sum(axis=0)
                hidden_gradient = _finite_matmul(
                    output_gradient, self.output_weights.T, "手写神经网络反向传播"
                )
                hidden_gradient[hidden_linear <= 0] = 0.0
                input_weight_gradient = (
                    _finite_matmul(
                        batch_features.T, hidden_gradient, "手写神经网络输入层梯度"
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

    # 复制网络参数用于早停恢复
    def _copy_parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return (
            self.input_weights.copy(), self.hidden_bias.copy(),
            self.output_weights.copy(), self.output_bias.copy(),
        )

    # 恢复验证损失最低时的网络参数
    def _restore_parameters(
        self, parameters: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    ) -> None:
        (
            self.input_weights, self.hidden_bias,
            self.output_weights, self.output_bias,
        ) = parameters

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """计算各目标类别概率。"""
        if self.input_weights is None:
            raise ValueError("模型尚未拟合")
        matrix = _validate_features(features, self.input_weights.shape[0])
        return self._forward(matrix)[2]

    def predict(self, features: np.ndarray) -> np.ndarray:
        """返回一维整数类别预测。"""
        return np.argmax(self.predict_proba(features), axis=1)

    def save(self, path: Path) -> Path:
        """将已拟合网络保存为 NumPy 压缩文件。"""
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
        """加载先前保存的手写神经网络。"""
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
