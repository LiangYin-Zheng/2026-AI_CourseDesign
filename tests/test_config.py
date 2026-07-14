from pathlib import Path

import pytest

from obesity_risk.config import load_config


VALID_CONFIG = (
    "data:\n"
    "  raw_path: data/obesity_level.csv\n"
    "  target: 0be1dad\n"
    "  exclude_columns: [id]\n"
    "  required_columns: [id, Gender, Age, Height, Weight, family_history_with_overweight, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, SCC, FAF, TUE, CALC, MTRANS, 0be1dad]\n"
    "  numeric_columns: [Age, Height, Weight, FCVC, NCP, CH2O, FAF, TUE]\n"
    "  categorical_columns: [Gender, family_history_with_overweight, FAVC, CAEC, SMOKE, SCC, CALC, MTRANS]\n"
    "  allow_extra_columns: false\n"
    "  allow_missing_columns: false\n"
    "  allow_all_null_columns: false\n"
    "split:\n"
    "  train: 0.70\n"
    "  validation: 0.15\n"
    "  test: 0.15\n"
    "  random_seed: 42\n"
    "paths:\n"
    "  processed_dir: data/processed\n"
    "  output_dir: outputs\n"
    "audit:\n"
    "  report_dir: outputs/data_audit\n"
    "  imbalance_ratio_warning: 1.5\n"
    "  iqr_exempt_columns: [NCP]\n"
    "  suspicious_ranges:\n"
    "    Age: [0, 120]\n"
    "    Height: [0.5, 2.5]\n"
    "    Weight: [2, 500]\n"
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
    "  reports_dir: outputs/reports\n"
)


# 写入测试使用的临时配置
def write_config(tmp_path: Path, content: str = VALID_CONFIG) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


# 验证合法配置可以读取
def test_load_valid_config(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    assert config["data"]["target"] == "0be1dad"
    assert config["split"]["random_seed"] == 42


# 验证配置文件缺失时给出明确错误
def test_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="配置文件不存在"):
        load_config(tmp_path / "missing.yaml")


# 验证配置根节点必须为字典
def test_config_root_must_be_dict(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="配置根节点必须是字典"):
        load_config(write_config(tmp_path, "- item\n"))


# 验证缺失必需配置字段会被拒绝
def test_missing_required_field(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  target: 0be1dad\n", "")
    with pytest.raises(ValueError, match="data.target"):
        load_config(write_config(tmp_path, content))


# 验证数据划分比例之和必须为 1
def test_split_ratios_must_sum_to_one(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  train: 0.70", "  train: 0.80")
    with pytest.raises(ValueError, match="比例之和必须为 1"):
        load_config(write_config(tmp_path, content))


# 验证随机种子必须为整数
def test_random_seed_must_be_integer(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  random_seed: 42", "  random_seed: true")
    with pytest.raises(ValueError, match="随机种子必须是整数"):
        load_config(write_config(tmp_path, content))


# 验证排除字段必须包含 id
def test_exclude_columns_must_contain_id(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  exclude_columns: [id]", "  exclude_columns: []")
    with pytest.raises(ValueError, match="排除字段必须包含 id"):
        load_config(write_config(tmp_path, content))


# 验证审查报告目录必须是相对路径
def test_audit_report_dir_must_be_relative(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace(
        "  report_dir: outputs/data_audit", "  report_dir: /private/tmp/audit"
    )
    with pytest.raises(ValueError, match="审查报告目录必须是项目内相对路径"):
        load_config(write_config(tmp_path, content))


# 验证 Schema 字段列表不能重复
def test_schema_columns_must_be_unique(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace(
        "  numeric_columns: [Age, Height, Weight, FCVC, NCP, CH2O, FAF, TUE]",
        "  numeric_columns: [Age, Age]",
    )
    with pytest.raises(ValueError, match="数值字段不能重复"):
        load_config(write_config(tmp_path, content))


# 验证 IQR 豁免字段必须属于数值字段
def test_iqr_exempt_columns_must_be_numeric(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  iqr_exempt_columns: [NCP]", "  iqr_exempt_columns: [Gender]")
    with pytest.raises(ValueError, match="IQR 豁免字段必须属于数值字段"):
        load_config(write_config(tmp_path, content))
