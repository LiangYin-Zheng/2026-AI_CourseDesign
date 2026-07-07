from __future__ import annotations

import unittest

from src.evaluation.reporter import render_family_comparison_report, render_model_report


class TestReporter(unittest.TestCase):
    def test_render_model_report_should_use_current_metrics(self) -> None:
        model_results = {
            'baseline': {
                'logistic_regression': {'test_metrics': {'accuracy': 0.62, 'macro_precision': 0.60, 'macro_recall': 0.61, 'macro_f1': 0.605}},
                'mlp_classifier': {'test_metrics': {'accuracy': 0.64, 'macro_precision': 0.63, 'macro_recall': 0.62, 'macro_f1': 0.625}},
            },
            'optimized': {
                'logistic_regression': {'test_metrics': {'accuracy': 0.71, 'macro_precision': 0.70, 'macro_recall': 0.69, 'macro_f1': 0.695}},
                'mlp_classifier': {'test_metrics': {'accuracy': 0.76, 'macro_precision': 0.75, 'macro_recall': 0.74, 'macro_f1': 0.745}},
            },
        }

        report = render_model_report(model_results, family_name='sklearn 模型')

        self.assertIn('当前优化后表现最好的模型是 mlp_classifier', report)
        self.assertIn('相比基线，mlp_classifier 的 macro_f1 变化为 +0.1200', report)
        self.assertNotIn('优化模型优先比较测试集 Macro F1', report)

    def test_render_family_comparison_report_should_follow_ranked_results(self) -> None:
        summary = {
            'project_name': 'demo',
            'training_mode': 'train',
            'status': 'ready',
            'message': 'ok',
            'dataset': {'sample_count': 1000, 'class_count': 4, 'split': {'train': 600, 'validation': 200, 'test': 200}},
            'comparison_rows': [
                {'family': 'sklearn', 'name': 'logistic_regression', 'metrics': {'accuracy': 0.82, 'macro_precision': 0.81, 'macro_recall': 0.80, 'macro_f1': 0.805}},
                {'family': 'manual', 'name': 'neural_network', 'metrics': {'accuracy': 0.85, 'macro_precision': 0.84, 'macro_recall': 0.83, 'macro_f1': 0.835}},
            ],
            'parameter_tables': [],
            'recommended_model': {'family': 'manual', 'name': 'neural_network', 'macro_f1': 0.835},
            'artifacts': {},
            'analysis_summary': {},
            'families': {},
        }

        report = render_family_comparison_report(summary)

        self.assertIn('当前最优模型是 manual / neural_network', report)
        self.assertIn('领先幅度为 0.0300', report)
        self.assertIn('手搓路线', report)
        self.assertNotIn('工程化路线更适合展示标准化训练、参数搜索和可重复实验流程。', report)


if __name__ == '__main__':
    unittest.main()
