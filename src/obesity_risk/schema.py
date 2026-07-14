from dataclasses import dataclass, field
import pandas as pd
from pandas.api.types import is_numeric_dtype


# 保存审查所需的固定字段约束
@dataclass(frozen=True)
class DatasetSchema:
    required_columns: tuple[str, ...]
    target_column: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...]
    allow_extra_columns: bool
    allow_missing_columns: bool
    allow_all_null_columns: bool
    suspicious_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    iqr_exempt_columns: tuple[str, ...] = ()
    allowed_categories: dict[str, tuple[object, ...]] = field(default_factory=dict)
    allowed_targets: tuple[object, ...] = ()


# 根据配置建立实际数据集 Schema
def build_schema(config: dict) -> DatasetSchema:
    data = config["data"]
    target = data["target"]
    observed_categories: dict[str, tuple[object, ...]] = {}
    observed_targets: tuple[object, ...] = ()
    if target == "0be1dad":
        observed_categories = {
            "Gender": ("Female", "Male"),
            "family_history_with_overweight": (0, 1),
            "FAVC": (0, 1),
            "CAEC": ("0", "Always", "Frequently", "Sometimes"),
            "SMOKE": (0, 1),
            "SCC": (0, 1),
            "CALC": ("0", "Frequently", "Sometimes"),
            "MTRANS": (
                "Automobile",
                "Bike",
                "Motorbike",
                "Public_Transportation",
                "Walking",
            ),
        }
        observed_targets = (
            "Insufficient_Weight",
            "0rmal_Weight",
            "Overweight_Level_I",
            "Overweight_Level_II",
            "Obesity_Type_I",
            "Obesity_Type_II",
            "Obesity_Type_III",
        )
    return DatasetSchema(
        required_columns=tuple(data["required_columns"]),
        target_column=target,
        numeric_columns=tuple(data["numeric_columns"]),
        categorical_columns=tuple(data["categorical_columns"]),
        excluded_columns=tuple(data["exclude_columns"]),
        allow_extra_columns=data["allow_extra_columns"],
        allow_missing_columns=data["allow_missing_columns"],
        allow_all_null_columns=data["allow_all_null_columns"],
        suspicious_ranges={
            name: (float(bounds[0]), float(bounds[1]))
            for name, bounds in config["audit"]["suspicious_ranges"].items()
        },
        iqr_exempt_columns=tuple(config["audit"]["iqr_exempt_columns"]),
        allowed_categories=observed_categories,
        allowed_targets=observed_targets,
    )


# 检查字段存在性、顺序、额外字段、全空字段及数值类型
def validate_schema(frame: pd.DataFrame, schema: DatasetSchema) -> dict:
    columns = list(frame.columns)
    required = list(schema.required_columns)
    missing = [name for name in required if name not in columns]
    extra = [name for name in columns if name not in required]
    all_null = [name for name in columns if frame[name].isna().all()]
    numeric_type_mismatches = [
        name
        for name in schema.numeric_columns
        if name in frame.columns and not is_numeric_dtype(frame[name])
    ]
    issues = []
    if missing:
        issues.append({"code": "missing_columns", "fields": missing})
    if extra:
        issues.append({"code": "extra_columns", "fields": extra})
    if columns != required:
        issues.append({"code": "column_order_mismatch"})
    if all_null:
        issues.append({"code": "all_null_columns", "fields": all_null})
    if numeric_type_mismatches:
        issues.append({"code": "numeric_type_mismatch", "fields": numeric_type_mismatches})
    is_valid = (
        (schema.allow_missing_columns or not missing)
        and (schema.allow_extra_columns or not extra)
        and (schema.allow_all_null_columns or not all_null)
        and not numeric_type_mismatches
        and columns == required
    )
    return {
        "is_valid": is_valid,
        "required_fields": required,
        "numeric_fields": list(schema.numeric_columns),
        "categorical_fields": list(schema.categorical_columns),
        "excluded_fields": list(schema.excluded_columns),
        "target_field": schema.target_column,
        "allow_extra_columns": schema.allow_extra_columns,
        "allow_missing_columns": schema.allow_missing_columns,
        "allow_all_null_columns": schema.allow_all_null_columns,
        "column_order_matches": columns == required,
        "missing_columns": missing,
        "extra_columns": extra,
        "all_null_columns": all_null,
        "numeric_type_mismatches": numeric_type_mismatches,
        "issues": issues,
    }
