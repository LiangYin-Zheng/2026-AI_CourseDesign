from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.utils import logger as project_logger


class TestProjectLogger(unittest.TestCase):
    def test_configure_project_logging_should_write_structured_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_logger._CONFIGURED = False
            log_path = project_logger.configure_project_logging(tmpdir, 'logs/project.log')
            self.assertEqual(log_path, Path(tmpdir) / 'logs/project.log')

            logger = project_logger.get_logger('unit-test')
            logger.notice('notice event %s', 'ready')
            logger.info('info event %s', 'done')

            content = log_path.read_text(encoding='utf-8')
            self.assertIn('unit-test', content)
            self.assertIn('NOTICE', content)
            self.assertIn('info event done', content)


if __name__ == '__main__':
    unittest.main()
