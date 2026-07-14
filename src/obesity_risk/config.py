from pathlib import Path

import yaml


# 检查当前阶段真正使用的配置项
def validate_config(config: dict) -> None:
    required_fields = {
        "data": ("raw_path", "target", "exclude_columns"),
        "split": ("train", "validation", "test", "random_seed"),
        "paths": ("processed_dir", "output_dir"),
    }
    for section, fields in required_fields.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"缺少配置字段：{section}")
        for field in fields:
            if field not in config[section]:
                raise ValueError(f"缺少配置字段：{section}.{field}")

    data = config["data"]
    if not isinstance(data["raw_path"], str) or not data["raw_path"].strip():
        raise ValueError("原始数据路径不能为空")
    if data["target"] != "0be1dad":
        raise ValueError("目标字段必须为 0be1dad")
    if not isinstance(data["exclude_columns"], list) or "id" not in data["exclude_columns"]:
        raise ValueError("排除字段必须包含 id")

    split = config["split"]
    ratios = [split["train"], split["validation"], split["test"]]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in ratios):
        raise ValueError("数据集划分比例必须是数值")
    if any(not 0 < value < 1 for value in ratios):
        raise ValueError("数据集划分比例必须大于 0 且小于 1")
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("数据集划分比例之和必须为 1")
    if isinstance(split["random_seed"], bool) or not isinstance(split["random_seed"], int):
        raise ValueError("随机种子必须是整数")

    paths = config["paths"]
    if not isinstance(paths["processed_dir"], str) or not paths["processed_dir"].strip():
        raise ValueError("处理数据目录不能为空")
    if not isinstance(paths["output_dir"], str) or not paths["output_dir"].strip():
        raise ValueError("输出目录不能为空")


# 读取 YAML 配置并执行基础校验
def load_config(config_path: Path) -> dict:
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
