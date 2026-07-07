from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# 从清洗后数据中选择建模特征列
def select_feature_frame(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    # 组合数值和类别特征列
    feature_columns: List[str] = config["numeric_features"] + config["categorical_features"]
    return df[feature_columns].copy()


# 构建 sklearn 预处理流水线
def build_sklearn_preprocessor(config: Dict[str, Any]) -> ColumnTransformer:
    # 取出数值特征和类别特征
    numeric_features: List[str] = config["numeric_features"]
    categorical_features: List[str] = config["categorical_features"]

    # 数值特征先补缺失再标准化
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    # 类别特征先补缺失再独热编码
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )
