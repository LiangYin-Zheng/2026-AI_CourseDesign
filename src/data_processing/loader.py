from __future__ import annotations

from pathlib import Path

import pandas as pd


# 读取原始 CSV 数据集

def load_dataset(data_path: str | Path) -> pd.DataFrame:
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到数据文件：{path}")
    return pd.read_csv(path)
