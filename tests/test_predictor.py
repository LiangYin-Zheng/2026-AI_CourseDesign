from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import LabelEncoder

from obesity_risk.predictor import Predictor, load_predictor


class ProbabilityModel:
    def __init__(self, probabilities: np.ndarray | None = None) -> None:
        self.probabilities = probabilities

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        if self.probabilities is not None:
            return self.probabilities
        numeric = pd.to_numeric(frame["x"]).to_numpy(dtype=float)
        positive = 1.0 / (1.0 + np.exp(-numeric))
        return np.column_stack((1.0 - positive, positive))


def make_bundle(probabilities: np.ndarray | None = None) -> dict:
    return {
        "model_name": "test_model",
        "mode": "sklearn_pipeline",
        "model": ProbabilityModel(probabilities),
        "label_encoder": LabelEncoder().fit(["high", "low"]),
        "input_columns": ["x", "category"],
        "required_columns": ["x", "category"],
        "numeric_columns": ["x"],
        "categorical_columns": ["category"],
        "numeric_ranges": {
            "x": {"minimum": -2.0, "maximum": 2.0, "source": "training_data"}
        },
        "categorical_options": {"category": ["A", "B"]},
    }


def test_predictor_loads_bundle_and_predicts_single_and_batch(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    joblib.dump(make_bundle(), model_path)

    predictor = load_predictor(model_path)
    single = predictor.predict_single({"x": 1.5, "category": "A"})
    batch = predictor.predict_batch(
        pd.DataFrame({"x": [-1.5, 1.5], "category": ["A", "B"]})
    )

    assert single["predicted_class"] in {"high", "low"}
    assert abs(sum(single["probabilities"].values()) - 1.0) < 1e-9
    assert len(batch) == 2
    assert "医学诊断" in single["disclaimer"]


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (pd.DataFrame({"x": [1.0]}), "缺少字段.*category"),
        (
            pd.DataFrame({"x": [1.0], "category": ["A"], "extra": [1]}),
            "未知字段.*extra",
        ),
        (pd.DataFrame({"x": [1.0], "category": [""]}), "category"),
        (pd.DataFrame({"x": [None], "category": ["A"]}), "x"),
        (pd.DataFrame({"x": [np.nan], "category": ["A"]}), "x"),
        (pd.DataFrame({"x": [np.inf], "category": ["A"]}), "x"),
        (pd.DataFrame({"x": ["invalid"], "category": ["A"]}), "x"),
        (pd.DataFrame({"x": [-2.1], "category": ["A"]}), "x.*-2.0.*2.0"),
        (pd.DataFrame({"x": [2.1], "category": ["A"]}), "x.*-2.0.*2.0"),
        (pd.DataFrame({"x": [1.0], "category": ["C"]}), "category.*A.*B"),
    ],
)
def test_predictor_rejects_invalid_input(frame: pd.DataFrame, message: str) -> None:
    predictor = Predictor(make_bundle())

    with pytest.raises(ValueError, match=message):
        predictor.predict_batch(frame)


@pytest.mark.parametrize(
    ("probabilities", "message"),
    [
        (np.array([0.4, 0.6]), "二维数组"),
        (np.array([[0.4, 0.6], [0.3, 0.7]]), "行数"),
        (np.array([[0.2, 0.3, 0.5]]), "列数"),
        (np.array([[np.nan, np.nan]]), "有限值"),
        (np.array([[-0.1, 1.1]]), r"\[0, 1\]"),
        (np.array([[0.2, 0.2]]), "概率和"),
    ],
)
def test_predictor_rejects_invalid_probabilities(
    probabilities: np.ndarray, message: str
) -> None:
    predictor = Predictor(make_bundle(probabilities))

    with pytest.raises((ValueError, FloatingPointError), match=message):
        predictor.predict_single({"x": 1.0, "category": "A"})


def test_load_predictor_rejects_missing_model_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="模型文件不存在"):
        load_predictor(tmp_path / "missing.joblib")
