CLASS_LABELS = {
    "Insufficient_Weight": "体重不足",
    "0rmal_Weight": "正常体重",
    "Overweight_Level_I": "超重 I 级",
    "Overweight_Level_II": "超重 II 级",
    "Obesity_Type_I": "肥胖 I 型",
    "Obesity_Type_II": "肥胖 II 型",
    "Obesity_Type_III": "肥胖 III 型",
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

# 字段含义尚未获得正式数据说明时，使用候选名称并保留原字段名。
FIELD_INFO = {
    "Gender": {"label": "性别", "group": "基本身体信息", "help": "类别字段；正式中文映射待数据说明确认"},
    "Age": {"label": "年龄", "group": "基本身体信息", "unit": "数据值（疑似年）", "step": 0.1},
    "Height": {"label": "身高", "group": "基本身体信息", "unit": "数据值（疑似米）", "step": 0.01},
    "Weight": {"label": "体重", "group": "基本身体信息", "unit": "数据值（疑似千克）", "step": 0.1},
    "family_history_with_overweight": {"label": "超重家族史", "group": "基本身体信息", "help": "0/1 正式含义待确认"},
    "FAVC": {"label": "高热量食物摄入（候选）", "group": "饮食习惯", "help": "FAVC；字段含义及 0/1 映射待确认"},
    "FCVC": {"label": "蔬菜摄入频率（候选）", "group": "饮食习惯", "unit": "数据集观察量表 1–3", "step": 0.1},
    "NCP": {"label": "每日进餐次数（候选）", "group": "饮食习惯", "unit": "数据集观察量表 1–4", "step": 0.1},
    "CAEC": {"label": "两餐之间进食频率（候选）", "group": "饮食习惯", "help": "CAEC；字符串 0 的含义待确认"},
    "CH2O": {"label": "每日饮水情况（候选）", "group": "饮食习惯", "unit": "数据集观察量表 1–3", "step": 0.1},
    "CALC": {"label": "饮酒频率（候选）", "group": "饮食习惯", "help": "CALC；字符串 0 的含义待确认"},
    "SMOKE": {"label": "吸烟状态", "group": "生活习惯", "help": "0/1 正式含义待确认"},
    "SCC": {"label": "热量监测（候选）", "group": "生活习惯", "help": "SCC；字段含义及 0/1 映射待确认"},
    "FAF": {"label": "身体活动频率（候选）", "group": "生活习惯", "unit": "数据集观察量表 0–3", "step": 0.1},
    "TUE": {"label": "电子设备使用情况（候选）", "group": "生活习惯", "unit": "数据集观察量表 0–2", "step": 0.1},
    "MTRANS": {"label": "主要交通方式（候选）", "group": "生活习惯", "help": "MTRANS；取值显示为交通方式，正式问题文本待确认"},
}

CATEGORY_LABELS = {
    "Female": "Female（女性候选）",
    "Male": "Male（男性候选）",
    0: "0（含义待确认）",
    1: "1（含义待确认）",
    "0": "0（含义待确认）",
    "Always": "Always（总是）",
    "Frequently": "Frequently（经常）",
    "Sometimes": "Sometimes（有时）",
    "Automobile": "Automobile（汽车）",
    "Bike": "Bike（自行车）",
    "Motorbike": "Motorbike（摩托车）",
    "Public_Transportation": "Public Transportation（公共交通）",
    "Walking": "Walking（步行）",
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
