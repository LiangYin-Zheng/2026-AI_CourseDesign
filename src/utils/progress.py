from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.log.project import get_logger

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

    # 初始化进度条
    def __post_init__(self) -> None:
        self._logger = get_logger(self.logger_name)
        self._open_bar()

    # 推进一个步骤
    def advance(self, stage: str, detail: str = '') -> None:
        self.completed_units += 1
        extra = stage if not detail else f'{stage} | {detail}'
        if self._bar is not None:
            self._logger.debug('进度更新：{}/{} | {}', self.completed_units, self.total_units, extra)
            self._bar.text(stage)
            self._bar()
            return
        safe_total = max(int(self.total_units), 1)
        safe_current = min(max(self.completed_units, 0), safe_total)
        ratio = safe_current / safe_total
        filled = int(24 * ratio)
        bar = '█' * filled + '░' * (24 - filled)
        suffix = f' | {extra}' if extra else ''
        self._logger.info(
            '{} [{}] {:6.2f}% ({}/{}){}',
            self.label,
            bar,
            ratio * 100,
            safe_current,
            safe_total,
            suffix,
        )

    # 关闭进度条
    def close(self) -> None:
        if self._bar_cm is None:
            return
        self._bar_cm.__exit__(None, None, None)
        self._bar_cm = None
        self._bar = None

    # 打开 alive_progress 进度条
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

    # 支持 with 语法
    def __enter__(self) -> WorkflowProgress:
        return self

    # 退出时自动关闭
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
