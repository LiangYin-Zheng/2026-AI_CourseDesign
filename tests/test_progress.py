from __future__ import annotations

import unittest
from unittest.mock import patch

from src.utils.progress import WorkflowProgress


class _FakeProgressBar:
    def __init__(self) -> None:
        self.text_values: list[str] = []
        self.step_values: list[int] = []

    def text(self, value: str) -> None:
        self.text_values.append(value)

    def __call__(self, step: int = 1) -> None:
        self.step_values.append(step)


class _FakeProgressContext:
    def __init__(self, total: int, title: str, **kwargs) -> None:
        self.total = total
        self.title = title
        self.kwargs = kwargs
        self.bar = _FakeProgressBar()
        self.exited = False

    def __enter__(self) -> _FakeProgressBar:
        return self.bar

    def __exit__(self, exc_type, exc, tb) -> None:
        self.exited = True


class TestWorkflowProgress(unittest.TestCase):
    def test_workflow_progress_uses_alive_progress_context(self) -> None:
        context = _FakeProgressContext(total=3, title='训练进度')

        def fake_alive_bar(total: int, title: str, **kwargs):
            context.total = total
            context.title = title
            context.kwargs = kwargs
            return context

        with patch('src.utils.progress.alive_bar', side_effect=fake_alive_bar):
            progress = WorkflowProgress(total_units=3, label='训练进度', logger_name='unit-test')
            progress.advance('读取数据', 'rows=100')
            progress.advance('清洗数据')
            progress.close()

        self.assertEqual(context.total, 3)
        self.assertEqual(context.title, '训练进度')
        self.assertEqual(context.kwargs, {'dual_line': True, 'receipt': False, 'title_length': 18})
        self.assertEqual(context.bar.text_values, ['读取数据', '清洗数据'])
        self.assertEqual(context.bar.step_values, [1, 1])
        self.assertTrue(context.exited)
        self.assertEqual(progress.completed_units, 2)


if __name__ == '__main__':
    unittest.main()
