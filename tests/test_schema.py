from pathlib import Path

import pandas as pd

from obesity_risk.config import load_config
from obesity_risk.paths import get_project_root
from obesity_risk.schema import DatasetSchema, build_schema, validate_schema


# 创建小型 Schema 测试对象
def make_schema() -> DatasetSchema:
    return DatasetSchema(
        required_columns=("id", "Age", "Gender", "target"),
        target_column="target",
        numeric_columns=("Age",),
        categorical_columns=("Gender",),
        excluded_columns=("id",),
        allow_extra_columns=False,
        allow_missing_columns=False,
        allow_all_null_columns=False,
        suspicious_ranges={"Age": (0.0, 120.0)},
    )


# 验证合法数据的字段角色和 Schema 状态
def test_validate_schema_reports_roles_and_valid_frame() -> None:
    frame = pd.DataFrame({"id": [1], "Age": [20.0], "Gender": ["F"], "target": ["A"]})
    summary = validate_schema(frame, make_schema())
    assert summary["is_valid"] is True
    assert summary["numeric_fields"] == ["Age"]
    assert summary["categorical_fields"] == ["Gender"]
    assert summary["target_field"] == "target"


# 验证缺失必需字段会被报告
def test_validate_schema_reports_missing_required_field() -> None:
    frame = pd.DataFrame({"id": [1], "Age": [20.0], "target": ["A"]})
    summary = validate_schema(frame, make_schema())
    assert summary["is_valid"] is False
    assert summary["missing_columns"] == ["Gender"]


# 验证字段顺序、额外字段和全空字段会被报告
def test_validate_schema_reports_order_extra_and_all_null() -> None:
    frame = pd.DataFrame(
        {"Age": [None], "id": [1], "Gender": ["F"], "target": ["A"], "extra": [1]}
    )
    summary = validate_schema(frame, make_schema())
    assert summary["column_order_matches"] is False
    assert summary["extra_columns"] == ["extra"]
    assert summary["all_null_columns"] == ["Age"]
    assert summary["is_valid"] is False


# 验证 Schema 结果不包含本机路径
def test_schema_contains_no_paths() -> None:
    assert str(Path.home()) not in str(validate_schema(pd.DataFrame(), make_schema()))


# 验证默认 Schema 与实际 18 列结构一致
def test_default_schema_matches_actual_eighteen_columns() -> None:
    project_root = get_project_root()
    schema = build_schema(load_config(project_root / "config/default.yaml"))
    assert len(schema.required_columns) == 18
    assert schema.required_columns[0] == "id"
    assert schema.required_columns[-1] == schema.target_column == "0be1dad"
    assert schema.numeric_columns == (
        "Age",
        "Height",
        "Weight",
        "FCVC",
        "NCP",
        "CH2O",
        "FAF",
        "TUE",
    )
