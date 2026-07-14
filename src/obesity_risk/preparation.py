from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from obesity_risk.io_utils import write_json
from obesity_risk.schema import DatasetSchema, validate_schema


@dataclass
class PreparedData:
    train_features: pd.DataFrame
    validation_features: pd.DataFrame
    test_features: pd.DataFrame
    train_labels: np.ndarray
    validation_labels: np.ndarray
    test_labels: np.ndarray
    transformed_train: np.ndarray
    transformed_validation: np.ndarray
    transformed_test: np.ndarray
    preprocessor: ColumnTransformer
    label_encoder: LabelEncoder
    feature_names: list[str]
    split_indices: dict[str, list[int]]
    clean_summary: dict
    input_metadata: dict


# 根据训练集和已确认 Schema 生成预测输入边界与类别选项
def build_input_metadata(
    train_features: pd.DataFrame, schema: DatasetSchema
) -> dict:
    # 生成模型训练和预测共用的输入元数据。
    input_columns = train_features.columns.tolist()
    numeric_ranges = {}
    for column in schema.numeric_columns:
        if column in schema.suspicious_ranges:
            minimum, maximum = schema.suspicious_ranges[column]
            source = "schema_config"
        else:
            minimum = float(train_features[column].min())
            maximum = float(train_features[column].max())
            source = "training_data"
        numeric_ranges[column] = {
            "minimum": float(minimum),
            "maximum": float(maximum),
            "source": source,
        }
    categorical_options = {
        column: [
            value.item() if isinstance(value, np.generic) else value
            for value in sorted(train_features[column].dropna().unique(), key=str)
        ]
        for column in schema.categorical_columns
    }
    return {
        "input_columns": input_columns,
        "required_columns": input_columns,
        "numeric_columns": list(schema.numeric_columns),
        "categorical_columns": list(schema.categorical_columns),
        "numeric_ranges": numeric_ranges,
        "categorical_options": categorical_options,
    }


# 在副本上执行可解释的最小清洗，不裁剪合法极端值
def clean_dataframe(frame: pd.DataFrame, schema: DatasetSchema) -> tuple[pd.DataFrame, dict]:
    # 清洗字段格式、无穷值和重复行，并返回清洗摘要。
    cleaned = frame.copy(deep=True)
    cleaned.columns = [str(name).strip() for name in cleaned.columns]
    schema_summary = validate_schema(cleaned, schema)
    if not schema_summary["is_valid"]:
        raise ValueError(f"数据 Schema 校验失败：{schema_summary['issues']}")
    before_rows = len(cleaned)
    duplicate_count = int(cleaned.duplicated(keep="first").sum())
    cleaned = cleaned.drop_duplicates(keep="first").copy()
    for column in schema.numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
    for column in (*schema.categorical_columns, schema.target_column):
        if pd.api.types.is_object_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            cleaned[column] = cleaned[column].replace("", np.nan)
    if cleaned[schema.target_column].isna().any():
        raise ValueError("目标字段存在缺失值，无法进行分层划分")
    summary = {
        "rows_before": before_rows,
        "rows_after": len(cleaned),
        "duplicate_rows_removed": duplicate_count,
        "numeric_outliers_removed": 0,
        "rule": "去除完全重复行；规范字符串空白；无穷值转缺失；保留范围内极端值",
        "bmi_feature_added": False,
        "bmi_reason": "体重和身高已作为原始特征，BMI 与目标定义可能直接相关，为降低目标泄漏风险不构造 BMI",
    }
    return cleaned, summary


# 按目标类别依次划分训练、验证和测试索引
def stratified_split_indices(
    labels: pd.Series, split_config: dict
) -> dict[str, list[int]]:
    # 使用固定随机种子返回互斥的三份分层行索引。
    all_indices = labels.index.to_numpy()
    train_indices, remainder_indices = train_test_split(
        all_indices,
        train_size=float(split_config["train"]),
        random_state=int(split_config["random_seed"]),
        stratify=labels.loc[all_indices],
    )
    validation_share = float(split_config["validation"]) / (
        float(split_config["validation"]) + float(split_config["test"])
    )
    validation_indices, test_indices = train_test_split(
        remainder_indices,
        train_size=validation_share,
        random_state=int(split_config["random_seed"]),
        stratify=labels.loc[remainder_indices],
    )
    return {
        "train": sorted(int(index) for index in train_indices),
        "validation": sorted(int(index) for index in validation_indices),
        "test": sorted(int(index) for index in test_indices),
    }


# 创建只在训练数据上拟合的列预处理器
def build_preprocessor(schema: DatasetSchema, preprocessing_config: dict) -> ColumnTransformer:
    # 创建数值填补/缩放和类别填补/独热编码预处理器。
    numeric_steps: list[tuple[str, object]] = [
        ("imputer", SimpleImputer(strategy=preprocessing_config["numeric_imputation"]))
    ]
    if preprocessing_config["scale_numeric"]:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy=preprocessing_config["categorical_imputation"])),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown=preprocessing_config["unknown_category_policy"],
                    sparse_output=False,
                    dtype=np.float64,
                ),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, list(schema.numeric_columns)),
            ("categorical", categorical_pipeline, list(schema.categorical_columns)),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


# 清洗、划分并仅使用训练集拟合预处理器和标签编码器
def prepare_dataframe(
    frame: pd.DataFrame, schema: DatasetSchema, config: dict
) -> PreparedData:
    # 生成四模型共享的无泄漏训练、验证和测试数据。
    cleaned, clean_summary = clean_dataframe(frame, schema)
    split_indices = stratified_split_indices(cleaned[schema.target_column], config["split"])
    feature_columns = [
        *schema.numeric_columns,
        *schema.categorical_columns,
    ]
    feature_frame = cleaned.loc[:, feature_columns]
    target = cleaned[schema.target_column]
    train_features = feature_frame.loc[split_indices["train"]].copy()
    validation_features = feature_frame.loc[split_indices["validation"]].copy()
    test_features = feature_frame.loc[split_indices["test"]].copy()
    label_encoder = LabelEncoder().fit(target.loc[split_indices["train"]])
    unknown_labels = set(target) - set(label_encoder.classes_)
    if unknown_labels:
        raise ValueError(f"训练集未覆盖全部目标类别：{sorted(unknown_labels)}")
    preprocessor = build_preprocessor(schema, config["preprocessing"])
    transformed_train = np.asarray(preprocessor.fit_transform(train_features), dtype=np.float64)
    transformed_validation = np.asarray(preprocessor.transform(validation_features), dtype=np.float64)
    transformed_test = np.asarray(preprocessor.transform(test_features), dtype=np.float64)
    for matrix in (transformed_train, transformed_validation, transformed_test):
        if not np.isfinite(matrix).all():
            raise ValueError("预处理结果包含 NaN 或无穷值")
    return PreparedData(
        train_features=train_features,
        validation_features=validation_features,
        test_features=test_features,
        train_labels=label_encoder.transform(target.loc[split_indices["train"]]),
        validation_labels=label_encoder.transform(target.loc[split_indices["validation"]]),
        test_labels=label_encoder.transform(target.loc[split_indices["test"]]),
        transformed_train=transformed_train,
        transformed_validation=transformed_validation,
        transformed_test=transformed_test,
        preprocessor=preprocessor,
        label_encoder=label_encoder,
        feature_names=list(preprocessor.get_feature_names_out()),
        split_indices=split_indices,
        clean_summary=clean_summary,
        input_metadata=build_input_metadata(train_features, schema),
    )


# 保存固定划分、特征和预处理器，供四模型复用
def save_prepared_artifacts(prepared: PreparedData, processed_dir: Path) -> dict[str, Path]:
    # 保存划分摘要、索引、特征元数据和训练集预处理器。
    processed_dir.mkdir(parents=True, exist_ok=True)
    labels = prepared.label_encoder.classes_.tolist()
    split_summary = {"cleaning": prepared.clean_summary, "classes": labels, "splits": {}}
    for name, encoded in (
        ("train", prepared.train_labels),
        ("validation", prepared.validation_labels),
        ("test", prepared.test_labels),
    ):
        counts = np.bincount(encoded, minlength=len(labels))
        split_summary["splits"][name] = {
            "sample_count": int(len(encoded)),
            "class_distribution": {
                label: {"count": int(count), "ratio": float(count / len(encoded))}
                for label, count in zip(labels, counts)
            },
        }
    feature_metadata = {
        **prepared.input_metadata,
        "transformed_feature_count": len(prepared.feature_names),
        "transformed_feature_names": prepared.feature_names,
        "classes": labels,
        "target_leakage_exclusions": ["id", "BMI"],
    }
    paths = {
        "summary": write_json(processed_dir / "split_summary.json", split_summary),
        "indices": write_json(processed_dir / "split_indices.json", prepared.split_indices),
        "metadata": write_json(processed_dir / "feature_metadata.json", feature_metadata),
        "preprocessor": processed_dir / "preprocessor.joblib",
    }
    joblib.dump(
        {"preprocessor": prepared.preprocessor, "label_encoder": prepared.label_encoder},
        paths["preprocessor"],
    )
    return paths
