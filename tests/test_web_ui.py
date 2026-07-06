from __future__ import annotations

import unittest

from src.interfaces.web.templates import build_index_page


class TestWebUiTemplate(unittest.TestCase):
    def test_build_index_page_should_render_application_shell(self) -> None:
        html = build_index_page({
            'project_name': 'demo',
            'status': 'ready',
            'message': 'ok',
            'training_mode': 'train',
            'sample_fields': [],
            'available_training_modes': [],
        })

        self.assertIn('<aside class="sidebar">', html)
        self.assertIn('data-view="overview"', html)
        self.assertIn('data-view="artifacts"', html)
        self.assertIn('function showView(viewName)', html)
        self.assertIn('id="artifact-preview"', html)
        self.assertIn('查看原图', html)
        self.assertIn('/artifacts/', html)
        self.assertIn('submitPrediction()', html)


if __name__ == '__main__':
    unittest.main()
