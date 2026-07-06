from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.logger import get_logger, log_progress

try:  # pragma: no cover - 依赖是否安装取决于运行环境
    from alive_progress import alive_bar
except ImportError:  # pragma: no cover
    alive_bar = None


@dataclass
class WorkflowProgress:
    total_units: int
    label: str = '全流程进度'
    logger_name: str = 'workflow-progress'
    completed_units: int = 0
    _logger: object = field(init=False, repr=False)
    _bar_cm: Any = field(init=False, repr=False, default=None)
    _bar: Any = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        self._logger = get_logger(self.logger_name)
        self._open_bar()

    def advance(self, stage: str, detail: str = '') -> None:
        self.completed_units += 1
        extra = stage if not detail else f'{stage} | {detail}'
        if self._bar is not None:
            self._logger.debug('进度更新：{}/{} | {}', self.completed_units, self.total_units, extra)
            self._bar.text(stage)
            self._bar()
            return
        log_progress(self._logger, self.label, self.completed_units, self.total_units, extra)

    def close(self) -> None:
        if self._bar_cm is None:
            return
        self._bar_cm.__exit__(None, None, None)
        self._bar_cm = None
        self._bar = None

    def _open_bar(self) -> None:
        if alive_bar is None:
            return
        total_units = max(int(self.total_units), 1)
        self._bar_cm = alive_bar(
            total_units,
            title=self.label,
            dual_line=True,
            receipt=False,
            title_length=18,
        )
        self._bar = self._bar_cm.__enter__()

    def __enter__(self) -> WorkflowProgress:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
