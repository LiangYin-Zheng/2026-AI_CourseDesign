from __future__ import annotations

import unittest

from src.core.contracts import ARTIFACT_GROUP_NAMES, DEFAULT_TRAINING_MODE, FIELD_DEFINITIONS, FLOAT_FIELDS, INTEGER_FIELDS, SAMPLE_FIELD_NAMES, TRAINING_MODE_OPTIONS


class TestContracts(unittest.TestCase):
    def test_training_modes_should_come_from_yaml(self) -> None:
        values = [item['value'] for item in TRAINING_MODE_OPTIONS]
        self.assertEqual(DEFAULT_TRAINING_MODE, 'train')
        self.assertIn('artifacts-only', values)
        self.assertIn('train-manual', values)

    def test_field_definitions_should_come_from_yaml(self) -> None:
        self.assertIn(('gender', '性别', 'Female', ['Female', 'Male']), FIELD_DEFINITIONS)
        self.assertIn('age', FLOAT_FIELDS)
        self.assertIn('family_history_with_overweight', INTEGER_FIELDS)
        self.assertIn('transportation_mode', SAMPLE_FIELD_NAMES)

    def test_artifact_groups_should_have_display_order(self) -> None:
        self.assertEqual(ARTIFACT_GROUP_NAMES, ['analysis', 'evaluation', 'figures', 'logs', 'models', 'predictions', 'reports'])


if __name__ == '__main__':
    unittest.main()
