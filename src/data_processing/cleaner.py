from __future__ import annotations  # 延迟解析类型

from typing import Any, Dict  # 引入标准库的类型提示模块，用于定义函数参数和返回值的类型

import numpy as np  # 引入 NumPy 库，用于数值计算和数组操作
import pandas as pd  # 引入 pandas 库，用于数据处理和分析


# 将类别频次文本映射为有序风险分值
def map_frequency_to_score(value: str) -> int:
    
    # 定义频次到分值的映射关系
    mapping = {
        "Never": 0,
        "Sometimes": 1,
        "Frequently": 2,
        "Always": 3,
    }
    # 找不到匹配值时默认返回 0
    return mapping.get(str(value), 0)


# 将原始数据清洗为规范化数据
def clean_dataset(raw_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:

    # 复制一份原始数据，避免直接修改输入对象
    df = raw_df.copy()
    # 按配置重命名原始列
    df = df.rename(columns=config["raw_column_mapping"])
    # 按配置统一目标标签的取值
    df[config["target_column"]] = df[config["target_column"]].replace(config["label_mapping"])

    # 按配置规范化类别字段
    for column_name, mapping in config["categorical_normalization"].items():
        df[column_name] = df[column_name].astype(str).replace(mapping)

    # 这里对数值特征做边界裁剪，是为了缓解录入误差对模型梯度的放大影响。
    # 定义数值特征的裁剪范围
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
    # 派生家庭肥胖史的文字标签
    df["family_history_text"] = df["family_history_with_overweight"].map({0: "No", 1: "Yes"})
    # 将出行方式转换为是否久坐出行
    df["sedentary_transport"] = df["transportation_mode"].isin(["Automobile", "Motorbike"]).astype(int)
    # 将零食频率转换为分值
    df["snacking_score"] = df["snacking_frequency"].map(map_frequency_to_score)
    # 将饮酒频率转换为分值
    df["alcohol_score"] = df["alcohol_consumption"].map(map_frequency_to_score)

    # BMI 是肥胖预测中最直观且最关键的派生指标，能够显著增强模型的可解释性。
    # 计算 BMI 指标
    df["bmi"] = df["weight_kg"] / np.square(df["height_m"])

    # 行为风险得分用于把高热量饮食、久坐出行、吸烟、饮酒等因素汇总成一个综合暴露指标。
    # 汇总行为风险得分
    df["behavior_risk_score"] = (
        df["high_calorie_food_frequency"]
        + df["smokes"]
        + df["sedentary_transport"]
        + df["snacking_score"]
        + df["alcohol_score"]
        - df["calorie_monitoring"]
    )

    return df
