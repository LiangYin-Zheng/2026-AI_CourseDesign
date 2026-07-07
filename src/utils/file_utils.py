from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# 确保目录存在
def ensure_directory(path: str | Path) -> Path:
    # 创建目标目录及其父目录
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# 写入 JSON 文件
def write_json(path: str | Path, data: Any) -> None:
    # 写入前先确保目录存在
    target_path = Path(path)
    ensure_directory(target_path.parent)
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


# 读取 JSON 文件
def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


# 写入文本文件
def write_text(path: str | Path, content: str) -> None:
    # 写入前先确保目录存在
    target_path = Path(path)
    ensure_directory(target_path.parent)
    with target_path.open("w", encoding="utf-8") as file:
        file.write(content)
