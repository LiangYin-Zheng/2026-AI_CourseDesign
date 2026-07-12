from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(path: str | Path, base: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


@lru_cache(maxsize=1)
def _load_yaml(path: str) -> Dict[str, Any]:
    source_path = Path(path)
    with source_path.open('r', encoding='utf-8') as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f'配置文件格式错误：{source_path}')
    return data


def load_project_config(
    config_path: str | Path = 'config/project.yaml',
) -> Dict[str, Any]:
    project_root = _project_root()
    project_config_path = _resolve_path(config_path, project_root)
    config = dict(_load_yaml(str(project_config_path)))
    ui_config = dict(config.get('ui', {}))

    config.setdefault('output_dirs', {})
    config['output_dirs'].setdefault('logs', 'output/logs')
    config['project_root'] = str(project_root)
    config['ui'] = ui_config
    return config
