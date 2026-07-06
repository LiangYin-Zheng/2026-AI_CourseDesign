from __future__ import annotations

import unittest

from src.config import load_project_config
from src.data_processing.cleaner import clean_dataset
from src.data_processing.loader import load_dataset
from src.data_processing.splitter import stratified_split_dataframe
from src.models.sklearn_trainer import train_sklearn_models


class TestSklearnPipeline(unittest.TestCase):
    """覆盖 sklearn 版本最小可运行链路。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_project_config()
        cls.config['sklearn_models']['optimization_grids']['logistic_regression'] = {
            'C': [1.0],
            'max_iter': [200],
            'class_weight': [None],
        }
        cls.config['sklearn_models']['optimization_grids']['mlp_classifier'] = {
            'hidden_units': [24],
            'learning_rate_init': [0.001],
            'alpha': [0.0005],
            'epochs': [20],
        }
        cls.config['sklearn_models']['baseline']['mlp_classifier']['epochs'] = 20
        raw_df = load_dataset(cls.config['data_path']).head(800)
        cls.clean_df = clean_dataset(raw_df, cls.config)

    def test_train_sklearn_models_should_produce_metrics(self) -> None:
        datasets = stratified_split_dataframe(
            self.clean_df,
            self.config['target_column'],
            self.config['test_size'],
            self.config['validation_size'],
            self.config['random_seed'],
        )
        training_summary = train_sklearn_models(datasets, self.config)
        logistic_metrics = training_summary['model_results']['optimized']['logistic_regression']['test_metrics']
        mlp_metrics = training_summary['model_results']['optimized']['mlp_classifier']['test_metrics']
        self.assertGreater(logistic_metrics['accuracy'], 0.45)
        self.assertGreater(mlp_metrics['accuracy'], 0.45)
        self.assertIn('macro_roc_auc_ovr', mlp_metrics)


if __name__ == '__main__':
    unittest.main()
