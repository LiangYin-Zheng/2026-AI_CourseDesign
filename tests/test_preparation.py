from pathlib import Path

import numpy as np
import pandas as pd

from obesity_risk.config import load_config
from obesity_risk.preparation import build_preprocessor, prepare_dataframe
from obesity_risk.schema import DatasetSchema


# 创建包含数值缺失和三类目标的小型数据
def make_frame() -> pd.DataFrame:
    rows = []
    for index in range(60):
        rows.append(
            {
                "id": index,
                "Age": np.nan if index == 3 else 18 + index % 30,
                "Height": 1.55 + (index % 10) * 0.02,
                "Weight": 50 + index % 25,
                "Gender": "Female" if index % 2 else "Male",
                "target": f"class_{index % 3}",
            }
        )
    return pd.DataFrame(rows)


# 创建数据准备测试使用的字段约束
def make_schema() -> DatasetSchema:
    return DatasetSchema(
        required_columns=("id", "Age", "Height", "Weight", "Gender", "target"),
        target_column="target",
        numeric_columns=("Age", "Height", "Weight"),
        categorical_columns=("Gender",),
        excluded_columns=("id",),
        allow_extra_columns=False,
        allow_missing_columns=False,
        allow_all_null_columns=False,
    )


# 读取默认配置供小型流程复用
def default_config() -> dict:
    return load_config(Path(__file__).parents[1] / "config/default.yaml")


# 验证固定分层三分互斥、类别比例稳定且预处理无非有限值
def test_prepare_dataframe_is_stratified_disjoint_and_finite() -> None:
    frame = make_frame()
    before = frame.copy(deep=True)
    prepared = prepare_dataframe(frame, make_schema(), default_config())
    sets = {name: set(indices) for name, indices in prepared.split_indices.items()}
    assert sets["train"].isdisjoint(sets["validation"])
    assert sets["train"].isdisjoint(sets["test"])
    assert sets["validation"].isdisjoint(sets["test"])
    assert set.union(*sets.values()) == set(frame.index)
    assert np.isfinite(prepared.transformed_train).all()
    assert np.isfinite(prepared.transformed_validation).all()
    assert np.isfinite(prepared.transformed_test).all()
    assert set(prepared.train_labels) == {0, 1, 2}
    assert prepared.input_metadata["required_columns"] == [
        "Age",
        "Height",
        "Weight",
        "Gender",
    ]
    assert prepared.input_metadata["numeric_ranges"]["Age"]["source"] == "training_data"
    assert prepared.input_metadata["categorical_options"]["Gender"] == ["Female", "Male"]
    pd.testing.assert_frame_equal(frame, before)


# 验证训练集众数填补和未知类别忽略策略可安全转换
def test_preprocessor_handles_missing_and_unknown_category() -> None:
    config = default_config()
    preprocessor = build_preprocessor(make_schema(), config["preprocessing"])
    train = pd.DataFrame(
        {
            "Age": [20.0, np.nan, 30.0],
            "Height": [1.6, 1.7, 1.8],
            "Weight": [50.0, 70.0, 90.0],
            "Gender": ["Female", "Male", None],
        }
    )
    transformed = preprocessor.fit_transform(train)
    unknown = preprocessor.transform(
        pd.DataFrame({"Age": [25], "Height": [1.75], "Weight": [80], "Gender": ["Unknown"]})
    )
    assert np.isfinite(transformed).all()
    assert np.isfinite(unknown).all()
    assert unknown.shape[1] == transformed.shape[1]
