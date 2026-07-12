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


@dataclass
class SimpleNeuralNetwork:
    hidden_units: int = 24
    learning_rate: float = 0.03
    epochs: int = 280
    l2_strength: float = 0.0005
    random_seed: int = 42
    W1: np.ndarray | None = None
    b1: np.ndarray | None = None
    W2: np.ndarray | None = None
    b2: np.ndarray | None = None
    history: List[Dict[str, float]] = field(default_factory=list)

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> 'SimpleNeuralNetwork':
        sample_count, feature_count = X.shape
        class_count = int(np.max(y)) + 1
        rng = np.random.default_rng(self.random_seed)
        self.W1 = rng.normal(0.0, 0.05, size=(feature_count, self.hidden_units))
        self.b1 = np.zeros((1, self.hidden_units))
        self.W2 = rng.normal(0.0, 0.05, size=(self.hidden_units, class_count))
        self.b2 = np.zeros((1, class_count))
        y_one_hot = np.eye(class_count)[y]
        self.history = []
        report_interval = max(1, self.epochs // 10)

        for epoch_index in range(self.epochs):
            with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                hidden_linear = X @ self.W1 + self.b1
                hidden_activation = np.tanh(hidden_linear)
                logits = hidden_activation @ self.W2 + self.b2
                probabilities = softmax(logits)

                output_error = (probabilities - y_one_hot) / sample_count
                dW2 = hidden_activation.T @ output_error + self.l2_strength * self.W2
                db2 = np.sum(output_error, axis=0, keepdims=True)

                hidden_error = (output_error @ self.W2.T) * (1.0 - np.square(hidden_activation))
                dW1 = X.T @ hidden_error + self.l2_strength * self.W1
                db1 = np.sum(hidden_error, axis=0, keepdims=True)

            self.W2 -= self.learning_rate * dW2
            self.b2 -= self.learning_rate * db2
            self.W1 -= self.learning_rate * dW1
            self.b1 -= self.learning_rate * db1

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
        regularization = 0.5 * self.l2_strength * (float(np.sum(np.square(self.W1))) + float(np.sum(np.square(self.W2))))
        return float(negative_log_likelihood + regularization)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.W1 is None or self.b1 is None or self.W2 is None or self.b2 is None:
            raise ValueError('模型尚未训练，无法执行预测。')
        with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
            hidden_activation = np.tanh(X @ self.W1 + self.b1)
            logits = hidden_activation @ self.W2 + self.b2
            return softmax(logits)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def to_state(self) -> Dict[str, np.ndarray | float | int | list]:
        return {
            'hidden_units': self.hidden_units,
            'learning_rate': self.learning_rate,
            'epochs': self.epochs,
            'l2_strength': self.l2_strength,
            'random_seed': self.random_seed,
            'W1': self.W1,
            'b1': self.b1,
            'W2': self.W2,
            'b2': self.b2,
            'history': self.history,
            'model_type': 'neural_network',
        }

    @classmethod
    def from_state(cls, state: Dict[str, np.ndarray | float | int | list]) -> 'SimpleNeuralNetwork':
        model = cls(
            hidden_units=int(state['hidden_units']),
            learning_rate=float(state['learning_rate']),
            epochs=int(state['epochs']),
            l2_strength=float(state['l2_strength']),
            random_seed=int(state['random_seed']),
        )
        model.W1 = np.asarray(state['W1'])
        model.b1 = np.asarray(state['b1'])
        model.W2 = np.asarray(state['W2'])
        model.b2 = np.asarray(state['b2'])
        model.history = list(state.get('history', []))
        return model
