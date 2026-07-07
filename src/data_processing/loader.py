from __future__ import annotations  # 延迟解析类型

from pathlib import Path  # 引入标准库的 Path 类，用于处理文件路径
import pandas as pd  # 引入 pandas 库，用于数据处理和分析


# 读取原始 CSV 数据集
def load_dataset(data_path: str | Path) -> pd.DataFrame:
    
    # 读取 CSV 文件并返回 DataFrame
    path = Path(data_path)

    # 检查文件是否存在
    if not path.exists():
        raise FileNotFoundError(f"未找到数据文件：{path}")

    # 读取 CSV 文件
    return pd.read_csv(path)
