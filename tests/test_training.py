from pathlib import Path

import pandas as pd

from obesity_risk.config import load_config
from obesity_risk.preparation import prepare_dataframe
from obesity_risk.predictor import load_predictor
from obesity_risk.schema import DatasetSchema
from obesity_risk.training import train_sklearn_models


# 验证两个 sklearn Pipeline 均可在小数据上训练、评估和保存
def test_sklearn_models_smoke_test(tmp_path: Path) -> None:
    rows = []
    for index in range(90):
        class_index = index % 3
        rows.append(
            {
                "id": index,
                "Age": 20 + class_index * 10 + index % 4,
                "Height": 1.55 + class_index * 0.08 + (index % 3) * 0.01,
                "Weight": 50 + class_index * 25 + index % 5,
                "Gender": "Female" if index % 2 else "Male",
                "target": f"class_{class_index}",
            }
        )
    frame = pd.DataFrame(rows)
    schema = DatasetSchema(
        required_columns=("id", "Age", "Height", "Weight", "Gender", "target"),
        target_column="target",
        numeric_columns=("Age", "Height", "Weight"),
        categorical_columns=("Gender",),
        excluded_columns=("id",),
        allow_extra_columns=False,
        allow_missing_columns=False,
        allow_all_null_columns=False,
    )
    config = load_config(Path(__file__).parents[1] / "config/default.yaml")
    config["training"]["sklearn_logistic"]["candidates"] = [
        {"C": 1.0, "class_weight": None, "solver": "lbfgs"}
    ]
    config["training"]["sklearn_logistic"]["max_iter"] = 100
    config["training"]["sklearn_mlp"]["candidates"] = [
        {
            "hidden_layer_sizes": [8],
            "activation": "relu",
            "alpha": 0.0001,
            "learning_rate_init": 0.01,
        }
    ]
    config["training"]["sklearn_mlp"]["max_iter"] = 60
    prepared = prepare_dataframe(frame, schema, config)
    results = train_sklearn_models(
        prepared,
        config,
        tmp_path / "models",
        tmp_path / "metrics",
    )
    assert {result["model_name"] for result in results} == {
        "sklearn_logistic",
        "sklearn_mlp",
    }
    assert all(0 <= result["test_metrics"]["macro_f1"] <= 1 for result in results)
    assert (tmp_path / "models/sklearn_logistic.joblib").is_file()
    assert (tmp_path / "models/sklearn_mlp.joblib").is_file()
    predictor = load_predictor(tmp_path / "models/sklearn_logistic.joblib")
    prediction = predictor.predict_single(prepared.train_features.iloc[[0]])
    assert abs(sum(prediction["probabilities"].values()) - 1.0) < 1e-9
