from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Mapping


_CONFIGURED = False
_NAMESPACE = 'obesity-risk-system'
_NOTICE_LEVEL = 25
_CONSOLE_FORMAT = '%(asctime)s | %(component)s | %(message)s'
_FILE_FORMAT = '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(component)s | %(pathname)s:%(funcName)s:%(lineno)d | %(message)s'
_VISIBLE_CONSOLE_COMPONENTS = {'main', 'desktop-gui', 'serving-inference'}


def _install_notice_level() -> None:
    logging.addLevelName(_NOTICE_LEVEL, 'NOTICE')
    if hasattr(logging.Logger, 'notice'):
        return

    def notice(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(_NOTICE_LEVEL):
            self._log(_NOTICE_LEVEL, message, args, **kwargs)

    logging.Logger.notice = notice  # type: ignore[attr-defined]


def _component_name(name: str) -> str:
    return name.split('.')[-1] if name else _NAMESPACE


def _format_message(message: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    if not args and not kwargs:
        return message
    try:
        return message.format(*args, **kwargs)
    except Exception:
        return message


def _should_show_in_console(record: logging.LogRecord) -> bool:
    component = getattr(record, 'component', '')
    return record.levelno >= logging.WARNING or component in _VISIBLE_CONSOLE_COMPONENTS


class _ProjectFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'component'):
            record.component = _NAMESPACE  # type: ignore[attr-defined]
        return super().format(record)


class _ProjectLogger:
    def __init__(self, logger: logging.Logger, component: str) -> None:
        self._logger = logger
        self._component = component

    @property
    def extra(self) -> dict[str, Any]:
        return {'component': self._component}

    def bind(self, **kwargs: Any) -> '_ProjectLogger':
        component = _component_name(str(kwargs.get('component', self._component)))
        return _ProjectLogger(self._logger, component)

    def log(self, level: Any, msg: str, *args: Any, **kwargs: Any) -> None:
        if isinstance(level, str):
            levelno = _NOTICE_LEVEL if level.upper() == 'NOTICE' else getattr(logging, level.upper(), logging.INFO)
        else:
            levelno = int(level)
        message = _format_message(msg, args, kwargs)
        self._logger.log(levelno, message, extra={'component': self._component})

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.ERROR, msg, *args, **kwargs)

    def notice(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(_NOTICE_LEVEL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        message = _format_message(msg, args, kwargs)
        self._logger.error(message, exc_info=True, extra={'component': self._component})

    def __getattr__(self, item: str) -> Any:
        return getattr(self._logger, item)


def _build_logger(component: str) -> _ProjectLogger:
    base_logger = logging.getLogger(f'{_NAMESPACE}.{component}')
    return _ProjectLogger(base_logger, component)


def configure_project_logging(
    project_root: str | Path,
    relative_log_path: str = 'output/logs/project.log',
) -> Path:
    """配置项目级日志输出，控制台保留关键信息，文件保留完整信息。"""
    global _CONFIGURED
    log_path = Path(project_root) / relative_log_path
    if _CONFIGURED:
        return log_path

    log_path.parent.mkdir(parents=True, exist_ok=True)
    _install_notice_level()

    root_logger = logging.getLogger(_NAMESPACE)
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)
    root_logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_ProjectFormatter(_CONSOLE_FORMAT, datefmt='%H:%M:%S'))
    console_handler.addFilter(_should_show_in_console)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_ProjectFormatter(_FILE_FORMAT, datefmt='%Y-%m-%d %H:%M:%S'))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    _CONFIGURED = True
    return log_path


def get_logger(name: str) -> _ProjectLogger:
    """获取统一命名空间下的 logger。"""
    full_name = name if name.startswith(_NAMESPACE) else f'{_NAMESPACE}.{name}'
    component = _component_name(full_name)
    return _build_logger(component)


def format_kv_pairs(payload: Mapping[str, Any]) -> str:
    return ' | '.join(f'{key}={value}' for key, value in payload.items())
