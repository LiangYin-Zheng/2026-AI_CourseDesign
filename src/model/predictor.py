import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class Predictor:
    def __init__(self, bundle: dict) -> None:
        # 使用已加载的模型 bundle 创建预测器。
        required = {
            "model_name",
            "mode",
            "model",
            "label_encoder",
            "input_columns",
            "required_columns",
            "numeric_columns",
            "categorical_columns",
            "numeric_ranges",
            "categorical_options",
        }
        missing = required - set(bundle)
        if missing:
            raise ValueError(f"模型文件缺少字段：{sorted(missing)}")
        self.bundle = bundle
        self.input_columns = list(bundle["input_columns"])
        self.required_columns = list(bundle["required_columns"])
        self.numeric_columns = list(bundle["numeric_columns"])
        self.categorical_columns = list(bundle["categorical_columns"])
        if set(self.required_columns) != set(self.input_columns):
            raise ValueError("模型文件的必填字段与输入字段不一致")
        if set(self.numeric_columns + self.categorical_columns) != set(
            self.input_columns
        ):
            raise ValueError("模型文件的特征类型与输入字段不一致")

    def _validate_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            raise ValueError("预测输入必须是非空 DataFrame")
        missing = [
            column for column in self.required_columns if column not in frame.columns
        ]
        extra = [column for column in frame.columns if column not in self.input_columns]
        if missing:
            raise ValueError(f"预测输入缺少字段：{missing}")
        if extra:
            raise ValueError(f"预测输入包含未知字段：{extra}")
        validated = frame.loc[:, self.input_columns].copy()
        for column in self.required_columns:
            missing_value = validated[column].isna()
            if pd.api.types.is_object_dtype(validated[column]):
                missing_value |= validated[column].map(
                    lambda value: isinstance(value, str) and not value.strip()
                )
            if missing_value.any():
                raise ValueError(f"必填字段包含空值：{column}")
        for column in self.numeric_columns:
            converted = pd.to_numeric(validated[column], errors="coerce")
            if converted.isna().any() or not np.isfinite(converted.to_numpy()).all():
                raise ValueError(f"数值字段包含非法输入：{column}")
            bounds = self.bundle["numeric_ranges"].get(column)
            if not isinstance(bounds, dict) or not {"minimum", "maximum"} <= set(
                bounds
            ):
                raise ValueError(f"模型文件缺少数值范围：{column}")
            minimum = float(bounds["minimum"])
            maximum = float(bounds["maximum"])
            if ((converted < minimum) | (converted > maximum)).any():
                raise ValueError(
                    f"数值字段 {column} 超出允许范围 [{minimum}, {maximum}]"
                )
            validated[column] = converted
        for column in self.categorical_columns:
            options = self.bundle["categorical_options"].get(column)
            if not isinstance(options, list) or not options:
                raise ValueError(f"模型文件缺少类别选项：{column}")
            if not validated[column].isin(options).all():
                raise ValueError(f"类别字段 {column} 必须属于合法选项：{options}")
        return validated

    # 调用 sklearn Pipeline 或手写模型计算概率
    def _predict_probabilities(self, frame: pd.DataFrame) -> np.ndarray:
        if self.bundle["mode"] == "sklearn_pipeline":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                probabilities = self.bundle["model"].predict_proba(frame)
            return np.asarray(probabilities, dtype=np.float64)
        if self.bundle["mode"] == "manual":
            transformed = self.bundle["preprocessor"].transform(frame)
            return np.asarray(
                self.bundle["model"].predict_proba(transformed), dtype=np.float64
            )
        raise ValueError("模型文件包含不支持的预测模式")

    def _validate_probabilities(
        self, probabilities: np.ndarray, row_count: int
    ) -> np.ndarray:
        if probabilities.ndim != 2:
            raise ValueError("模型返回的概率必须是二维数组")
        if probabilities.shape[0] != row_count:
            raise ValueError("模型返回的概率行数与输入行数不一致")
        class_count = len(self.bundle["label_encoder"].classes_)
        if probabilities.shape[1] != class_count:
            raise ValueError("模型返回的概率列数与类别数不一致")
        if not np.isfinite(probabilities).all():
            raise ValueError("模型返回的概率包含非有限值")
        if ((probabilities < 0) | (probabilities > 1)).any():
            raise ValueError("模型返回的概率必须位于 [0, 1]")
        if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
            raise ValueError("模型返回的每行概率和必须接近 1")
        return probabilities

    def predict_batch(self, frame: pd.DataFrame) -> list[dict]:
        # 验证批量输入，并返回每行的类别、概率和模型名称。
        validated = self._validate_frame(frame)
        probabilities = self._validate_probabilities(
            self._predict_probabilities(validated), len(validated)
        )
        encoded = np.argmax(probabilities, axis=1)
        class_names = self.bundle["label_encoder"].classes_.tolist()
        predictions = []
        for row_index, class_index in enumerate(encoded):
            predictions.append(
                {
                    "predicted_class": class_names[int(class_index)],
                    "highest_probability": float(probabilities[row_index, class_index]),
                    "probabilities": {
                        class_name: float(probability)
                        for class_name, probability in zip(
                            class_names, probabilities[row_index]
                        )
                    },
                    "model_name": self.bundle["model_name"],
                    "disclaimer": ("仅用于课程项目演示，不构成医学诊断或健康建议。"),
                }
            )
        return predictions

    def predict_single(self, sample: dict | pd.DataFrame) -> dict:
        # 预测单条样本，并返回结构化结果。
        frame = pd.DataFrame([sample]) if isinstance(sample, dict) else sample
        if not isinstance(frame, pd.DataFrame) or len(frame) != 1:
            raise ValueError("单条预测必须提供一个字典或单行 DataFrame")
        return self.predict_batch(frame)[0]


def load_predictor(model_path: Path) -> Predictor:
    # 加载 joblib 模型 bundle 并返回独立于 UI 框架的预测器。
    if not model_path.is_file():
        raise FileNotFoundError("模型文件不存在")
    try:
        bundle = joblib.load(model_path)
    except (OSError, ValueError, EOFError) as error:
        raise ValueError("模型文件无法加载") from error
    if not isinstance(bundle, dict):
        raise ValueError("模型文件结构不合法")
    return Predictor(bundle)
