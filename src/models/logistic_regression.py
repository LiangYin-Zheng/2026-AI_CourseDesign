from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

import numpy as np


ProgressCallback = Callable[[int, int, Dict[str, float]], None]


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted_logits = logits - np.max(logits, axis=1, keepdims=True)
    exp_logits = np.exp(shifted_logits)
    return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)


@dataclass
class SoftmaxLogisticRegression:
    learning_rate: float = 0.08
    epochs: int = 300
    reg_strength: float = 0.0005
    random_seed: int = 42
    weights: np.ndarray | None = None
    bias: np.ndarray | None = None
    history: List[Dict[str, float]] = field(default_factory=list)

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> 'SoftmaxLogisticRegression':
        sample_count, feature_count = X.shape
        class_count = int(np.max(y)) + 1
        random_generator = np.random.default_rng(self.random_seed)
        self.weights = random_generator.normal(0.0, 0.01, size=(feature_count, class_count))
        self.bias = np.zeros((1, class_count))
        y_one_hot = np.eye(class_count)[y]
        self.history = []
        report_interval = max(1, self.epochs // 10)

        for epoch_index in range(self.epochs):
            with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                logits = X @ self.weights + self.bias
                probabilities = softmax(logits)
                weight_gradient = (X.T @ (probabilities - y_one_hot)) / sample_count + self.reg_strength * self.weights
                bias_gradient = np.mean(probabilities - y_one_hot, axis=0, keepdims=True)

            self.weights -= self.learning_rate * weight_gradient
            self.bias -= self.learning_rate * bias_gradient

            should_report = epoch_index == 0 or (epoch_index + 1) % report_interval == 0 or epoch_index == self.epochs - 1
            if should_report:
                train_loss = self.loss(X, y)
                record = {'epoch': float(epoch_index + 1), 'train_loss': float(train_loss)}
                if X_val is not None and y_val is not None:
                    record['validation_loss'] = float(self.loss(X_val, y_val))
                self.history.append(record)
                if progress_callback is not None:
                    progress_callback(epoch_index + 1, self.epochs, record)
        return self

    def loss(self, X: np.ndarray, y: np.ndarray) -> float:
        probabilities = self.predict_proba(X)
        safe_probabilities = np.clip(probabilities, 1e-12, 1.0)
        negative_log_likelihood = -np.log(safe_probabilities[np.arange(len(y)), y]).mean()
        regularization = 0.5 * self.reg_strength * float(np.sum(np.square(self.weights)))
        return float(negative_log_likelihood + regularization)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None or self.bias is None:
            raise ValueError('模型尚未训练，无法执行预测。')
        with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
            logits = X @ self.weights + self.bias
            return softmax(logits)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def to_state(self) -> Dict[str, np.ndarray | float | int | list]:
        return {
            'learning_rate': self.learning_rate,
            'epochs': self.epochs,
            'reg_strength': self.reg_strength,
            'random_seed': self.random_seed,
            'weights': self.weights,
            'bias': self.bias,
            'history': self.history,
            'model_type': 'logistic_regression',
        }

    @classmethod
    def from_state(cls, state: Dict[str, np.ndarray | float | int | list]) -> 'SoftmaxLogisticRegression':
        model = cls(
            learning_rate=float(state['learning_rate']),
            epochs=int(state['epochs']),
            reg_strength=float(state['reg_strength']),
            random_seed=int(state['random_seed']),
        )
        model.weights = np.asarray(state['weights'])
        model.bias = np.asarray(state['bias'])
        model.history = list(state.get('history', []))
        return model
