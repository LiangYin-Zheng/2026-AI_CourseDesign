import hashlib
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


# 表示原始 CSV 无法安全读取
class DataLoadError(ValueError):
    """表示原始 CSV 无法安全读取。"""


# 检查 CSV 路径是否存在、是普通文件且扩展名正确
def _validate_csv_path(csv_path: Path) -> None:
    if not csv_path.exists():
        raise DataLoadError(f"CSV 文件不存在：{csv_path.name}")
    if not csv_path.is_file():
        raise DataLoadError(f"CSV 路径不是普通文件：{csv_path.name}")
    if csv_path.suffix.lower() != ".csv":
        raise DataLoadError(f"数据文件扩展名必须为 .csv：{csv_path.name}")


# 计算文件大小、纳秒修改时间和 SHA-256，不返回本机绝对路径
def snapshot_file(csv_path: Path) -> dict[str, str | int]:
    _validate_csv_path(csv_path)
    digest = hashlib.sha256()
    try:
        with csv_path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        stat = csv_path.stat()
    except OSError as error:
        raise DataLoadError(f"CSV 文件无法读取：{csv_path.name}") from error
    return {
        "name": csv_path.name,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": digest.hexdigest(),
    }


# 按原始字段和值读取 UTF-8 CSV，不执行清洗或转换
def load_csv_readonly(csv_path: Path) -> pd.DataFrame:
    _validate_csv_path(csv_path)
    try:
        frame = pd.read_csv(csv_path, encoding="utf-8", engine="c")
    except EmptyDataError as error:
        raise DataLoadError("CSV 没有可审查的数据记录") from error
    except UnicodeDecodeError as error:
        raise DataLoadError(f"CSV 不是可读取的 UTF-8 编码：{csv_path.name}") from error
    except ParserError as error:
        raise DataLoadError(f"CSV 格式无法解析：{csv_path.name}") from error
    except OSError as error:
        raise DataLoadError(f"CSV 文件无法读取：{csv_path.name}") from error
    if frame.empty:
        raise DataLoadError("CSV 没有可审查的数据记录")
    return frame
