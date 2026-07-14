from pathlib import Path

import pytest

from core.paths import get_project_paths


# 创建路径测试使用的最小配置
def make_config(
    raw_path: str = "data/obesity_level.csv",
    processed_dir: str = "data/processed",
    output_dir: str = "outputs",
    report_dir: str = "outputs/data_audit",
) -> dict:
    return {
        "data": {"raw_path": raw_path},
        "paths": {
            "processed_dir": processed_dir,
            "output_dir": output_dir,
        },
        "audit": {"report_dir": report_dir},
        "outputs": {
            "figures_dir": "outputs/eda/figures",
            "metrics_dir": "outputs/metrics",
            "models_dir": "outputs/models",
            "reports_dir": "outputs/reports",
        },
    }


# 创建只包含空原始文件的临时项目
def make_project(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "obesity_level.csv").touch()
    return tmp_path


# 验证项目内路径可以正确解析
def test_resolve_paths_inside_project(tmp_path: Path) -> None:
    project_root = make_project(tmp_path)
    paths = get_project_paths(project_root, make_config())
    assert paths["raw_data"] == (project_root / "data/obesity_level.csv").resolve()
    assert paths["audit_report_dir"] == (project_root / "outputs/data_audit").resolve()


# 验证原始数据路径不能越出项目目录
def test_raw_data_path_cannot_escape_project(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="原始数据路径"):
        get_project_paths(tmp_path, make_config(raw_path="../outside.csv"))


# 验证处理目录不能越出项目目录
def test_processed_dir_cannot_escape_project(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="处理数据目录"):
        get_project_paths(tmp_path, make_config(processed_dir="../processed"))


# 验证输出目录不能越出项目目录
def test_output_dir_cannot_escape_project(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="输出目录"):
        get_project_paths(tmp_path, make_config(output_dir="../outputs"))


# 验证审查报告目录不能越出项目目录
def test_audit_report_dir_cannot_escape_project(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="审查报告目录"):
        get_project_paths(tmp_path, make_config(report_dir="../audit"))


# 验证审查报告目录不能等于原始 CSV
def test_audit_report_dir_cannot_equal_raw_csv(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="不能覆盖原始数据文件"):
        get_project_paths(tmp_path, make_config(report_dir="data/obesity_level.csv"))


# 验证处理和输出路径不能覆盖原始 CSV
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


# 验证处理和输出目录不能使用项目根目录
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


# 验证处理目录和输出目录不能相同
def test_processed_and_output_dirs_must_be_different(tmp_path: Path) -> None:
    make_project(tmp_path)
    with pytest.raises(ValueError, match="不能相同"):
        get_project_paths(tmp_path, make_config(output_dir="data/processed"))


# 验证原始数据文件必须存在
def test_raw_data_file_must_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="原始数据文件不存在"):
        get_project_paths(tmp_path, make_config())
