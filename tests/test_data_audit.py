import json

import numpy as np
import pandas as pd

from obesity_risk.data_audit import audit_dataframe
from obesity_risk.schema import DatasetSchema


# 创建小型审查 Schema 测试对象
def make_schema() -> DatasetSchema:
    return DatasetSchema(
        required_columns=("Age", "Weight", "Gender", "flag", "target"),
        target_column="target",
        numeric_columns=("Age", "Weight"),
        categorical_columns=("Gender", "flag"),
        excluded_columns=(),
        allow_extra_columns=False,
        allow_missing_columns=False,
        allow_all_null_columns=False,
        suspicious_ranges={"Age": (0.0, 120.0), "Weight": (2.0, 500.0)},
        allowed_categories={"Gender": ("Female", "Male"), "flag": (0, 1)},
        allowed_targets=("A", "B"),
    )


# 验证规模、缺失值和重复行统计
def test_audit_counts_shape_missing_and_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "Age": [20.0, 20.0, None],
            "Weight": [60.0, 60.0, np.inf],
            "Gender": ["Female", "Female", " male "],
            "flag": [1, 1, 0],
            "target": ["A", "A", "B"],
        }
    )
    result = audit_dataframe(frame, make_schema(), imbalance_ratio_warning=1.5)
    assert result["dataset_summary"]["row_count"] == 3
    assert result["dataset_summary"]["column_count"] == 5
    assert result["missing_summary"]["total_missing"] == 1
    assert result["duplicate_summary"]["duplicate_row_count"] == 1
    assert result["numeric_summary"]["Weight"]["infinite_count"] == 1


# 验证数值和类别字段的质量问题标记
def test_audit_reports_numeric_and_categorical_quality() -> None:
    frame = pd.DataFrame(
        {
            "Age": [-1, 0, 130],
            "Weight": [60, 70, 80],
            "Gender": ["Male", " male ", "Femail"],
            "flag": [0, 1, 2],
            "target": ["A", "A", "B"],
        }
    )
    result = audit_dataframe(frame, make_schema(), imbalance_ratio_warning=1.5)
    age = result["numeric_summary"]["Age"]
    assert age["negative_count"] == 1
    assert age["zero_count"] == 1
    assert age["outside_suspicious_range_count"] == 2
    gender = result["categorical_summary"]["Gender"]
    assert gender["leading_or_trailing_whitespace_count"] == 1
    assert gender["case_inconsistencies"]
    assert gender["similar_value_pairs"]
    assert result["categorical_summary"]["flag"]["unexpected_values"] == [2]
    assert result["numeric_summary"]["flag"]["iqr_bounds"] is None


# 验证合法类别不会被误报为相近拼写
def test_allowed_categories_are_not_reported_as_similar_typos() -> None:
    frame = pd.DataFrame(
        {
            "Age": [20, 21],
            "Weight": [60, 70],
            "Gender": ["Female", "Male"],
            "flag": [0, 1],
            "target": ["A", "B"],
        }
    )
    result = audit_dataframe(frame, make_schema())
    assert result["categorical_summary"]["Gender"]["similar_value_pairs"] == []


# 验证目标分布和 JSON 序列化
def test_target_distribution_and_json_serialization() -> None:
    frame = pd.DataFrame(
        {
            "Age": [20, 21, 22],
            "Weight": [60, 70, 80],
            "Gender": ["Female", "Male", "Female"],
            "flag": [0, 1, 0],
            "target": ["A", "A", "B"],
        }
    )
    result = audit_dataframe(frame, make_schema(), imbalance_ratio_warning=1.5)
    target = result["target_summary"]
    assert target["class_count"] == 2
    assert target["most_frequent_class"] == {"value": "A", "count": 2}
    assert target["max_min_count_ratio"] == 2.0
    assert target["is_imbalanced"] is True
    json.dumps(result, ensure_ascii=False, allow_nan=False)


# 验证 Schema 问题会被纳入结果且不修改输入
def test_schema_issue_is_included_without_mutating_frame() -> None:
    frame = pd.DataFrame({"Age": [20], "Weight": [60], "Gender": ["Female"], "flag": [0]})
    before = frame.copy(deep=True)
    result = audit_dataframe(frame, make_schema())
    assert result["schema_summary"]["missing_columns"] == ["target"]
    assert any(issue["code"] == "schema_invalid" for issue in result["quality_issues"])
    pd.testing.assert_frame_equal(frame, before)
