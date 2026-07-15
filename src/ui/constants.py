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

# 集中维护训练控件的参数说明，避免页面内重复长文本。
PARAMETER_HELP = {
    "hidden_layer_sizes": (
        "每个数字代表一层神经元数量，使用英文逗号分隔。\n\n"
        "示例：64 为单隐藏层，训练较快；64,32 为两层结构，适合当前课程数据；"
        "128,64,32 更复杂且训练更久。建议 1～3 层，每层 16～256 个神经元；"
        "系统允许 1～4 层、每层 4～512。"
    ),
    "hidden_size": (
        "手写神经网络仅支持一个隐藏层。允许 4～512，建议 16～128；"
        "增大可能提升表达能力但会增加训练时间和过拟合风险。示例：48。"
    ),
    "learning_rate": (
        "控制每次参数更新幅度。允许范围以控件为准，建议从 0.0001～0.01 尝试；"
        "过大可能导致训练不稳定，过小可能收敛缓慢。默认值来自 config/default.yaml。"
        "示例：0.001。"
    ),
    "C": (
        "sklearn 逻辑回归的正则化强度倒数。允许 0.01～20，建议 0.1～10；"
        "C 越小约束越强，越大越贴合训练数据。示例：1.0。"
    ),
    "alpha": (
        "sklearn 神经网络的 L2 正则化系数。允许 0.00001～0.1，建议 0.0001～0.01；"
        "数值越大约束越强，可降低过拟合但过大可能欠拟合。示例：0.001。"
    ),
    "l2": (
        "NumPy 手写模型的 L2 正则化系数。允许 0～0.1，建议 0.0001～0.01；"
        "数值越大权重约束越强，0 表示不使用 L2。示例：0.0005。"
    ),
    "max_iter": (
        "表示最多优化迭代次数。允许范围以控件为准，建议 200～800；"
        "增大会提高最长训练时间，早停模型可能提前结束，并不保证执行全部轮数。"
        "示例：500。"
    ),
    "max_epochs": (
        "表示最多训练 Epoch。允许范围以控件为准，建议 100～500；"
        "增大会提高最长训练时间，验证损失早停可能使训练提前结束。示例：300。"
    ),
    "batch_size": (
        "每次梯度更新使用的样本数量，仅用于支持 mini-batch 的手写神经网络。"
        "允许 16～2048，建议 64～512；较小批次更新更频繁，较大批次占用更多内存。"
        "示例：256。"
    ),
    "patience": (
        "验证指标连续多少轮没有足够改善后触发早停。允许 2～200，建议 10～40；"
        "调大可等待更久但增加耗时，调小可能过早停止。示例：25。"
    ),
    "tolerance": (
        "判断验证损失是否真正改善的最小阈值。允许 0.000001～0.01，建议 0.000001～0.001；"
        "调大更容易早停，调小会要求更细微的改善。示例：0.00001。"
    ),
    "activation": (
        "隐藏层激活函数。relu 通常训练较快，tanh 输出更平滑；只显示当前 sklearn MLP"
        " 实际支持的选项。示例：relu。"
    ),
    "class_weight": (
        "控制不同类别在损失中的权重。不加权保持原始样本贡献，自动平衡会提高少数类别权重；"
        "只适用于 sklearn 逻辑回归。示例：不加权。"
    ),
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
