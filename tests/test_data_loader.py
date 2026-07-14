import hashlib
from pathlib import Path

import pandas as pd
import pytest

from data.loader import DataLoadError, load_csv_readonly, snapshot_file


# 创建临时 CSV 测试文件
def write_csv(tmp_path: Path, text: str = "Age,Gender\n20,Female\n") -> Path:
    path = tmp_path / "sample.csv"
    path.write_text(text, encoding="utf-8")
    return path


# 验证 CSV 返回 DataFrame 且文件快照不变
def test_load_csv_returns_dataframe_without_modifying_file(tmp_path: Path) -> None:
    path = write_csv(tmp_path)
    before = snapshot_file(path)
    frame = load_csv_readonly(path)
    after = snapshot_file(path)
    assert isinstance(frame, pd.DataFrame)
    assert frame.shape == (1, 2)
    assert before == after
    assert before["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


# 验证缺失文件提示不泄露绝对路径
def test_missing_csv_has_safe_error(tmp_path: Path) -> None:
    path = tmp_path / "private" / "missing.csv"
    with pytest.raises(DataLoadError, match="CSV 文件不存在") as captured:
        load_csv_readonly(path)
    assert str(tmp_path) not in str(captured.value)


# 验证目录路径被拒绝
def test_directory_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "folder.csv"
    path.mkdir()
    with pytest.raises(DataLoadError, match="不是普通文件"):
        load_csv_readonly(path)


# 验证非 CSV 扩展名被拒绝
def test_non_csv_extension_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DataLoadError, match="扩展名必须为 .csv"):
        load_csv_readonly(path)


# 验证空文件和只有表头的文件被拒绝
@pytest.mark.parametrize("content", ["", "Age,Gender\n"])
def test_empty_csv_is_rejected(tmp_path: Path, content: str) -> None:
    path = write_csv(tmp_path, content)
    with pytest.raises(DataLoadError, match="CSV 没有可审查的数据记录"):
        load_csv_readonly(path)


# 验证格式错误的 CSV 被拒绝
def test_unparseable_csv_is_rejected(tmp_path: Path) -> None:
    path = write_csv(tmp_path, 'Age,Gender\n20,"Female\n21,Male\n')
    with pytest.raises(DataLoadError, match="CSV 格式无法解析"):
        load_csv_readonly(path)


# 验证非 UTF-8 编码的 CSV 被拒绝
def test_non_utf8_csv_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_bytes("名称\n测试\n".encode("gbk"))
    with pytest.raises(DataLoadError, match="UTF-8"):
        load_csv_readonly(path)
