import json
from pathlib import Path

import numpy as np


# 将 NumPy 标量和数组转换为 JSON 可写对象
def to_json_value(value: object) -> object:
    """递归转换 NumPy 值，供 JSON 和报告产物复用。"""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_value(item) for item in value]
    return value


# 原子写入 UTF-8 文本，避免中断留下半份结果
def write_text(path: Path, content: str) -> Path:
    """创建父目录并原子写入 UTF-8 文本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
    return path


# 以稳定中文 JSON 格式保存结构化产物
def write_json(path: Path, content: object) -> Path:
    """将结构化对象转换并保存为 UTF-8 JSON。"""
    serialized = json.dumps(
        to_json_value(content), ensure_ascii=False, indent=2, allow_nan=False
    )
    return write_text(path, serialized + "\n")
