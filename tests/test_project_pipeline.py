from __future__ import annotations

import unittest

from src.config import load_project_config
from src.data_processing.cleaner import clean_dataset
from src.data_processing.loader import load_dataset
from src.data_processing.splitter import stratified_split_dataframe
from src.evaluation.metrics import evaluate_predictions
from src.features.preprocessor import TabularPreprocessor
from src.models.logistic_regression import SoftmaxLogisticRegression
from src.models.neural_network import SimpleNeuralNetwork


class TestProjectPipeline(unittest.TestCase):
    """覆盖课程项目关键最小链路的测试集合。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_project_config()
        raw_df = load_dataset(cls.config['data_path']).head(1200)
        cls.clean_df = clean_dataset(raw_df, cls.config)

    def test_clean_dataset_should_normalize_columns_and_labels(self) -> None:
        self.assertIn('obesity_level', self.clean_df.columns)
        self.assertIn('bmi', self.clean_df.columns)
        self.assertNotIn('0be1dad', self.clean_df.columns)
        self.assertNotIn('0rmal_Weight', set(self.clean_df['obesity_level'].unique()))

    def test_preprocessor_should_generate_feature_matrix(self) -> None:
        datasets = stratified_split_dataframe(
            self.clean_df,
            self.config['target_column'],
            self.config['test_size'],
            self.config['validation_size'],
            self.config['random_seed'],
        )
        preprocessor = TabularPreprocessor(
            numeric_features=self.config['numeric_features'],
            categorical_features=self.config['categorical_features'],
        )
        preprocessor.fit(datasets['train'], self.config['target_column'])
        X_train = preprocessor.transform(datasets['train'])
        self.assertEqual(X_train.shape[0], len(datasets['train']))
        self.assertEqual(X_train.shape[1], len(preprocessor.feature_names_))

    def test_models_should_fit_on_small_subset(self) -> None:
        datasets = stratified_split_dataframe(
            self.clean_df,
            self.config['target_column'],
            self.config['test_size'],
            self.config['validation_size'],
            self.config['random_seed'],
        )
        preprocessor = TabularPreprocessor(
            numeric_features=self.config['numeric_features'],
            categorical_features=self.config['categorical_features'],
        )
        preprocessor.fit(datasets['train'], self.config['target_column'])
        X_train = preprocessor.transform(datasets['train'])
        y_train = preprocessor.encode_target(datasets['train'][self.config['target_column']])
        X_validation = preprocessor.transform(datasets['validation'])
        y_validation = preprocessor.encode_target(datasets['validation'][self.config['target_column']])
        X_test = preprocessor.transform(datasets['test'])
        y_test = preprocessor.encode_target(datasets['test'][self.config['target_column']])

        logistic_model = SoftmaxLogisticRegression(learning_rate=0.08, epochs=80, reg_strength=0.0008)
        logistic_model.fit(X_train, y_train, X_validation, y_validation)
        logistic_metrics = evaluate_predictions(y_test, logistic_model.predict(X_test))
        self.assertGreater(logistic_metrics['accuracy'], 0.45)

        neural_model = SimpleNeuralNetwork(hidden_units=20, learning_rate=0.03, epochs=90, l2_strength=0.0005)
        neural_model.fit(X_train, y_train, X_validation, y_validation)
        neural_metrics = evaluate_predictions(y_test, neural_model.predict(X_test))
        self.assertGreater(neural_metrics['accuracy'], 0.40)


if __name__ == '__main__':
    unittest.main()
