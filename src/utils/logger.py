from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Mapping

from loguru import logger as _loguru_logger


_CONFIGURED = False
_NAMESPACE = 'obesity-risk-system'
_NOTICE_LEVEL = 25
_CONSOLE_LOG_FORMAT = '{time:HH:mm:ss} | {extra[component]} | {message}'
_FILE_LOG_FORMAT = '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[component]} | {file.path}:{function}:{line} | {message}'
_VISIBLE_CONSOLE_COMPONENTS = {'main', 'web-server', 'desktop-gui', 'serving-inference'}


def _install_notice_level() -> None:
    try:
        _loguru_logger.level('NOTICE')
    except ValueError:
        _loguru_logger.level('NOTICE', no=_NOTICE_LEVEL, color='<cyan>')


def _component_name(name: str) -> str:
    return name.split('.')[-1] if name else _NAMESPACE


def _should_show_in_console(record: dict[str, Any]) -> bool:
    component = record['extra'].get('component', '')
    return record['level'].no >= logging.WARNING or component in _VISIBLE_CONSOLE_COMPONENTS


def configure_project_logging(
    project_root: str | Path,
    relative_log_path: str = 'output/logs/project.log',
) -> Path:
    """配置项目级日志输出，控制台保持精简，文件保留完整信息。"""
    global _CONFIGURED
    log_path = Path(project_root) / relative_log_path
    if _CONFIGURED:
        return log_path

    log_path.parent.mkdir(parents=True, exist_ok=True)
    _install_notice_level()
    _loguru_logger.remove()
    _loguru_logger.add(
        sys.stderr,
        level='INFO',
        format=_CONSOLE_LOG_FORMAT,
        colorize=True,
        enqueue=False,
        backtrace=False,
        diagnose=False,
        filter=_should_show_in_console,
    )
    _loguru_logger.add(
        log_path,
        level='DEBUG',
        format=_FILE_LOG_FORMAT,
        encoding='utf-8',
        rotation='10 MB',
        retention='14 days',
        compression='zip',
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )
    _CONFIGURED = True
    return log_path


def get_logger(name: str):
    """获取统一命名空间下的 logger。"""
    full_name = name if name.startswith(_NAMESPACE) else f'{_NAMESPACE}.{name}'
    return _loguru_logger.bind(component=_component_name(full_name))


def format_kv_pairs(payload: Mapping[str, Any]) -> str:
    return ' | '.join(f'{key}={value}' for key, value in payload.items())


def build_progress_message(label: str, current: int, total: int, extra: str = '', width: int = 24) -> str:
    safe_total = max(total, 1)
    safe_current = min(max(current, 0), safe_total)
    ratio = safe_current / safe_total
    filled = int(width * ratio)
    bar = '█' * filled + '░' * (width - filled)
    suffix = f' | {extra}' if extra else ''
    return f'{label} [{bar}] {ratio * 100:6.2f}% ({safe_current}/{safe_total}){suffix}'


def log_progress(logger: Any, label: str, current: int, total: int, extra: str = '') -> None:
    logger.info(build_progress_message(label, current, total, extra=extra))
