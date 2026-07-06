from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


# 将类别频次文本映射为有序风险分值

def map_frequency_to_score(value: str) -> int:
    mapping = {
        "Never": 0,
        "Sometimes": 1,
        "Frequently": 2,
        "Always": 3,
    }
    return mapping.get(str(value), 0)


# 将原始数据清洗为规范化数据

def clean_dataset(raw_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = raw_df.copy()
    df = df.rename(columns=config["raw_column_mapping"])
    df[config["target_column"]] = df[config["target_column"]].replace(config["label_mapping"])

    for column_name, mapping in config["categorical_normalization"].items():
        df[column_name] = df[column_name].astype(str).replace(mapping)

    # 这里对数值特征做边界裁剪，是为了缓解录入误差对模型梯度的放大影响。
    numeric_clip_rules = {
        "age": (10, 100),
        "height_m": (1.2, 2.3),
        "weight_kg": (30, 250),
        "water_intake_liters": (0.5, 5.0),
        "physical_activity_score": (0.0, 3.5),
        "technology_use_hours": (0.0, 3.5),
    }
    for column_name, (lower_bound, upper_bound) in numeric_clip_rules.items():
        df[column_name] = df[column_name].clip(lower=lower_bound, upper=upper_bound)

    # 将二元字段同时保留为数值表达，并派生文字表达，方便后续分析和界面展示。
    df["family_history_text"] = df["family_history_with_overweight"].map({0: "No", 1: "Yes"})
    df["sedentary_transport"] = df["transportation_mode"].isin(["Automobile", "Motorbike"]).astype(int)
    df["snacking_score"] = df["snacking_frequency"].map(map_frequency_to_score)
    df["alcohol_score"] = df["alcohol_consumption"].map(map_frequency_to_score)

    # BMI 是肥胖预测中最直观且最关键的派生指标，能够显著增强模型的可解释性。
    df["bmi"] = df["weight_kg"] / np.square(df["height_m"])

    # 行为风险得分用于把高热量饮食、久坐出行、吸烟、饮酒等因素汇总成一个综合暴露指标。
    df["behavior_risk_score"] = (
        df["high_calorie_food_frequency"]
        + df["smokes"]
        + df["sedentary_transport"]
        + df["snacking_score"]
        + df["alcohol_score"]
        - df["calorie_monitoring"]
    )

    return df
