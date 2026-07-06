"""
模块作用：读取项目配置并提供统一访问入口。
输入输出：输入为 JSON 配置文件路径，输出为标准化后的配置字典。
依赖关系：依赖 pathlib、json，用于被主流程、训练流程和接口服务复用。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_project_config(config_path: str | Path = 'config/project_config.json') -> Dict[str, Any]:
    path = Path(config_path)
    with path.open('r', encoding='utf-8') as file:
        config = json.load(file)
    project_root = str(Path(__file__).resolve().parent.parent)
    config['project_root'] = project_root
    config.setdefault('output_dirs', {})
    config['output_dirs'].setdefault('logs', 'output/logs')
    return config
