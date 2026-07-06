from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Mapping

try:  # pragma: no cover - 是否安装 loguru 取决于当前环境
    from loguru import logger as _loguru_logger
except ImportError:  # pragma: no cover
    _loguru_logger = None


_CONFIGURED = False
_NAMESPACE = 'obesity-risk-system'
_NOTICE_LEVEL = 25
_CONSOLE_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(component)s] %(message)s'
_FILE_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(component)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
_LOGURU_CONSOLE_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[component]}</cyan> | {message}'
_LOGURU_FILE_FORMAT = '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[component]} | {file.path}:{function}:{line} | {message}'


def _install_notice_level() -> None:
    if logging.getLevelName(_NOTICE_LEVEL) != 'NOTICE':
        logging.addLevelName(_NOTICE_LEVEL, 'NOTICE')

        def notice(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
            if self.isEnabledFor(_NOTICE_LEVEL):
                self._log(_NOTICE_LEVEL, message, args, **kwargs)

        logging.Logger.notice = notice  # type: ignore[attr-defined]

    if _loguru_logger is not None:
        try:
            _loguru_logger.level('NOTICE')
        except ValueError:
            _loguru_logger.level('NOTICE', no=_NOTICE_LEVEL, color='<cyan>')


class _ComponentFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'component'):
            record.component = record.name.rsplit('.', 1)[-1]
        return True


class _LoguruInterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if _loguru_logger is None:
            return
        try:
            level_name = _loguru_logger.level(record.levelname).name
        except ValueError:
            level_name = record.levelno
        component = getattr(record, 'component', record.name.rsplit('.', 1)[-1])
        _loguru_logger.bind(component=component).opt(depth=6, exception=record.exc_info).log(level_name, record.getMessage())


class ProjectLoggerAdapter(logging.LoggerAdapter):
    def notice(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(_NOTICE_LEVEL, msg, *args, **kwargs)


def _component_name(name: str) -> str:
    return name.split('.')[-1] if name else _NAMESPACE


def _configure_with_stdlib(log_path: Path) -> None:
    root_logger = logging.getLogger(_NAMESPACE)
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.propagate = False

    formatter = logging.Formatter(_FILE_LOG_FORMAT, datefmt=_DATE_FORMAT)
    component_filter = _ComponentFilter()

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_LOG_FORMAT, datefmt=_DATE_FORMAT))
    console_handler.addFilter(component_filter)

    file_handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(component_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def _configure_with_loguru(log_path: Path) -> None:
    assert _loguru_logger is not None
    _install_notice_level()
    _loguru_logger.remove()
    _loguru_logger.add(
        sys.stderr,
        level='INFO',
        format=_LOGURU_CONSOLE_FORMAT,
        colorize=True,
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )
    _loguru_logger.add(
        log_path,
        level='DEBUG',
        format=_LOGURU_FILE_FORMAT,
        encoding='utf-8',
        rotation='10 MB',
        retention='14 days',
        compression='zip',
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )

    root_logger = logging.getLogger(_NAMESPACE)
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(_LoguruInterceptHandler())
    root_logger.propagate = False


def configure_project_logging(
    project_root: str | Path,
    relative_log_path: str = 'output/logs/project.log',
) -> Path:
    """配置项目级终端 + 文件日志，仅初始化一次。"""
    global _CONFIGURED
    log_path = Path(project_root) / relative_log_path
    if _CONFIGURED:
        return log_path

    log_path.parent.mkdir(parents=True, exist_ok=True)
    _install_notice_level()
    if _loguru_logger is not None:
        _configure_with_loguru(log_path)
    else:
        _configure_with_stdlib(log_path)
    _CONFIGURED = True
    return log_path


def get_logger(name: str) -> ProjectLoggerAdapter:
    """获取统一命名空间下的 logger。"""
    full_name = name if name.startswith(_NAMESPACE) else f'{_NAMESPACE}.{name}'
    base_logger = logging.getLogger(full_name)
    return ProjectLoggerAdapter(base_logger, {'component': _component_name(name)})


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
