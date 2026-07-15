CLASS_LABELS = {
    "Insufficient_Weight": "体重不足",
    "0rmal_Weight": "正常体重",
    "Overweight_Level_I": "超重 I 级",
    "Overweight_Level_II": "超重 II 级",
    "Obesity_Type_I": "肥胖 I 型",
    "Obesity_Type_II": "肥胖 II 型",
    "Obesity_Type_III": "肥胖 III 型",
}

# 将原始类别值转换为界面使用的规范英文标签。
TARGET_DISPLAY_LABELS = {
    "Insufficient_Weight": "Insufficient_Weight",
    "0rmal_Weight": "Normal_Weight",
    "Overweight_Level_I": "Overweight_Level_I",
    "Overweight_Level_II": "Overweight_Level_II",
    "Obesity_Type_I": "Obesity_Type_I",
    "Obesity_Type_II": "Obesity_Type_II",
    "Obesity_Type_III": "Obesity_Type_III",
}

MODEL_INFO = {
    "sklearn_logistic": {
        "name": "sklearn 逻辑回归",
        "implementation": "sklearn",
        "kind": "逻辑回归",
    },
    "sklearn_mlp": {
        "name": "sklearn 神经网络",
        "implementation": "sklearn",
        "kind": "多层感知机",
    },
    "manual_logistic": {
        "name": "NumPy 手写逻辑回归",
        "implementation": "NumPy 手写",
        "kind": "Softmax 逻辑回归",
    },
    "manual_mlp": {
        "name": "NumPy 手写神经网络",
        "implementation": "NumPy 手写",
        "kind": "单隐藏层神经网络",
    },
}

# 使用面向普通用户的中文字段名称，并在帮助文字中保留原始字段。
FIELD_INFO = {
    "Gender": {"label": "性别", "group": "基本身体信息", "help": "选择女性或男性"},
    "Age": {"label": "年龄", "group": "基本身体信息", "unit": "单位：岁", "step": 0.1},
    "Height": {"label": "身高", "group": "基本身体信息", "unit": "单位：米", "step": 0.01},
    "Weight": {"label": "体重", "group": "基本身体信息", "unit": "单位：千克", "step": 0.1},
    "family_history_with_overweight": {"label": "是否有超重家族史", "group": "基本身体信息", "help": "选择“是”或“否"},
    "FAVC": {"label": "是否经常食用高热量食物", "group": "饮食习惯", "help": "选择“是”或“否"},
    "FCVC": {"label": "蔬菜摄入频率", "group": "饮食习惯", "unit": "1 表示较少，2 表示中等，3 表示较多；小数表示中间程度", "step": 0.1},
    "NCP": {"label": "每日主要进餐次数", "group": "饮食习惯", "unit": "1–4 表示每天主要进餐次数；小数表示原数据中的中间值", "step": 0.1},
    "CAEC": {"label": "两餐之间进食频率", "group": "饮食习惯", "help": "选择从不、有时、经常或总是"},
    "CH2O": {"label": "每日饮水水平", "group": "饮食习惯", "unit": "1 表示较少，2 表示中等，3 表示较多；小数表示中间程度", "step": 0.1},
    "CALC": {"label": "饮酒频率", "group": "饮食习惯", "help": "选择从不、有时或经常"},
    "SMOKE": {"label": "是否吸烟", "group": "生活习惯", "help": "选择“是”或“否"},
    "SCC": {"label": "是否监测每日热量摄入", "group": "生活习惯", "help": "选择“是”或“否"},
    "FAF": {"label": "每周身体活动频率", "group": "生活习惯", "unit": "0 表示很少，3 表示频繁；小数表示中间程度", "step": 0.1},
    "TUE": {"label": "电子设备使用时长等级", "group": "生活习惯", "unit": "0 表示较短，2 表示较长；小数表示中间程度", "step": 0.1},
    "MTRANS": {"label": "主要交通方式", "group": "生活习惯", "help": "选择日常最常使用的交通方式"},
}

CATEGORY_LABELS = {
    "Female": "女性",
    "Male": "男性",
    0: "否",
    1: "是",
    "0": "从不",
    "Always": "总是",
    "Frequently": "经常",
    "Sometimes": "有时",
    "Automobile": "汽车",
    "Bike": "自行车",
    "Motorbike": "摩托车",
    "Public_Transportation": "公共交通",
    "Walking": "步行",
}

NAV_ITEMS = (
    "系统概览",
    "肥胖风险预测",
    "模型性能分析",
    "数据探索分析",
    "模型训练中心",
    "项目说明",
)

NAV_LABELS = {
    "系统概览": ":material/dashboard:  系统概览",
    "肥胖风险预测": ":material/analytics:  肥胖风险预测",
    "模型性能分析": ":material/monitoring:  模型性能分析",
    "数据探索分析": ":material/query_stats:  数据探索分析",
    "模型训练中心": ":material/model_training:  模型训练中心",
    "项目说明": ":material/info:  项目说明",
}

DISCLAIMER = "该结果仅为模型基于课程数据集生成的分类结果，不构成医学诊断、健康评估或治疗建议。"
