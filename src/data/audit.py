from difflib import SequenceMatcher
import math

import numpy as np
import pandas as pd

from core.schema import DatasetSchema, validate_schema


# 将 NumPy 标量转换为可序列化的 Python 值
def _python_value(value: object) -> object | None:
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    return value


# 将有限数值转换为浮点数，异常或无穷值返回 None
def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value) or not math.isfinite(float(value)):
        return None
    return float(value)


# 统计单列取值数量和比例
def _distribution(series: pd.Series) -> list[dict]:
    counts = series.value_counts(dropna=False)
    total = len(series)
    return [
        {
            "value": "<MISSING>" if pd.isna(value) else _python_value(value),
            "count": int(count),
            "ratio": float(count / total) if total else 0.0,
        }
        for value, count in counts.items()
    ]


# 统计数值列摘要并标记疑似异常，不修改原列
def _numeric_column_summary(
    series: pd.Series,
    suspicious_range: tuple[float, float] | None,
    apply_iqr: bool,
) -> dict:
    converted = pd.to_numeric(series, errors="coerce")
    non_numeric_count = int((series.notna() & converted.isna()).sum())
    numeric = converted.astype(float)
    finite = numeric[np.isfinite(numeric)]
    stats = finite.describe(percentiles=[0.25, 0.5, 0.75]) if not finite.empty else None
    q1 = _safe_float(stats["25%"]) if stats is not None else None
    q3 = _safe_float(stats["75%"] if stats is not None else None)
    extreme_count = 0
    iqr_bounds: list[float] | None = None
    if apply_iqr and q1 is not None and q3 is not None:
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        iqr_bounds = [lower, upper]
        extreme_count = int(((finite < lower) | (finite > upper)).sum())
    outside_count = 0
    if suspicious_range is not None:
        outside_count = int(
            ((finite < suspicious_range[0]) | (finite > suspicious_range[1])).sum()
        )
    zero_count = int((finite == 0).sum())
    unreasonable_zero_count = (
        zero_count if suspicious_range is not None and suspicious_range[0] > 0 else 0
    )
    return {
        "count": int(series.notna().sum()),
        "finite_count": int(len(finite)),
        "mean": _safe_float(stats["mean"] if stats is not None else None),
        "std": _safe_float(stats["std"] if stats is not None else None),
        "min": _safe_float(stats["min"] if stats is not None else None),
        "25%": q1,
        "50%": _safe_float(stats["50%"] if stats is not None else None),
        "75%": q3,
        "max": _safe_float(stats["max"] if stats is not None else None),
        "negative_count": int((finite < 0).sum()),
        "zero_count": zero_count,
        "unreasonable_zero_count": unreasonable_zero_count,
        "infinite_count": int(np.isinf(numeric).sum()),
        "non_numeric_count": non_numeric_count,
        "iqr_bounds": iqr_bounds,
        "iqr_extreme_count": extreme_count,
        "suspicious_range": list(suspicious_range) if suspicious_range else None,
        "outside_suspicious_range_count": outside_count,
    }


# 统计类别列分布、格式问题和未预期取值
def _categorical_column_summary(
    series: pd.Series, allowed_values: tuple[object, ...] | None
) -> dict:
    non_null = series.dropna()
    string_values = [value for value in non_null if isinstance(value, str)]
    whitespace_count = sum(value != value.strip() for value in string_values)
    empty_count = sum(value.strip() == "" for value in string_values)

    case_groups: dict[str, set[str]] = {}
    for value in string_values:
        case_groups.setdefault(value.strip().casefold(), set()).add(value.strip())
    case_inconsistencies = [
        sorted(values) for values in case_groups.values() if len(values) > 1
    ]

    unique_strings = sorted(set(value.strip() for value in string_values if value.strip()))
    similar_pairs = []
    allowed_strings = (
        [value for value in allowed_values if isinstance(value, str)]
        if allowed_values is not None
        else []
    )
    for index, left in enumerate(unique_strings):
        for right in unique_strings[index + 1 :]:
            if left.casefold() == right.casefold():
                continue
            if allowed_values is not None and left in allowed_strings and right in allowed_strings:
                continue
            similarity = SequenceMatcher(None, left.casefold(), right.casefold()).ratio()
            if similarity >= 0.8:
                similar_pairs.append(
                    {"left": left, "right": right, "similarity": round(similarity, 3)}
                )

    if allowed_values is not None:
        for observed in unique_strings:
            if observed in allowed_strings:
                continue
            for allowed in allowed_strings:
                similarity = SequenceMatcher(
                    None, observed.casefold(), allowed.casefold()
                ).ratio()
                if similarity >= 0.8:
                    candidate = {
                        "left": observed,
                        "right": allowed,
                        "similarity": round(similarity, 3),
                    }
                    if candidate not in similar_pairs:
                        similar_pairs.append(candidate)

    unexpected = []
    if allowed_values is not None:
        for value in pd.unique(non_null):
            if _python_value(value) not in allowed_values:
                unexpected.append(_python_value(value))
        unexpected.sort(key=str)
    return {
        "unique_count": int(series.nunique(dropna=True)),
        "distribution": _distribution(series),
        "leading_or_trailing_whitespace_count": whitespace_count,
        "empty_string_count": empty_count,
        "case_inconsistencies": case_inconsistencies,
        "similar_value_pairs": similar_pairs,
        "unexpected_values": unexpected,
    }


# 统计目标类别分布和类别不平衡提示
def _target_summary(
    frame: pd.DataFrame,
    schema: DatasetSchema,
    imbalance_ratio_warning: float,
) -> dict:
    if schema.target_column not in frame.columns:
        return {
            "field": schema.target_column,
            "class_count": 0,
            "class_distribution": [],
            "most_frequent_class": None,
            "least_frequent_class": None,
            "max_min_count_ratio": None,
            "imbalance_ratio_warning": float(imbalance_ratio_warning),
            "is_imbalanced": False,
            "unexpected_values": [],
        }
    series = frame[schema.target_column]
    distribution = _distribution(series)
    non_missing = [item for item in distribution if item["value"] != "<MISSING>"]
    most = non_missing[0] if non_missing else None
    least = min(non_missing, key=lambda item: item["count"]) if non_missing else None
    ratio = None
    if most and least and least["count"]:
        ratio = float(most["count"] / least["count"])
    unexpected = []
    if schema.allowed_targets:
        unexpected = sorted(
            [
                _python_value(value)
                for value in pd.unique(series.dropna())
                if _python_value(value) not in schema.allowed_targets
            ],
            key=str,
        )
    return {
        "field": schema.target_column,
        "class_count": int(series.nunique(dropna=True)),
        "class_distribution": distribution,
        "most_frequent_class": (
            {"value": most["value"], "count": most["count"]} if most else None
        ),
        "least_frequent_class": (
            {"value": least["value"], "count": least["count"]} if least else None
        ),
        "max_min_count_ratio": ratio,
        "imbalance_ratio_warning": float(imbalance_ratio_warning),
        "is_imbalanced": ratio is not None and ratio >= imbalance_ratio_warning,
        "unexpected_values": unexpected,
    }


# 生成字段、数值和类别摘要
def _build_summaries(frame: pd.DataFrame, schema: DatasetSchema) -> tuple[dict, list[str], dict, dict]:
    row_count = len(frame)
    fields = {}
    for name in frame.columns:
        missing_count = int(frame[name].isna().sum())
        fields[name] = {
            "position": int(frame.columns.get_loc(name)),
            "dtype": str(frame[name].dtype),
            "non_null_count": int(frame[name].notna().sum()),
            "missing_count": missing_count,
            "missing_ratio": float(missing_count / row_count) if row_count else 0.0,
            "unique_count": int(frame[name].nunique(dropna=True)),
        }

    inferred_numeric = list(frame.select_dtypes(include=[np.number]).columns)
    numeric_names = list(dict.fromkeys([*inferred_numeric, *schema.numeric_columns]))
    numeric_summary = {
        name: _numeric_column_summary(
            frame[name],
            schema.suspicious_ranges.get(name),
            apply_iqr=(
                name not in schema.categorical_columns
                and name not in schema.excluded_columns
                and name not in schema.iqr_exempt_columns
            ),
        )
        for name in numeric_names
        if name in frame.columns
    }
    categorical_summary = {
        name: _categorical_column_summary(frame[name], schema.allowed_categories.get(name))
        for name in schema.categorical_columns
        if name in frame.columns
    }
    return fields, inferred_numeric, numeric_summary, categorical_summary


# 汇总 Schema、缺失、重复、数值、类别和目标问题
def _build_quality_issues(
    schema_summary: dict,
    total_missing: int,
    duplicate_count: int,
    numeric_summary: dict,
    categorical_summary: dict,
    target_summary: dict,
) -> list[dict]:
    quality_issues = []
    if not schema_summary["is_valid"]:
        quality_issues.append(
            {"code": "schema_invalid", "severity": "error", "details": schema_summary["issues"]}
        )
    if total_missing:
        quality_issues.append(
            {"code": "missing_values", "severity": "warning", "count": total_missing}
        )
    if duplicate_count:
        quality_issues.append(
            {"code": "duplicate_rows", "severity": "warning", "count": duplicate_count}
        )
    for name, summary in numeric_summary.items():
        flags = {
            key: summary[key]
            for key in (
                "negative_count",
                "unreasonable_zero_count",
                "infinite_count",
                "non_numeric_count",
                "iqr_extreme_count",
                "outside_suspicious_range_count",
            )
            if summary[key]
        }
        if flags:
            quality_issues.append(
                {"code": "numeric_quality", "severity": "warning", "field": name, "flags": flags}
            )
    for name, summary in categorical_summary.items():
        flags = {
            key: summary[key]
            for key in (
                "leading_or_trailing_whitespace_count",
                "empty_string_count",
                "case_inconsistencies",
                "similar_value_pairs",
                "unexpected_values",
            )
            if summary[key]
        }
        if flags:
            quality_issues.append(
                {"code": "categorical_quality", "severity": "warning", "field": name, "flags": flags}
            )
    if target_summary["unexpected_values"]:
        quality_issues.append(
            {
                "code": "unexpected_target_values",
                "severity": "error",
                "values": target_summary["unexpected_values"],
            }
        )
    if target_summary["is_imbalanced"]:
        quality_issues.append(
            {
                "code": "target_imbalance",
                "severity": "warning",
                "ratio": target_summary["max_min_count_ratio"],
            }
        )
    return quality_issues


# 生成数据质量审查结果，不清洗或修改输入 DataFrame
def audit_dataframe(
    frame: pd.DataFrame,
    schema: DatasetSchema,
    imbalance_ratio_warning: float = 1.5,
) -> dict:
    schema_summary = validate_schema(frame, schema)
    row_count = len(frame)
    fields, inferred_numeric, numeric_summary, categorical_summary = _build_summaries(
        frame, schema
    )
    total_missing = int(frame.isna().sum().sum())
    duplicate_count = int(frame.duplicated(keep="first").sum())
    target_summary = _target_summary(frame, schema, imbalance_ratio_warning)
    quality_issues = _build_quality_issues(
        schema_summary,
        total_missing,
        duplicate_count,
        numeric_summary,
        categorical_summary,
        target_summary,
    )

    return {
        "dataset_summary": {
            "row_count": int(row_count),
            "column_count": int(frame.shape[1]),
            "columns": list(frame.columns),
            "fields": fields,
            "pandas_numeric_columns": inferred_numeric,
            "pandas_non_numeric_columns": [
                name for name in frame.columns if name not in inferred_numeric
            ],
        },
        "schema_summary": schema_summary,
        "missing_summary": {
            "total_missing": total_missing,
            "total_missing_ratio": (
                float(total_missing / frame.size) if frame.size else 0.0
            ),
            "by_field": {
                name: {
                    "missing_count": summary["missing_count"],
                    "missing_ratio": summary["missing_ratio"],
                }
                for name, summary in fields.items()
            },
        },
        "duplicate_summary": {
            "duplicate_row_count": duplicate_count,
            "duplicate_row_ratio": float(duplicate_count / row_count) if row_count else 0.0,
        },
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "target_summary": target_summary,
        "quality_issues": quality_issues,
        "file_snapshot": {},
    }
