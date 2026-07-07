from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# 加载项目配置文件
def load_project_config(config_path: str | Path = 'config/project_config.json') -> Dict[str, Any]:
    # 读取 JSON 配置
    path = Path(config_path)
    with path.open('r', encoding='utf-8') as file:
        config = json.load(file)
    # 注入项目根目录
    project_root = str(Path(__file__).resolve().parent.parent)
    config['project_root'] = project_root
    # 补齐输出目录默认值
    config.setdefault('output_dirs', {})
    config['output_dirs'].setdefault('logs', 'output/logs')
    return config
