import math
from pathlib import Path

import yaml


REQUIRED_FIELDS = {
    "data": (
        "raw_path", "target", "exclude_columns", "required_columns",
        "numeric_columns", "categorical_columns", "allow_extra_columns",
        "allow_missing_columns", "allow_all_null_columns",
    ),
    "split": ("train", "validation", "test", "random_seed"),
    "paths": ("processed_dir", "output_dir"),
    "audit": ("report_dir", "imbalance_ratio_warning", "iqr_exempt_columns", "suspicious_ranges"),
    "preprocessing": (
        "numeric_imputation", "categorical_imputation", "scale_numeric",
        "unknown_category_policy",
    ),
    "training": ("sklearn_logistic", "sklearn_mlp", "manual_logistic", "manual_mlp"),
    "optimization": ("enabled", "scoring"),
    "eda": ("dpi", "scatter_sample_size"),
    "outputs": ("figures_dir", "metrics_dir", "models_dir", "reports_dir"),
}


# 检查所有流程必需的配置区域和字段
def _validate_required_fields(config: dict) -> None:
    for section, fields in REQUIRED_FIELDS.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"缺少配置字段：{section}")
        for field in fields:
            if field not in config[section]:
                raise ValueError(f"缺少配置字段：{section}.{field}")


# 检查数据字段角色之间不存在重复或目标泄漏
def _validate_data_config(data_config: dict) -> None:
    if not isinstance(data_config["raw_path"], str) or not data_config["raw_path"].strip():
        raise ValueError("原始数据路径不能为空")
    if not isinstance(data_config["target"], str) or not data_config["target"].strip():
        raise ValueError("目标字段不能为空")
    if not isinstance(data_config["exclude_columns"], list) or "id" not in data_config["exclude_columns"]:
        raise ValueError("排除字段必须包含 id")
    labels = {
        "required_columns": "必需字段",
        "numeric_columns": "数值字段",
        "categorical_columns": "类别字段",
    }
    for field, label in labels.items():
        values = data_config[field]
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            raise ValueError(f"{label}必须是非空字段名列表")
        if len(values) != len(set(values)):
            raise ValueError(f"{label}不能重复")
    required = set(data_config["required_columns"])
    numeric = set(data_config["numeric_columns"])
    categorical = set(data_config["categorical_columns"])
    if numeric & categorical:
        raise ValueError("数值字段和类别字段不能重叠")
    if not numeric | categorical <= required:
        raise ValueError("数值字段和类别字段必须包含在必需字段中")
    if data_config["target"] not in required:
        raise ValueError("目标字段必须包含在必需字段中")
    if data_config["target"] in numeric | categorical:
        raise ValueError("目标字段不能同时作为输入字段")
    for field in ("allow_extra_columns", "allow_missing_columns", "allow_all_null_columns"):
        if not isinstance(data_config[field], bool):
            raise ValueError(f"data.{field} 必须是布尔值")


# 检查三份数据比例与随机种子
def _validate_split_config(split_config: dict) -> None:
    ratios = [split_config["train"], split_config["validation"], split_config["test"]]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in ratios):
        raise ValueError("数据集划分比例必须是数值")
    if any(not 0 < float(value) < 1 for value in ratios):
        raise ValueError("数据集划分比例必须大于 0 且小于 1")
    if not math.isclose(sum(ratios), 1.0, abs_tol=1e-6):
        raise ValueError("数据集划分比例之和必须为 1")
    seed = split_config["random_seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("随机种子必须是整数且非负")


# 检查审查阈值和字段范围
def _validate_audit_config(audit_config: dict, numeric_columns: list[str]) -> None:
    threshold = audit_config["imbalance_ratio_warning"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 1:
        raise ValueError("类别不平衡告警阈值必须是不小于 1 的数值")
    exempt = audit_config["iqr_exempt_columns"]
    if not isinstance(exempt, list) or len(exempt) != len(set(exempt)):
        raise ValueError("IQR 豁免字段必须是不重复的列表")
    if any(field not in numeric_columns for field in exempt):
        raise ValueError("IQR 豁免字段必须属于数值字段")
    if not isinstance(audit_config["suspicious_ranges"], dict):
        raise ValueError("疑似异常范围必须是字典")
    for field, bounds in audit_config["suspicious_ranges"].items():
        if field not in numeric_columns:
            raise ValueError(f"疑似异常范围字段不在数值字段中：{field}")
        valid = (
            isinstance(bounds, list) and len(bounds) == 2
            and all(not isinstance(value, bool) and isinstance(value, (int, float)) for value in bounds)
            and all(math.isfinite(value) for value in bounds) and bounds[0] < bounds[1]
        )
        if not valid:
            raise ValueError(f"疑似异常范围必须是递增的两个有限数值：{field}")


# 检查预处理和训练参数的基本合法性
def _validate_training_config(config: dict) -> None:
    preprocessing = config["preprocessing"]
    if preprocessing["numeric_imputation"] != "median":
        raise ValueError("当前数值填补策略仅支持 median")
    if preprocessing["categorical_imputation"] != "most_frequent":
        raise ValueError("当前类别填补策略仅支持 most_frequent")
    if preprocessing["unknown_category_policy"] != "ignore":
        raise ValueError("未知类别策略必须为 ignore")
    if not isinstance(preprocessing["scale_numeric"], bool):
        raise ValueError("preprocessing.scale_numeric 必须是布尔值")
    for model_name in ("sklearn_logistic", "sklearn_mlp"):
        model_config = config["training"][model_name]
        if not isinstance(model_config.get("candidates"), list) or not model_config["candidates"]:
            raise ValueError(f"training.{model_name}.candidates 必须是非空列表")
    for model_name in ("manual_logistic", "manual_mlp"):
        model_config = config["training"][model_name]
        if int(model_config.get("max_epochs", 0)) <= 0:
            raise ValueError(f"training.{model_name}.max_epochs 必须大于 0")
    if config["optimization"]["scoring"] != "f1_macro":
        raise ValueError("当前优化指标必须为 f1_macro")


# 检查所有写入路径使用项目内相对路径
def _validate_path_strings(config: dict) -> None:
    values = {
        "paths.processed_dir": config["paths"]["processed_dir"],
        "paths.output_dir": config["paths"]["output_dir"],
        "audit.report_dir": config["audit"]["report_dir"],
        **{f"outputs.{key}": value for key, value in config["outputs"].items()},
    }
    for field, value in values.items():
        if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
            label = "审查报告目录" if field == "audit.report_dir" else field
            raise ValueError(f"{label}必须是项目内相对路径")


# 校验项目完整配置
def validate_config(config: dict) -> None:
    # 校验配置结构和流程所需的安全约束。
    _validate_required_fields(config)
    _validate_data_config(config["data"])
    _validate_split_config(config["split"])
    _validate_audit_config(config["audit"], config["data"]["numeric_columns"])
    _validate_training_config(config)
    _validate_path_strings(config)


# 读取 YAML 配置并执行校验
def load_config(config_path: Path) -> dict:
    # 读取指定 YAML 配置并返回校验后的字典。
    if not config_path.is_file():
        raise FileNotFoundError("配置文件不存在")
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ValueError("配置文件无法读取") from error
    if not isinstance(config, dict):
        raise ValueError("配置根节点必须是字典")
    validate_config(config)
    return config
