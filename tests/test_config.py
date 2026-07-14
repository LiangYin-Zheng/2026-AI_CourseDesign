from pathlib import Path

import pytest

from obesity_risk.config import load_config


VALID_CONFIG = (
    "data:\n"
    "  raw_path: data/obesity_level.csv\n"
    "  target: 0be1dad\n"
    "  exclude_columns: [id]\n"
    "split:\n"
    "  train: 0.70\n"
    "  validation: 0.15\n"
    "  test: 0.15\n"
    "  random_seed: 42\n"
    "paths:\n"
    "  processed_dir: data/processed\n"
    "  output_dir: outputs\n"
)


# 写入测试使用的临时配置
def write_config(tmp_path: Path, content: str = VALID_CONFIG) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_load_valid_config(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))
    assert config["data"]["target"] == "0be1dad"
    assert config["split"]["random_seed"] == 42


def test_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="配置文件不存在"):
        load_config(tmp_path / "missing.yaml")


def test_config_root_must_be_dict(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="配置根节点必须是字典"):
        load_config(write_config(tmp_path, "- item\n"))


def test_missing_required_field(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  target: 0be1dad\n", "")
    with pytest.raises(ValueError, match="data.target"):
        load_config(write_config(tmp_path, content))


def test_split_ratios_must_sum_to_one(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  train: 0.70", "  train: 0.80")
    with pytest.raises(ValueError, match="比例之和必须为 1"):
        load_config(write_config(tmp_path, content))


def test_random_seed_must_be_integer(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  random_seed: 42", "  random_seed: true")
    with pytest.raises(ValueError, match="随机种子必须是整数"):
        load_config(write_config(tmp_path, content))


def test_exclude_columns_must_contain_id(tmp_path: Path) -> None:
    content = VALID_CONFIG.replace("  exclude_columns: [id]", "  exclude_columns: []")
    with pytest.raises(ValueError, match="排除字段必须包含 id"):
        load_config(write_config(tmp_path, content))
