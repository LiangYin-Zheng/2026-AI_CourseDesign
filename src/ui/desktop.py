from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pyqtgraph as pg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, CardWidget, PrimaryPushButton, PushButton, SubtitleLabel, TableWidget, TextEdit

from src.core.config import load_project_config
from src.core.contracts import get_form_fields, get_page_copy, get_training_mode_options
from src.log.project import configure_project_logging
from src.serving.inference import load_dashboard_bundle, load_inference_bundle, predict_single
from src.utils.file_utils import write_json


class StatusBanner(CardWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        on_refresh: Callable[[], None] | None = None,
        on_train: Callable[[], None] | None = None,
        on_predict: Callable[[], None] | None = None,
        on_export: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = SubtitleLabel(title, self)
        self._subtitle = BodyLabel(subtitle, self)
        self._meta = BodyLabel('', self)
        self._status = BodyLabel('', self)
        self._mode = BodyLabel('', self)
        self._recommended = BodyLabel('', self)
        self._sample_count = BodyLabel('', self)

        self._refresh_button = PushButton('刷新摘要', self)
        self._train_button = PrimaryPushButton('启动训练', self)
        self._predict_button = PushButton('执行预测', self)
        self._export_button = PushButton('导出快照', self)

        if on_refresh is not None:
            self._refresh_button.clicked.connect(on_refresh)
        if on_train is not None:
            self._train_button.clicked.connect(on_train)
        if on_predict is not None:
            self._predict_button.clicked.connect(on_predict)
        if on_export is not None:
            self._export_button.clicked.connect(on_export)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(18)

        text_box = QVBoxLayout()
        text_box.setSpacing(4)
        text_box.addWidget(self._title)
        text_box.addWidget(self._subtitle)
        text_box.addWidget(self._meta)
        layout.addLayout(text_box, 2)

        summary_box = QVBoxLayout()
        summary_box.setSpacing(4)
        summary_box.addWidget(self._status)
        summary_box.addWidget(self._mode)
        summary_box.addWidget(self._recommended)
        summary_box.addWidget(self._sample_count)
        layout.addLayout(summary_box, 1)

        action_box = QVBoxLayout()
        action_box.setSpacing(8)
        action_box.addWidget(self._refresh_button)
        action_box.addWidget(self._train_button)
        action_box.addWidget(self._predict_button)
        action_box.addWidget(self._export_button)
        action_box.addStretch(1)
        layout.addLayout(action_box, 0)

    def set_snapshot(self, dashboard: dict[str, Any]) -> None:
        overview = dashboard.get('overview', {})
        dataset = dashboard.get('dataset', {})
        self._meta.setText(f"生成时间：{dashboard.get('generated_at', '-')}")
        self._status.setText(f"状态：{dashboard.get('status', '-')}")
        self._mode.setText(f"训练路线：{overview.get('training_mode_label', '-')}")
        recommended = overview.get('recommended_model', {})
        self._recommended.setText(f"推荐模型：{recommended.get('family', '-')}/{recommended.get('name', '-')}")
        self._sample_count.setText(f"样本量：{dataset.get('sample_count', '-')}")


class DashboardPage(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        on_refresh: Callable[[], None] | None = None,
        on_train: Callable[[], None] | None = None,
        on_predict: Callable[[], None] | None = None,
        on_export: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.banner = StatusBanner(title, subtitle, on_refresh, on_train, on_predict, on_export, self)
        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        layout.addWidget(self.banner)
        layout.addWidget(self.body, 1)

    def refresh_snapshot(self, dashboard: dict[str, Any], bundle: dict[str, Any]) -> None:
        self.banner.set_snapshot(dashboard)


class MetricCard(CardWidget):
    def __init__(self, title: str, value: str = '-', detail: str = '', parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = BodyLabel(title, self)
        self._value = SubtitleLabel(value, self)
        self._detail = BodyLabel(detail, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._detail)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_detail(self, detail: str) -> None:
        self._detail.setText(detail)


class FieldFormWidget(CardWidget):
    def __init__(self, fields: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fields = fields
        self._inputs: dict[str, QWidget] = {}

        self._container = QWidget(self)
        self._layout = QGridLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setHorizontalSpacing(14)
        self._layout.setVerticalSpacing(12)

        wrapper = QScrollArea(self)
        wrapper.setWidgetResizable(True)
        wrapper.setFrameShape(QFrame.NoFrame)
        wrapper.setWidget(self._container)

        outer = QGridLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.addWidget(wrapper, 0, 0)

        self._build_form()

    def _build_form(self) -> None:
        for index, field in enumerate(self._fields):
            row = index // 2
            column = index % 2
            label = field['label']
            value_type = field.get('value_type', 'text')
            default = field.get('default')
            options = field.get('options') or []

            form = QFormLayout()
            form.setLabelAlignment(Qt.AlignLeft)
            cell = QWidget(self._container)
            cell.setLayout(form)

            if options:
                editor = QComboBox(cell)
                editor.addItems([str(option) for option in options])
                editor.setCurrentText(str(default))
            elif value_type == 'int':
                editor = QSpinBox(cell)
                editor.setRange(-999999, 999999)
                editor.setValue(int(default))
            elif value_type == 'float':
                editor = QDoubleSpinBox(cell)
                editor.setRange(-999999.0, 999999.0)
                editor.setDecimals(4)
                editor.setValue(float(default))
            else:
                editor = QLineEdit(cell)
                editor.setText(str(default))

            form.addRow(label, editor)
            self._inputs[field['name']] = editor
            self._layout.addWidget(cell, row, column)

    def values(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for field in self._fields:
            name = field['name']
            widget = self._inputs[name]
            value_type = field.get('value_type', 'text')
            if isinstance(widget, QComboBox):
                payload[name] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                payload[name] = int(widget.value())
            elif isinstance(widget, QDoubleSpinBox):
                payload[name] = float(widget.value())
            else:
                payload[name] = widget.text()
            if value_type == 'int' and not isinstance(payload[name], int):
                payload[name] = int(float(payload[name]))
        return payload

    def reset(self) -> None:
        for field in self._fields:
            widget = self._inputs[field['name']]
            default = field.get('default')
            if isinstance(widget, QComboBox):
                widget.setCurrentText(str(default))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(default))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(default))
            else:
                widget.setText(str(default))


class ModelTableWidget(TableWidget):
    def __init__(self, columns: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(False)

    def set_rows(self, rows: list[list[Any]]) -> None:
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.setItem(row_index, column_index, self._make_item(value))
        self.resizeColumnsToContents()

    @staticmethod
    def _make_item(value: Any):
        return QTableWidgetItem(str(value))


class OverviewPage(DashboardPage):
    def __init__(
        self,
        title: str,
        subtitle: str,
        on_refresh=None,
        on_train=None,
        on_predict=None,
        on_export=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, subtitle, on_refresh=on_refresh, on_train=on_train, on_predict=on_predict, on_export=on_export, parent=parent)
        self._metrics_box = QWidget(self.body)
        self._metrics_layout = QGridLayout(self._metrics_box)
        self._metrics_layout.setContentsMargins(0, 0, 0, 0)
        self._metrics_layout.setHorizontalSpacing(12)
        self._metrics_layout.setVerticalSpacing(12)

        self._chart = pg.PlotWidget(self.body)
        self._chart.showGrid(x=False, y=True, alpha=0.2)
        self._chart.setBackground(None)

        self._artifact_hint = QLabel('等待加载训练摘要。', self.body)

        self.body_layout.addWidget(self._metrics_box)
        self.body_layout.addWidget(self._chart, 2)
        self.body_layout.addWidget(self._artifact_hint)

        self._cards = [
            MetricCard('项目名称'),
            MetricCard('样本量'),
            MetricCard('类别数'),
            MetricCard('推荐模型'),
            MetricCard('Macro F1'),
            MetricCard('训练状态'),
        ]
        for index, card in enumerate(self._cards):
            self._metrics_layout.addWidget(card, 0, index)

    def refresh_snapshot(self, dashboard: dict[str, Any], bundle: dict[str, Any]) -> None:
        super().refresh_snapshot(dashboard, bundle)
        overview = dashboard.get('overview', {})
        dataset = dashboard.get('dataset', {})
        values = [
            overview.get('project_name', '-'),
            dataset.get('sample_count', '-'),
            dataset.get('class_count', '-'),
            overview.get('recommended_model', {}).get('label', '-'),
            overview.get('best_macro_f1', '-'),
            overview.get('training_status', '-'),
        ]
        details = [
            '项目总览',
            f"训练路线：{overview.get('training_mode_label', '-')}",
            f"标签：{dataset.get('target_column', '-')}",
            f"推荐：{overview.get('recommended_model', {}).get('family', '-')}/{overview.get('recommended_model', {}).get('name', '-')}",
            f"更新时间：{dashboard.get('generated_at', '-')}",
            f"状态：{dashboard.get('status', '-')}",
        ]
        for card, value, detail in zip(self._cards, values, details):
            card.set_value(str(value))
            card.set_detail(detail)

        self._render_chart(dashboard)
        self._artifact_hint.setText(self._artifact_summary(dashboard))

    def _render_chart(self, dashboard: dict[str, Any]) -> None:
        self._chart.clear()
        rows = dashboard.get('comparison_rows', [])[:6]
        if not rows:
            self._chart.addItem(pg.TextItem('暂无模型对比数据'))
            return
        x = list(range(len(rows)))
        values = [float(row.get('metrics', {}).get('macro_f1', 0.0) or 0.0) for row in rows]
        labels = [f"{row.get('family', '-')}/{row.get('name', '-')}" for row in rows]
        bar = pg.BarGraphItem(x=x, height=values, width=0.6, brush=pg.mkBrush('#0f766e'))
        self._chart.addItem(bar)
        self._chart.getAxis('bottom').setTicks([list(zip(x, labels))])
        self._chart.setLabel('left', 'Macro F1')

    @staticmethod
    def _artifact_summary(dashboard: dict[str, Any]) -> str:
        groups = dashboard.get('artifact_groups', [])
        summary = [f"{item.get('label', item.get('name', '-'))}: {item.get('file_count', 0)}" for item in groups]
        return '产物分组：' + ' | '.join(summary)


class ComparisonPage(DashboardPage):
    def __init__(
        self,
        title: str,
        subtitle: str,
        on_refresh=None,
        on_train=None,
        on_predict=None,
        on_export=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, subtitle, on_refresh=on_refresh, on_train=on_train, on_predict=on_predict, on_export=on_export, parent=parent)
        self._table = ModelTableWidget(['家族', '模型', 'Accuracy', 'Macro Precision', 'Macro Recall', 'Macro F1'], self.body)
        self._param_table = ModelTableWidget(['家族', '模型', '参数'], self.body)
        self._chart = pg.PlotWidget(self.body)
        self._chart.showGrid(x=False, y=True, alpha=0.2)

        split = QWidget(self.body)
        split_layout = QHBoxLayout(split)
        split_layout.setContentsMargins(0, 0, 0, 0)
        left = QWidget(split)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._table, 2)
        left_layout.addWidget(self._chart, 1)
        right = QWidget(split)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self._param_table, 1)
        split_layout.addWidget(left, 3)
        split_layout.addWidget(right, 2)
        self.body_layout.addWidget(split, 1)

    def refresh_snapshot(self, dashboard: dict[str, Any], bundle: dict[str, Any]) -> None:
        super().refresh_snapshot(dashboard, bundle)
        rows = dashboard.get('comparison_rows', [])
        self._table.set_rows([
            [
                row.get('family', '-'),
                row.get('name', '-'),
                row.get('metrics', {}).get('accuracy', '-'),
                row.get('metrics', {}).get('macro_precision', '-'),
                row.get('metrics', {}).get('macro_recall', '-'),
                row.get('metrics', {}).get('macro_f1', '-'),
            ]
            for row in rows
        ])
        self._param_table.set_rows([
            [row.get('family', '-'), row.get('name', '-'), row.get('parameters', {})]
            for row in dashboard.get('parameter_rows', [])
        ])
        self._render_chart(rows)

    def _render_chart(self, rows: list[dict[str, Any]]) -> None:
        self._chart.clear()
        if not rows:
            return
        x = list(range(len(rows)))
        values = [float(row.get('metrics', {}).get('macro_f1', 0.0) or 0.0) for row in rows]
        labels = [row.get('name', '-') for row in rows]
        self._chart.addItem(pg.BarGraphItem(x=x, height=values, width=0.55, brush=pg.mkBrush('#f97316')))
        self._chart.getAxis('bottom').setTicks([list(zip(x, labels))])
        self._chart.setLabel('left', 'Macro F1')


class PredictionPage(DashboardPage):
    def __init__(
        self,
        title: str,
        subtitle: str,
        fields: list[dict[str, Any]],
        on_predict: Callable[[], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        on_train: Callable[[], None] | None = None,
        on_export: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, subtitle, on_refresh=on_refresh, on_train=on_train, on_predict=on_predict, on_export=on_export, parent=parent)
        self.form = FieldFormWidget(fields, self.body)
        self._result = TextEdit(self.body)
        self._result.setReadOnly(True)
        self._predict = PushButton('执行预测', self.body)
        self._reset = PushButton('重置表单', self.body)
        if on_predict is not None:
            self._predict.clicked.connect(on_predict)
        self._reset.clicked.connect(self.form.reset)

        button_row = QWidget(self.body)
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self._predict)
        button_layout.addWidget(self._reset)
        button_layout.addStretch(1)

        self.body_layout.addWidget(self.form, 2)
        self.body_layout.addWidget(button_row)
        self.body_layout.addWidget(QLabel('预测结果', self.body))
        self.body_layout.addWidget(self._result, 1)

    def payload(self) -> dict[str, Any]:
        return self.form.values()

    def set_result(self, text: str) -> None:
        self._result.setPlainText(text)


class TrainingPage(DashboardPage):
    def __init__(
        self,
        title: str,
        subtitle: str,
        training_modes: list[dict[str, Any]],
        on_launch: Callable[[], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        on_predict: Callable[[], None] | None = None,
        on_export: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, subtitle, on_refresh=on_refresh, on_train=on_launch, on_predict=on_predict, on_export=on_export, parent=parent)
        self._modes = training_modes
        self._mode_combo = QComboBox(self.body)
        self._mode_combo.addItems([item['label'] for item in training_modes])
        self._mode_combo.currentIndexChanged.connect(self._update_mode_text)
        self._mode_text = QLabel(self.body)
        self._progress = QProgressBar(self.body)
        self._log = TextEdit(self.body)
        self._log.setReadOnly(True)
        self._launch = PushButton('启动训练', self.body)
        if on_launch is not None:
            self._launch.clicked.connect(on_launch)

        top_box = QWidget(self.body)
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(BodyLabel('训练路线', top_box))
        top_layout.addWidget(self._mode_combo, 1)
        top_layout.addWidget(self._launch)

        self.body_layout.addWidget(top_box)
        self.body_layout.addWidget(self._mode_text)
        self.body_layout.addWidget(self._progress)
        self.body_layout.addWidget(self._log, 1)
        self._update_mode_text()

    def training_mode_value(self) -> str:
        index = self._mode_combo.currentIndex()
        return self._modes[index]['value']

    def set_log(self, text: str) -> None:
        self._log.setPlainText(text)

    def append_log(self, text: str) -> None:
        current = self._log.toPlainText()
        self._log.setPlainText(f'{current}\n{text}'.strip())

    def _update_mode_text(self, *_: Any) -> None:
        index = self._mode_combo.currentIndex()
        item = self._modes[index]
        self._mode_text.setText(item.get('description', ''))


class ArtifactsPage(DashboardPage):
    def __init__(
        self,
        title: str,
        subtitle: str,
        on_refresh=None,
        on_train=None,
        on_predict=None,
        on_export=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, subtitle, on_refresh=on_refresh, on_train=on_train, on_predict=on_predict, on_export=on_export, parent=parent)
        self._group_list = QListWidget(self.body)
        self._file_list = QListWidget(self.body)
        self._preview_title = QLabel('选择图表文件后预览。', self.body)
        self._figure = Figure(figsize=(6, 4), dpi=120)
        self._canvas = FigureCanvas(self._figure)

        left_box = QWidget(self.body)
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._group_list, 1)
        left_layout.addWidget(self._file_list, 2)

        right_box = QWidget(self.body)
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self._preview_title)
        right_layout.addWidget(self._canvas, 1)

        split = QWidget(self.body)
        split_layout = QHBoxLayout(split)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addWidget(left_box, 2)
        split_layout.addWidget(right_box, 3)

        self.body_layout.addWidget(split, 1)
        self._group_list.currentItemChanged.connect(self._on_group_changed)
        self._file_list.currentItemChanged.connect(self._on_file_changed)
        self._artifacts: dict[str, list[str]] = {}

    def refresh_snapshot(self, dashboard: dict[str, Any], bundle: dict[str, Any]) -> None:
        super().refresh_snapshot(dashboard, bundle)
        self._artifacts = dashboard.get('artifacts', {})
        self._group_list.clear()
        for group in dashboard.get('artifact_groups', []):
            label = f"{group.get('label', group.get('name', '-'))} ({group.get('file_count', 0)})"
            item = QListWidgetItem(label)
            item.setData(32, group.get('name'))
            self._group_list.addItem(item)
        if self._group_list.count():
            self._group_list.setCurrentRow(0)

    def _on_group_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        self._file_list.clear()
        if current is None:
            return
        group_name = current.data(Qt.ItemDataRole.UserRole)
        for file_path in self._artifacts.get(str(group_name), []):
            self._file_list.addItem(file_path)
        if self._file_list.count():
            self._file_list.setCurrentRow(0)

    def _on_file_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        file_path = Path(current.text())
        self._preview_title.setText(file_path.name)
        self._render_image(file_path)

    def _render_image(self, file_path: Path) -> None:
        self._figure.clear()
        axis = self._figure.add_subplot(111)
        if not file_path.exists():
            axis.text(0.5, 0.5, '文件不存在', ha='center', va='center')
            axis.axis('off')
            self._canvas.draw()
            return
        if file_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            import matplotlib.image as mpimg

            axis.imshow(mpimg.imread(file_path))
            axis.axis('off')
        else:
            axis.text(0.5, 0.5, file_path.read_text(encoding='utf-8', errors='ignore')[:400], ha='center', va='center')
            axis.axis('off')
        self._figure.tight_layout()
        self._canvas.draw()


class DesktopMainWindow(FluentWindow):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.ui = config.get('ui', {})
        self.page_copy = get_page_copy(self.ui)
        self.training_modes = get_training_mode_options(self.ui)
        self.fields = get_form_fields(self.ui)
        self.setWindowTitle(self.ui.get('app', {}).get('title', config.get('project_name', '肥胖风险预测系统')))
        window = self.ui.get('app', {}).get('window', {})
        self.resize(int(window.get('width', 1600)), int(window.get('height', 980)))
        self.setMinimumSize(int(window.get('minimum_width', 1360)), int(window.get('minimum_height', 860)))
        setTheme(Theme.DARK if self.ui.get('app', {}).get('theme', 'dark') == 'dark' else Theme.LIGHT)

        self.state: dict[str, Any] = {'dashboard': {}, 'bundle': {}}
        self._build_pages()
        self.reload_state()

    def _load_runtime_snapshot(self) -> dict[str, Any]:
        return {
            'dashboard': load_dashboard_bundle(self.config),
            'bundle': load_inference_bundle(self.config),
        }

    def _launch_training_process(self, mode: str) -> subprocess.Popen[Any]:
        command = [sys.executable, str(Path(self.config['project_root']) / 'main.py'), mode]
        return subprocess.Popen(command, cwd=self.config['project_root'])

    def _export_dashboard_snapshot(self, dashboard: dict[str, Any]) -> Path:
        export_path = Path(self.config['output_dirs']['reports']) / 'desktop_dashboard_snapshot.json'
        write_json(export_path, dashboard)
        return export_path

    def _build_pages(self) -> None:
        overview = self.page_copy.get('overview', {})
        training = self.page_copy.get('training', {})
        comparison = self.page_copy.get('comparison', {})
        prediction = self.page_copy.get('prediction', {})
        artifacts = self.page_copy.get('artifacts', {})

        self.overview_page = OverviewPage(
            overview.get('title', '总览'),
            overview.get('description', ''),
            on_refresh=self.reload_state,
            on_train=self.launch_training,
            on_predict=self.submit_prediction,
            on_export=self.export_dashboard,
            parent=self,
        )
        self.training_page = TrainingPage(
            training.get('title', '训练'),
            training.get('description', ''),
            self.training_modes,
            on_launch=self.launch_training,
            on_refresh=self.reload_state,
            on_predict=self.submit_prediction,
            on_export=self.export_dashboard,
            parent=self,
        )
        self.comparison_page = ComparisonPage(
            comparison.get('title', '对比'),
            comparison.get('description', ''),
            on_refresh=self.reload_state,
            on_train=self.launch_training,
            on_predict=self.submit_prediction,
            on_export=self.export_dashboard,
            parent=self,
        )
        self.prediction_page = PredictionPage(
            prediction.get('title', '预测'),
            prediction.get('description', ''),
            self.fields,
            on_predict=self.submit_prediction,
            on_refresh=self.reload_state,
            on_train=self.launch_training,
            on_export=self.export_dashboard,
            parent=self,
        )
        self.artifacts_page = ArtifactsPage(
            artifacts.get('title', '产物'),
            artifacts.get('description', ''),
            on_refresh=self.reload_state,
            on_train=self.launch_training,
            on_predict=self.submit_prediction,
            on_export=self.export_dashboard,
            parent=self,
        )

        self.addSubInterface(self.overview_page, FIF.HOME, overview.get('title', '总览'), position=NavigationItemPosition.TOP)
        self.addSubInterface(self.training_page, FIF.PLAY, training.get('title', '训练'), position=NavigationItemPosition.TOP)
        self.addSubInterface(self.comparison_page, FIF.PIE_SINGLE, comparison.get('title', '对比'), position=NavigationItemPosition.TOP)
        self.addSubInterface(self.prediction_page, FIF.SEARCH, prediction.get('title', '预测'), position=NavigationItemPosition.TOP)
        self.addSubInterface(self.artifacts_page, FIF.FOLDER, artifacts.get('title', '产物'), position=NavigationItemPosition.TOP)

    def reload_state(self) -> None:
        self.state = self._load_runtime_snapshot()
        dashboard = self.state['dashboard']
        bundle = self.state['bundle']
        for page in [self.overview_page, self.training_page, self.comparison_page, self.prediction_page, self.artifacts_page]:
            page.refresh_snapshot(dashboard, bundle)
        InfoBar.success('摘要已刷新', dashboard.get('message', '训练摘要已加载。'), parent=self)

    def launch_training(self) -> None:
        mode = self.training_page.training_mode_value()
        if mode == 'artifacts-only':
            InfoBar.warning('训练未启动', '当前选择为仅展示已有产物。', parent=self)
            return
        self._launch_training_process(mode)
        self.training_page.append_log(f'已启动训练：python main.py {mode}')
        InfoBar.success('训练已启动', f'已启动训练任务：{mode}', parent=self)

    def submit_prediction(self) -> None:
        payload = self.prediction_page.payload()
        result = predict_single(payload, self.config, self.state['bundle'])
        self.prediction_page.set_result(json.dumps(result, ensure_ascii=False, indent=2))
        InfoBar.success('预测完成', '单样本预测已执行。', parent=self)

    def export_dashboard(self) -> None:
        path = self._export_dashboard_snapshot(self.state['dashboard'])
        InfoBar.success('已导出快照', str(path), parent=self)


def run_desktop_app() -> None:
    config = load_project_config()
    configure_project_logging(config['project_root'], relative_log_path=config['output_dirs']['logs'] + '/project.log')
    app = QApplication.instance() or QApplication([])
    window = DesktopMainWindow(config)
    window.show()
    app.exec()
