from __future__ import annotations

import unittest

from src.reporting import render_analysis_markdown


class TestAnalysisReport(unittest.TestCase):
    def test_render_analysis_markdown_should_follow_summary_values(self) -> None:
        summary = {
            'overview': {'sample_count': 100, 'feature_count': 6, 'class_count': 2},
            'target_distribution': {'Class A': 70, 'Class B': 30},
            'target_ratio_percent': {'Class A': 70.0, 'Class B': 30.0},
            'numeric_separation_scores': {'age': 0.88, 'bmi': 0.63, 'weight_kg': 0.41},
            'key_findings': [
                'age 的类间区分度评分为 0.88，在当前样本中排名第 1。',
                'bmi 的类间区分度评分为 0.63，在当前样本中排名第 2。',
            ],
        }

        report = render_analysis_markdown(summary)

        self.assertIn('age、bmi、weight_kg', report)
        self.assertIn('标签分布存在一定偏斜', report)
        self.assertNotIn('BMI、体重、年龄和运动相关特征与肥胖等级的差异最明显。', report)


if __name__ == '__main__':
    unittest.main()
