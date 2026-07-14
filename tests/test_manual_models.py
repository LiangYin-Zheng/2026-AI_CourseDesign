from pathlib import Path

import numpy as np
import pytest

from obesity_risk.manual_models import (
    ManualLogisticRegression,
    ManualMLPClassifier,
    stable_softmax,
)


# 创建容易分离的三类二维训练数据
def make_classification_data() -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(7)
    features = np.vstack(
        [
            generator.normal((-2, -2), 0.35, (30, 2)),
            generator.normal((2, -2), 0.35, (30, 2)),
            generator.normal((0, 2), 0.35, (30, 2)),
        ]
    )
    labels = np.repeat(np.arange(3), 30)
    return features, labels


# 验证 Softmax 在极端得分下仍有限且逐行归一
def test_stable_softmax_handles_large_scores() -> None:
    probabilities = stable_softmax(np.array([[10000.0, 10001.0], [-10000.0, -9999.0]]))
    assert np.isfinite(probabilities).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)


# 验证手写逻辑回归损失下降、维度正确且保存加载一致
def test_manual_logistic_learns_and_round_trips(tmp_path: Path) -> None:
    features, labels = make_classification_data()
    model = ManualLogisticRegression(learning_rate=0.1, max_epochs=120, patience=20)
    model.fit(features, labels, features, labels)
    assert model.train_loss_history[-1] < model.train_loss_history[0]
    assert model.predict_proba(features).shape == (90, 3)
    path = model.save(tmp_path / "manual_logistic.npz")
    loaded = ManualLogisticRegression.load(path)
    np.testing.assert_array_equal(model.predict(features), loaded.predict(features))


# 验证手写神经网络损失下降、预测维度正确且保存加载一致
def test_manual_mlp_learns_and_round_trips(tmp_path: Path) -> None:
    features, labels = make_classification_data()
    model = ManualMLPClassifier(
        hidden_size=12,
        learning_rate=0.01,
        max_epochs=100,
        batch_size=18,
        patience=20,
        random_seed=9,
    )
    model.fit(features, labels, features, labels)
    assert model.train_loss_history[-1] < model.train_loss_history[0]
    assert model.predict(features).shape == (90,)
    path = model.save(tmp_path / "manual_mlp.npz")
    loaded = ManualMLPClassifier.load(path)
    np.testing.assert_array_equal(model.predict(features), loaded.predict(features))


# 验证手写逻辑回归的一步权重更新与有限差分梯度一致
def test_manual_logistic_gradient_matches_finite_difference() -> None:
    features = np.array([[-1.0, 0.5], [0.2, -0.8], [1.1, 0.7], [-0.4, -1.2]])
    labels = np.array([0, 1, 1, 0])
    learning_rate = 1e-4
    model = ManualLogisticRegression(
        learning_rate=learning_rate,
        l2=0.01,
        max_epochs=1,
        patience=1,
    ).fit(features, labels)
    inferred_gradient = -model.weights / learning_rate

    def loss(weights: np.ndarray) -> float:
        probabilities = stable_softmax(features @ weights)
        likelihood = -np.mean(np.log(probabilities[np.arange(len(labels)), labels]))
        return float(likelihood + 0.5 * 0.01 * np.sum(weights * weights))

    epsilon = 1e-6
    numerical = np.zeros_like(model.weights)
    zero_weights = np.zeros_like(model.weights)
    for row, column in ((0, 0), (1, 1)):
        positive = zero_weights.copy()
        negative = zero_weights.copy()
        positive[row, column] += epsilon
        negative[row, column] -= epsilon
        numerical[row, column] = (loss(positive) - loss(negative)) / (2 * epsilon)
        assert abs(numerical[row, column] - inferred_gradient[row, column]) < 1e-6


# 验证手写神经网络反向传播的一步更新与有限差分一致
def test_manual_mlp_gradients_match_finite_difference() -> None:
    features = np.array([[-1.0, 0.4], [0.3, -0.7], [1.0, 0.8], [-0.5, -1.1]])
    labels = np.array([0, 1, 1, 0])
    seed = 5
    hidden_size = 3
    learning_rate = 1e-5
    generator = np.random.default_rng(seed)
    initial_input = generator.normal(0.0, np.sqrt(2.0 / 2), (2, hidden_size))
    initial_output = generator.normal(0.0, np.sqrt(2.0 / hidden_size), (hidden_size, 2))
    model = ManualMLPClassifier(
        hidden_size=hidden_size,
        learning_rate=learning_rate,
        l2=0.01,
        max_epochs=1,
        batch_size=len(features),
        patience=1,
        random_seed=seed,
    ).fit(features, labels)

    def loss(input_weights: np.ndarray, output_weights: np.ndarray) -> float:
        hidden = np.maximum(features @ input_weights, 0.0)
        probabilities = stable_softmax(hidden @ output_weights)
        likelihood = -np.mean(np.log(probabilities[np.arange(len(labels)), labels]))
        penalty = 0.5 * 0.01 * (
            np.sum(input_weights * input_weights) + np.sum(output_weights * output_weights)
        )
        return float(likelihood + penalty)

    epsilon = 1e-6
    positive_input = initial_input.copy()
    negative_input = initial_input.copy()
    positive_input[0, 0] += epsilon
    negative_input[0, 0] -= epsilon
    numerical_input = (
        loss(positive_input, initial_output) - loss(negative_input, initial_output)
    ) / (2 * epsilon)
    inferred_input = (initial_input[0, 0] - model.input_weights[0, 0]) / learning_rate
    assert abs(numerical_input - inferred_input) < 1e-5

    positive_output = initial_output.copy()
    negative_output = initial_output.copy()
    positive_output[0, 0] += epsilon
    negative_output[0, 0] -= epsilon
    numerical_output = (
        loss(initial_input, positive_output) - loss(initial_input, negative_output)
    ) / (2 * epsilon)
    inferred_output = (initial_output[0, 0] - model.output_weights[0, 0]) / learning_rate
    assert abs(numerical_output - inferred_output) < 1e-5


def test_manual_mlp_rejects_validation_class_outside_training_range() -> None:
    features, labels = make_classification_data()
    validation_labels = labels.copy()
    validation_labels[0] = 3
    model = ManualMLPClassifier(max_epochs=2, batch_size=30)

    with pytest.raises(ValueError, match="验证标签超出训练类别范围"):
        model.fit(features, labels, features, validation_labels)


def test_manual_mlp_rejects_negative_validation_label() -> None:
    features, labels = make_classification_data()
    validation_labels = labels.copy()
    validation_labels[0] = -1
    model = ManualMLPClassifier(max_epochs=2, batch_size=30)

    with pytest.raises(ValueError, match="非负整数"):
        model.fit(features, labels, features, validation_labels)


def test_manual_mlp_accepts_valid_validation_labels() -> None:
    features, labels = make_classification_data()
    model = ManualMLPClassifier(max_epochs=2, batch_size=30)

    fitted = model.fit(features, labels, features, labels)

    assert fitted.validation_loss_history
