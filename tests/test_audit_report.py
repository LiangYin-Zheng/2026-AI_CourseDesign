import json
from pathlib import Path

import pytest

from obesity_risk.audit_report import write_audit_reports


# 创建最小报告测试结果
def sample_result() -> dict:
    return {
        "dataset_summary": {"row_count": 1, "column_count": 1, "columns": ["x"]},
        "schema_summary": {"is_valid": True},
        "missing_summary": {"total_missing": 0},
        "duplicate_summary": {"duplicate_row_count": 0},
        "numeric_summary": {},
        "categorical_summary": {},
        "target_summary": {"class_distribution": []},
        "quality_issues": [],
        "file_snapshot": {"name": "sample.csv", "size_bytes": 10, "mtime_ns": 1, "sha256": "a"},
    }


# 验证报告目录创建和 JSON 可读取
def test_write_reports_creates_directory_and_valid_json(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "sample.csv"
    raw.parent.mkdir()
    raw.write_text("x\n1\n", encoding="utf-8")
    paths = write_audit_reports(sample_result(), tmp_path / "outputs" / "audit", raw)
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["dataset_summary"]["row_count"] == 1
    assert "数据审查报告" in paths["markdown"].read_text(encoding="utf-8")
    assert str(tmp_path) not in paths["markdown"].read_text(encoding="utf-8")


# 验证报告不能覆盖原始 CSV
def test_report_path_cannot_overwrite_raw_csv(tmp_path: Path) -> None:
    raw = tmp_path / "data_audit.json"
    raw.write_text("source", encoding="utf-8")
    with pytest.raises(ValueError, match="不能覆盖原始数据文件"):
        write_audit_reports(sample_result(), tmp_path, raw)
    assert raw.read_text(encoding="utf-8") == "source"
