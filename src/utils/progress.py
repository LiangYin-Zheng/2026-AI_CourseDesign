from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.logger import get_logger, log_progress


@dataclass
class WorkflowProgress:
    total_units: int
    label: str = '全流程进度'
    logger_name: str = 'workflow-progress'
    completed_units: int = 0
    _logger: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._logger = get_logger(self.logger_name)

    def advance(self, stage: str, detail: str = '') -> None:
        self.completed_units += 1
        extra = stage if not detail else f'{stage} | {detail}'
        log_progress(self._logger, self.label, self.completed_units, self.total_units, extra)

