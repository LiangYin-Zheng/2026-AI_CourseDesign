from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Mapping

try:  # pragma: no cover - 是否安装 loguru 取决于当前环境
    from loguru import logger as _loguru_logger
except ImportError:  # pragma: no cover
    _loguru_logger = None


_CONFIGURED = False
_NAMESPACE = 'obesity-risk-system'
_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
_LOGURU_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | {message}'


class _LoguruInterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if _loguru_logger is None:
            return
        try:
            level_name = _loguru_logger.level(record.levelname).name
        except ValueError:
            level_name = record.levelno
        _loguru_logger.bind(name=record.name).opt(depth=6, exception=record.exc_info).log(level_name, record.getMessage())


def _configure_with_stdlib(log_path: Path) -> None:
    root_logger = logging.getLogger(_NAMESPACE)
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False


def _configure_with_loguru(log_path: Path) -> None:
    assert _loguru_logger is not None
    _loguru_logger.remove()
    _loguru_logger.add(sys.stderr, level='INFO', format=_LOGURU_FORMAT, colorize=True)
    _loguru_logger.add(log_path, level='DEBUG', format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}', encoding='utf-8')

    root_logger = logging.getLogger(_NAMESPACE)
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(_LoguruInterceptHandler())
    root_logger.propagate = False


def configure_project_logging(project_root: str | Path, relative_log_path: str = 'output/logs/project.log') -> Path:
    """配置项目级终端 + 文件日志，仅初始化一次。"""
    global _CONFIGURED
    log_path = Path(project_root) / relative_log_path
    if _CONFIGURED:
        return log_path

    log_path.parent.mkdir(parents=True, exist_ok=True)
    if _loguru_logger is not None:
        _configure_with_loguru(log_path)
    else:
        _configure_with_stdlib(log_path)
    _CONFIGURED = True
    return log_path


def get_logger(name: str) -> logging.Logger:
    """获取统一命名空间下的 logger。"""
    if name.startswith(_NAMESPACE):
        return logging.getLogger(name)
    return logging.getLogger(f'{_NAMESPACE}.{name}')


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


def log_progress(logger: logging.Logger, label: str, current: int, total: int, extra: str = '') -> None:
    logger.info(build_progress_message(label, current, total, extra=extra))
