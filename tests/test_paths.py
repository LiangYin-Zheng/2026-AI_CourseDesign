from pathlib import Path

import pytest

from obesity_risk.paths import get_project_paths


# 创建路径测试使用的最小配置
def make_config(
    raw_path: str = "data/obesity_level.csv",
    processed_dir: str = "data/processed",
    output_dir: str = "outputs",
) -> dict:
    return {
        "data": {"raw_path": raw_path},
        "paths": {
            "processed_dir": processed_dir,
            "output_dir": output_dir,
        },
    }


# 创建只包含空原始文件的临时项目
def make_project(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "obesity_level.csv").touch()
    return tmp_path


def test_resolve_paths_inside_project(tmp_path: Path) -> None:
    project_root = make_project(tmp_path)
    paths = get_project_paths(project_root, make_config())
    assert paths["raw_data"] == (project_root / "data/obesity_level.csv").resolve()


def test_raw_data_path_cannot_escape_project(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="原始数据路径"):
        get_project_paths(tmp_path, make_config(raw_path="../outside.csv"))


def test_processed_dir_cannot_escape_project(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="处理数据目录"):
        get_project_paths(tmp_path, make_config(processed_dir="../processed"))


def test_output_dir_cannot_escape_project(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="输出目录"):
        get_project_paths(tmp_path, make_config(output_dir="../outputs"))


@pytest.mark.parametrize("field", ["processed_dir", "output_dir"])
def test_output_path_cannot_equal_raw_csv(tmp_path: Path, field: str) -> None:
    make_project(tmp_path)
    values = {
        "processed_dir": "data/processed",
        "output_dir": "outputs",
    }
    values[field] = "data/obesity_level.csv"

    with pytest.raises(ValueError, match="不能覆盖原始数据文件"):
        get_project_paths(
            tmp_path,
            make_config(
                processed_dir=values["processed_dir"],
                output_dir=values["output_dir"],
            ),
        )


@pytest.mark.parametrize("field", ["processed_dir", "output_dir"])
def test_output_dir_cannot_be_project_root(tmp_path: Path, field: str) -> None:
    make_project(tmp_path)
    values = {
        "processed_dir": "data/processed",
        "output_dir": "outputs",
    }
    values[field] = "."

    with pytest.raises(ValueError, match="不能直接使用项目根目录"):
        get_project_paths(
            tmp_path,
            make_config(
                processed_dir=values["processed_dir"],
                output_dir=values["output_dir"],
            ),
        )


def test_processed_and_output_dirs_must_be_different(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="不能相同"):
        get_project_paths(tmp_path, make_config(output_dir="data/processed"))


def test_raw_data_file_must_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="原始数据文件不存在"):
        get_project_paths(tmp_path, make_config())
