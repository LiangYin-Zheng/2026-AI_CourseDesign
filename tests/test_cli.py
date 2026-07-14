from pathlib import Path

from obesity_risk.__main__ import main


# 验证默认健康检查入口保持可用
def test_default_health_check_still_works(capsys) -> None:
    assert main([]) == 0
    assert "项目配置检查通过" in capsys.readouterr().out


# 验证数据审查命令生成报告
def test_audit_data_generates_reports(monkeypatch, tmp_path: Path, capsys) -> None:
    data_dir = tmp_path / "data"
    config_dir = tmp_path / "config"
    data_dir.mkdir()
    config_dir.mkdir()
    (data_dir / "sample.csv").write_text("id,Age,Gender,target\n1,20,F,A\n", encoding="utf-8")
    (config_dir / "default.yaml").write_text(
        "data:\n"
        "  raw_path: data/sample.csv\n"
        "  target: target\n"
        "  exclude_columns: [id]\n"
        "  required_columns: [id, Age, Gender, target]\n"
        "  numeric_columns: [Age]\n"
        "  categorical_columns: [Gender]\n"
        "  allow_extra_columns: false\n"
        "  allow_missing_columns: false\n"
        "  allow_all_null_columns: false\n"
        "split:\n  train: 0.7\n  validation: 0.15\n  test: 0.15\n  random_seed: 42\n"
        "paths:\n  processed_dir: data/processed\n  output_dir: outputs\n"
        "audit:\n"
        "  report_dir: outputs/data_audit\n"
        "  imbalance_ratio_warning: 1.5\n"
        "  iqr_exempt_columns: []\n"
        "  suspicious_ranges:\n    Age: [0, 120]\n"
        "preprocessing:\n"
            "  numeric_imputation: median\n"
            "  categorical_imputation: most_frequent\n"
            "  scale_numeric: true\n"
            "  unknown_category_policy: ignore\n"
            "training:\n"
            "  sklearn_logistic:\n    max_iter: 20\n    candidates: [{C: 1.0}]\n"
            "  sklearn_mlp:\n    max_iter: 20\n    candidates: [{hidden_layer_sizes: [4]}]\n"
            "  manual_logistic:\n    max_epochs: 10\n"
            "  manual_mlp:\n    max_epochs: 10\n"
            "optimization:\n  enabled: true\n  scoring: f1_macro\n"
            "eda:\n  dpi: 100\n  scatter_sample_size: 20\n"
            "outputs:\n"
            "  figures_dir: outputs/eda/figures\n"
            "  metrics_dir: outputs/metrics\n"
            "  models_dir: outputs/models\n"
        "  reports_dir: outputs/reports\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("obesity_risk.workflows.get_project_root", lambda: tmp_path)
    assert main(["audit-data"]) == 0
    output = capsys.readouterr().out
    assert "原始数据保持不变" in output
    assert (tmp_path / "outputs/data_audit/data_audit.json").is_file()


# 验证 CLI 错误输出不包含 traceback
def test_cli_error_has_no_traceback(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr("obesity_risk.workflows.get_project_root", lambda: tmp_path)
    assert main(["audit-data"]) == 1
    output = capsys.readouterr().out
    assert "Traceback" not in output
