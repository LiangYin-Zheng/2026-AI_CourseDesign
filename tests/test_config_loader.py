from __future__ import annotations

import unittest

from src.core.config import load_project_config


class TestConfigLoader(unittest.TestCase):
    def test_load_project_config_should_merge_yaml_sources(self) -> None:
        config = load_project_config()
        self.assertEqual(config['project_name'], '肥胖风险预测系统设计')
        self.assertEqual(config['output_dirs']['logs'], 'output/logs')
        self.assertIn('ui', config)
        self.assertEqual(config['ui']['app']['title'], '肥胖风险预测系统 · 本地智能管理台')
        self.assertGreater(len(config['ui']['form_fields']), 0)


if __name__ == '__main__':
    unittest.main()
