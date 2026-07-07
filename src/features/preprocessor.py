from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd


@dataclass
class TabularPreprocessor:
    numeric_features: List[str]
    categorical_features: List[str]
    numeric_means: Dict[str, float] = field(default_factory=dict)
    numeric_stds: Dict[str, float] = field(default_factory=dict)
    category_levels: Dict[str, List[str]] = field(default_factory=dict)
    class_names: List[str] = field(default_factory=list)
    feature_names_: List[str] = field(default_factory=list)

    # 拟合预处理器统计信息
    def fit(self, df: pd.DataFrame, target_column: str) -> "TabularPreprocessor":
        # 初始化数值特征统计量
        self.numeric_means = {}
        self.numeric_stds = {}
        self.feature_names_ = []

        # 统计数值特征的均值和标准差
        for column_name in self.numeric_features:
            column_values = df[column_name].astype(float)
            self.numeric_means[column_name] = float(column_values.mean())
            std_value = float(column_values.std(ddof=0))
            self.numeric_stds[column_name] = std_value if std_value > 1e-8 else 1.0
            self.feature_names_.append(column_name)

        # 记录类别特征取值集合
        self.category_levels = {}
        for column_name in self.categorical_features:
            levels = sorted(df[column_name].astype(str).unique().tolist())
            self.category_levels[column_name] = levels
            self.feature_names_.extend([f"{column_name}__{level}" for level in levels])

        # 记录标签类别顺序
        self.class_names = sorted(df[target_column].astype(str).unique().tolist())
        return self

    # 将 DataFrame 转换为模型输入矩阵
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        # 构建数值特征矩阵
        numeric_blocks: list[np.ndarray] = []
        for column_name in self.numeric_features:
            values = df[column_name].astype(float).to_numpy().reshape(-1, 1)
            standardized_values = (values - self.numeric_means[column_name]) / self.numeric_stds[column_name]
            numeric_blocks.append(standardized_values)

        # 构建类别特征 one-hot 矩阵
        categorical_blocks: list[np.ndarray] = []
        for column_name in self.categorical_features:
            raw_values = df[column_name].astype(str).tolist()
            levels = self.category_levels[column_name]
            encoded_block = np.zeros((len(raw_values), len(levels)), dtype=float)
            for row_index, raw_value in enumerate(raw_values):
                if raw_value in levels:
                    encoded_block[row_index, levels.index(raw_value)] = 1.0
            categorical_blocks.append(encoded_block)

        return np.hstack(numeric_blocks + categorical_blocks)

    # 将标签列编码为整数索引
    def encode_target(self, labels: pd.Series) -> np.ndarray:
        # 生成标签到索引的映射
        class_to_index = {class_name: index for index, class_name in enumerate(self.class_names)}
        return labels.astype(str).map(class_to_index).to_numpy(dtype=int)

    # 将整数预测结果还原为标签名称
    def decode_target(self, indices: np.ndarray) -> List[str]:
        return [self.class_names[index] for index in indices.tolist()]

    # 将模型概率字典化，便于接口直接输出
    def probabilities_to_dict(self, probabilities: np.ndarray) -> List[Dict[str, float]]:
        # 按类别顺序组织概率输出
        result: List[Dict[str, float]] = []
        for row in probabilities:
            result.append({class_name: round(float(probability), 6) for class_name, probability in zip(self.class_names, row)})
        return result

    # 序列化预处理器元数据
    def to_dict(self) -> Dict[str, Any]:
        # 导出为 JSON 友好的字典
        return {
            "numeric_features": self.numeric_features,
            "categorical_features": self.categorical_features,
            "numeric_means": self.numeric_means,
            "numeric_stds": self.numeric_stds,
            "category_levels": self.category_levels,
            "class_names": self.class_names,
            "feature_names_": self.feature_names_,
        }

    # 从元数据恢复预处理器
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TabularPreprocessor":
        # 按保存的元数据重建实例
        processor = cls(
            numeric_features=data["numeric_features"],
            categorical_features=data["categorical_features"],
        )
        processor.numeric_means = data["numeric_means"]
        processor.numeric_stds = data["numeric_stds"]
        processor.category_levels = data["category_levels"]
        processor.class_names = data["class_names"]
        processor.feature_names_ = data["feature_names_"]
        return processor
