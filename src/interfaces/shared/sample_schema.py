from __future__ import annotations

from typing import Any


FIELD_DEFINITIONS = [
    ('gender', '性别', 'Female', ['Female', 'Male']),
    ('age', '年龄', 24.0, None),
    ('height_m', '身高（米）', 1.70, None),
    ('weight_kg', '体重（千克）', 72.0, None),
    ('family_history_with_overweight', '家族肥胖史', 1, ['1', '0']),
    ('high_calorie_food_frequency', '高热量饮食偏好', 1, ['1', '0']),
    ('vegetable_intake_score', '蔬菜摄入评分', 2.5, None),
    ('main_meals_per_day', '每日正餐次数', 3.0, None),
    ('snacking_frequency', '加餐频率', 'Sometimes', ['Never', 'Sometimes', 'Frequently', 'Always']),
    ('smokes', '是否吸烟', 0, ['0', '1']),
    ('water_intake_liters', '饮水量（升）', 2.0, None),
    ('calorie_monitoring', '是否热量监测', 0, ['0', '1']),
    ('physical_activity_score', '运动评分', 1.5, None),
    ('technology_use_hours', '电子设备使用时长评分', 1.0, None),
    ('alcohol_consumption', '饮酒频率', 'Sometimes', ['Never', 'Sometimes', 'Frequently', 'Always']),
    ('transportation_mode', '出行方式', 'Automobile', ['Public_Transportation', 'Automobile', 'Walking', 'Motorbike', 'Bike']),
]

INTEGER_FIELDS = {'family_history_with_overweight', 'high_calorie_food_frequency', 'smokes', 'calorie_monitoring'}
FLOAT_FIELDS = {'age', 'height_m', 'weight_kg', 'vegetable_intake_score', 'main_meals_per_day', 'water_intake_liters', 'physical_activity_score', 'technology_use_hours'}


def coerce_value(field_name: str, raw_value: str) -> Any:
    if field_name in INTEGER_FIELDS:
        return int(float(raw_value))
    if field_name in FLOAT_FIELDS:
        return float(raw_value)
    return raw_value


def coerce_sample_value(field_name: str, raw_value: str) -> Any:
    return coerce_value(field_name, raw_value)


def build_sample_payload(field_values: dict[str, str]) -> dict[str, Any]:
    return {field_name: coerce_value(field_name, raw_value) for field_name, raw_value in field_values.items()}

