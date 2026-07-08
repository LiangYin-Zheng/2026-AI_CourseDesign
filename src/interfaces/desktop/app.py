from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict

import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.config import load_project_config
from src.interfaces.shared.dashboard_schema import TRAINING_MODE_OPTIONS
from src.interfaces.shared.formatters import normalize_prediction_result
from src.interfaces.shared.sample_schema import FIELD_DEFINITIONS, build_sample_payload
from src.serving.inference import load_dashboard_bundle, load_inference_bundle, predict_single
from src.utils.file_utils import write_json
from src.log import configure_project_logging, get_logger

logger = get_logger('desktop-gui')


# 桌面端训练与预测控制台
class DesktopTrainingConsole:
    # 初始化界面状态
    def __init__(self) -> None:
        self.config = load_project_config()
        configure_project_logging(self.config['project_root'], relative_log_path=self.config['output_dirs']['logs'] + '/project.log')
        self.bundle = load_inference_bundle(self.config)
        self.dashboard = load_dashboard_bundle(self.config)
        self.root = tk.Tk()
        self.root.title('肥胖风险预测系统 · 本地训练管理器')
        self.root.geometry('1480x980')
        self.root.minsize(1280, 860)

        self.training_mode_var = tk.StringVar(value=self.dashboard.get('training_mode', 'train'))
        self.default_model_var = tk.StringVar(value=self.dashboard.get('overview', {}).get('recommended_model', {}).get('name', '-'))
        self.status_var = tk.StringVar(value=self.dashboard.get('message', '训练摘要已加载。'))
        self.result_state_var = tk.StringVar(value='等待执行预测。')
        self.form_vars: Dict[str, tk.StringVar] = {}

        self._chart_canvas: FigureCanvasTkAgg | None = None
        self._chart_figure: Figure | None = None
        self._build_ui()
        self._render_dashboard()

    # 构建主界面
    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        ttk.Label(header, text='肥胖风险预测系统', font=('Arial', 22, 'bold')).pack(anchor=tk.W)
        ttk.Label(header, text='桌面端围绕训练全流程组织：训练选择、过程信息、模型对比、参数、产物、图表和单样本预测。').pack(anchor=tk.W, pady=(3, 10))

        toolbar = ttk.Frame(container)
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ttk.Button(toolbar, text='加载', command=self.reload_state).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text='刷新', command=self.reload_state).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text='训练', command=self.launch_training).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text='预测', command=self.submit_prediction).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text='导出', command=self.export_dashboard).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.overview_tab = ttk.Frame(self.notebook, padding=10)
        self.training_tab = ttk.Frame(self.notebook, padding=10)
        self.comparison_tab = ttk.Frame(self.notebook, padding=10)
        self.prediction_tab = ttk.Frame(self.notebook, padding=10)
        self.artifact_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.overview_tab, text='总览')
        self.notebook.add(self.training_tab, text='训练')
        self.notebook.add(self.comparison_tab, text='对比')
        self.notebook.add(self.prediction_tab, text='预测')
        self.notebook.add(self.artifact_tab, text='产物')

        self._build_overview_tab()
        self._build_training_tab()
        self._build_comparison_tab()
        self._build_prediction_tab()
        self._build_artifact_tab()

    # 构建总览页
    def _build_overview_tab(self) -> None:
        self.overview_metric_frame = ttk.Frame(self.overview_tab)
        self.overview_metric_frame.pack(fill=tk.X, pady=(0, 12))

        upper = ttk.Frame(self.overview_tab)
        upper.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(upper, text='项目总览', padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.overview_text = scrolledtext.ScrolledText(left, wrap=tk.WORD, height=18)
        self.overview_text.pack(fill=tk.BOTH, expand=True)

        right = ttk.LabelFrame(upper, text='训练状态', padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        self.training_status_text = scrolledtext.ScrolledText(right, wrap=tk.WORD, height=18)
        self.training_status_text.pack(fill=tk.BOTH, expand=True)

    # 构建训练页
    def _build_training_tab(self) -> None:
        top = ttk.LabelFrame(self.training_tab, text='训练路线选择', padding=10)
        top.pack(fill=tk.X, pady=(0, 12))
        for option in TRAINING_MODE_OPTIONS:
            row = ttk.Frame(top)
            row.pack(fill=tk.X, pady=3)
            ttk.Radiobutton(row, text=option['label'], value=option['value'], variable=self.training_mode_var).pack(side=tk.LEFT)
            ttk.Label(row, text=option['description']).pack(side=tk.LEFT, padx=12)

        controls = ttk.Frame(self.training_tab)
        controls.pack(fill=tk.BOTH, expand=True)

        command_box = ttk.LabelFrame(controls, text='训练执行说明', padding=10)
        command_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.training_text = scrolledtext.ScrolledText(command_box, wrap=tk.WORD, height=18)
        self.training_text.pack(fill=tk.BOTH, expand=True)

        form_box = ttk.LabelFrame(controls, text='训练过程显示', padding=10)
        form_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        self.training_process_text = scrolledtext.ScrolledText(form_box, wrap=tk.WORD, height=18)
        self.training_process_text.pack(fill=tk.BOTH, expand=True)

    # 构建对比页
    def _build_comparison_tab(self) -> None:
        split = ttk.PanedWindow(self.comparison_tab, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(split, text='模型对比', padding=10)
        right = ttk.LabelFrame(split, text='参数配置摘要', padding=10)
        split.add(left, weight=3)
        split.add(right, weight=2)

        self.comparison_tree = ttk.Treeview(left, columns=('family', 'name', 'accuracy', 'macro_precision', 'macro_recall', 'macro_f1'), show='headings', height=12)
        for column, title, width in [
            ('family', '家族', 120),
            ('name', '模型名称', 160),
            ('accuracy', 'Accuracy', 110),
            ('macro_precision', 'Macro Precision', 130),
            ('macro_recall', 'Macro Recall', 120),
            ('macro_f1', 'Macro F1', 110),
        ]:
            self.comparison_tree.heading(column, text=title)
            self.comparison_tree.column(column, width=width, anchor=tk.W)
        self.comparison_tree.pack(fill=tk.BOTH, expand=True)

        self.parameter_tree = ttk.Treeview(right, columns=('family', 'name', 'parameters'), show='headings', height=12)
        for column, title, width in [('family', '家族', 100), ('name', '模型名称', 150), ('parameters', '参数', 360)]:
            self.parameter_tree.heading(column, text=title)
            self.parameter_tree.column(column, width=width, anchor=tk.W)
        self.parameter_tree.pack(fill=tk.BOTH, expand=True)

    # 构建预测页
    def _build_prediction_tab(self) -> None:
        split = ttk.PanedWindow(self.prediction_tab, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True)

        form_frame = ttk.LabelFrame(split, text='单样本输入', padding=10)
        result_frame = ttk.LabelFrame(split, text='预测结果', padding=10)
        split.add(form_frame, weight=3)
        split.add(result_frame, weight=2)

        form_canvas = tk.Canvas(form_frame, highlightthickness=0)
        form_scroll = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=form_canvas.yview)
        self.form_inner = ttk.Frame(form_canvas)
        self.form_inner.bind(
            '<Configure>',
            lambda _event: form_canvas.configure(scrollregion=form_canvas.bbox('all')),
        )
        form_canvas.create_window((0, 0), window=self.form_inner, anchor='nw')
        form_canvas.configure(yscrollcommand=form_scroll.set)
        form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        form_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for index, (field_name, label_text, default_value, options) in enumerate(FIELD_DEFINITIONS):
            row = index // 2
            column = index % 2
            cell = ttk.Frame(self.form_inner)
            cell.grid(row=row, column=column, sticky='ew', padx=8, pady=8)
            ttk.Label(cell, text=label_text).pack(anchor=tk.W)
            variable = tk.StringVar(value=str(default_value))
            self.form_vars[field_name] = variable
            if options:
                widget = ttk.Combobox(cell, textvariable=variable, values=options, state='readonly')
            else:
                widget = ttk.Entry(cell, textvariable=variable)
            widget.pack(fill=tk.X)

        self.form_inner.columnconfigure(0, weight=1)
        self.form_inner.columnconfigure(1, weight=1)

        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=24)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, '等待提交预测...')
        self.result_text.configure(state=tk.DISABLED)

    # 构建产物页
    def _build_artifact_tab(self) -> None:
        split = ttk.PanedWindow(self.artifact_tab, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(split, text='产物状态', padding=10)
        right = ttk.LabelFrame(split, text='图表预览', padding=10)
        split.add(left, weight=2)
        split.add(right, weight=3)

        self.artifact_tree = ttk.Treeview(left, columns=('group', 'count', 'exists', 'sample'), show='headings', height=14)
        for column, title, width in [('group', '分组', 120), ('count', '数量', 70), ('exists', '存在', 70), ('sample', '样例', 260)]:
            self.artifact_tree.heading(column, text=title)
            self.artifact_tree.column(column, width=width, anchor=tk.W)
        self.artifact_tree.pack(fill=tk.BOTH, expand=True)
        self.artifact_tree.bind('<<TreeviewSelect>>', self._on_artifact_select)

        self.chart_list = tk.Listbox(right, height=10)
        self.chart_list.pack(fill=tk.X, pady=(0, 8))
        self.chart_list.bind('<<ListboxSelect>>', self._on_chart_select)

        self.chart_holder = ttk.Frame(right)
        self.chart_holder.pack(fill=tk.BOTH, expand=True)

        self.chart_hint = ttk.Label(self.chart_holder, text='选择图表文件后显示预览。')
        self.chart_hint.pack(anchor=tk.W)

    # 刷新当前 dashboard
    def _render_dashboard(self) -> None:
        overview = self.dashboard.get('overview', {})
        self.status_var.set(self.dashboard.get('message', '训练摘要已加载。'))
        self.default_model_var.set(overview.get('recommended_model', {}).get('name', '-'))
        self.training_mode_var.set(self.dashboard.get('training_mode', 'train'))

        self._render_overview_metrics(overview)
        self._render_overview_text()
        self._render_training_text()
        self._render_comparison()
        self._render_parameters()
        self._render_artifacts()
        self._render_chart_options()

    # 渲染概览卡片
    def _render_overview_metrics(self, overview: Dict[str, Any]) -> None:
        for child in self.overview_metric_frame.winfo_children():
            child.destroy()

        cards = [
            ('项目名称', overview.get('project_name', '-')),
            ('样本量', overview.get('sample_count', '-')),
            ('类别数', overview.get('class_count', '-')),
            ('推荐模型', overview.get('recommended_model', {}).get('label', '-')),
            ('最优 Macro F1', overview.get('best_macro_f1', '-')),
            ('训练状态', overview.get('training_status', '-')),
        ]

        for index, (label, value) in enumerate(cards):
            card = ttk.Frame(self.overview_metric_frame, padding=10, relief=tk.GROOVE)
            card.grid(row=0, column=index, sticky='nsew', padx=6)
            ttk.Label(card, text=label).pack(anchor=tk.W)
            ttk.Label(card, text=str(value), font=('Arial', 16, 'bold')).pack(anchor=tk.W, pady=(6, 0))
            self.overview_metric_frame.columnconfigure(index, weight=1)

    # 渲染总览文本
    def _render_overview_text(self) -> None:
        overview = self.dashboard.get('overview', {})
        dataset = self.dashboard.get('dataset', {})
        artifact_status = self.dashboard.get('artifact_status', {})
        lines = [
            f"项目名称：{overview.get('project_name', '-')}",
            f"训练路线：{overview.get('training_mode_label', '-')}",
            f"推荐模型：{overview.get('recommended_model', {}).get('family', '-')}/{overview.get('recommended_model', {}).get('name', '-')}",
            f"最优 Macro F1：{overview.get('best_macro_f1', '-')}",
            f"数据切分：{dataset.get('split', {})}",
            '',
            '产物状态：',
            f"- 模型文件：{'存在' if artifact_status.get('models') else '缺失'}",
            f"- 图表文件：{'存在' if artifact_status.get('figures') else '缺失'}",
            f"- 报告文件：{'存在' if artifact_status.get('reports') else '缺失'}",
            f"- 日志路径：{artifact_status.get('log_path', '-')}",
        ]
        self._replace_text(self.overview_text, '\n'.join(lines))

    # 渲染训练说明与状态
    def _render_training_text(self) -> None:
        mode = self.training_mode_var.get()
        mode_label = next((item['label'] for item in TRAINING_MODE_OPTIONS if item['value'] == mode), mode)
        lines = [
            f"当前训练路线：{mode_label}",
            '',
            '可执行命令：',
            f"python main.py {mode}",
            '',
            '说明：',
            '- “训练”按钮会启动本地训练进程，不阻塞当前窗口。',
            '- “刷新”按钮会重新读取 dashboard 和模型文件。',
            '- “仅展示已有产物”不会启动训练，只用于加载现有结果。',
        ]
        self._replace_text(self.training_text, '\n'.join(lines))
        training_status_lines = [
            f"当前摘要状态：{self.dashboard.get('status', '-')}",
            f"生成时间：{self.dashboard.get('generated_at', '-')}",
            f"训练状态：{self.dashboard.get('overview', {}).get('training_status', '-')}",
            '',
            '参数摘要：',
        ]
        for row in self.dashboard.get('parameter_rows', [])[:6]:
            training_status_lines.append(f"- {row['family']}/{row['name']}: {json.dumps(row['parameters'], ensure_ascii=False)}")
        if len(training_status_lines) == 5:
            training_status_lines.append('- 暂无参数摘要，请先执行训练。')
        self._replace_text(self.training_process_text, '\n'.join(training_status_lines), readonly=False)

    # 渲染模型对比表
    def _render_comparison(self) -> None:
        self._clear_tree(self.comparison_tree)
        rows = self.dashboard.get('comparison_rows', [])
        if not rows:
            self.comparison_tree.insert('', tk.END, values=('-', '-', '-', '-', '-', '-'))
            return
        for row in rows:
            metrics = row.get('metrics', {})
            self.comparison_tree.insert('', tk.END, values=(
                row.get('family', '-'),
                row.get('name', '-'),
                metrics.get('accuracy', '-'),
                metrics.get('macro_precision', '-'),
                metrics.get('macro_recall', '-'),
                metrics.get('macro_f1', '-'),
            ))

    # 渲染参数表
    def _render_parameters(self) -> None:
        self._clear_tree(self.parameter_tree)
        rows = self.dashboard.get('parameter_rows', [])
        if not rows:
            self.parameter_tree.insert('', tk.END, values=('-', '-', '暂无参数摘要'))
            return
        for row in rows:
            self.parameter_tree.insert('', tk.END, values=(
                row.get('family', '-'),
                row.get('name', '-'),
                json.dumps(row.get('parameters', {}), ensure_ascii=False),
            ))

    # 渲染产物列表
    def _render_artifacts(self) -> None:
        self._clear_tree(self.artifact_tree)
        for group in self.dashboard.get('artifact_groups', []):
            files = group.get('files', [])
            preview = files[0] if files else '-'
            self.artifact_tree.insert('', tk.END, values=(
                group.get('label', group.get('name', '-')),
                group.get('file_count', 0),
                '是' if group.get('exists') else '否',
                preview,
            ))

    # 渲染图表选项
    def _render_chart_options(self) -> None:
        self.chart_list.delete(0, tk.END)
        chart_paths = []
        for group in self.dashboard.get('chart_groups', []):
            for file_path in group.get('files', []):
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    chart_paths.append(file_path)
        self._chart_paths = chart_paths
        for path in chart_paths:
            self.chart_list.insert(tk.END, path)
        if chart_paths:
            self.chart_list.selection_set(0)
            self._render_chart_preview(chart_paths[0])
        else:
            self._render_chart_preview(None)

    # 渲染图表预览
    def _render_chart_preview(self, relative_path: str | None) -> None:
        for child in self.chart_holder.winfo_children():
            if child is not self.chart_hint:
                child.destroy()
        if not relative_path:
            self.chart_hint.configure(text='暂无可预览图表。')
            return

        file_path = Path(self.config['project_root']) / relative_path
        if not file_path.exists():
            self.chart_hint.configure(text=f'图表文件不存在：{relative_path}')
            return

        self.chart_hint.configure(text=relative_path)
        try:
            figure = Figure(figsize=(6.5, 4.2), dpi=120)
            axis = figure.add_subplot(111)
            axis.imshow(mpimg.imread(file_path))
            axis.axis('off')
            figure.tight_layout()
            canvas = FigureCanvasTkAgg(figure, master=self.chart_holder)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(8, 0))
            self._chart_canvas = canvas
            self._chart_figure = figure
        except Exception as error:  # noqa: BLE001
            self.chart_hint.configure(text=f'无法预览图表：{error}')

    # 响应图表选择
    def _on_chart_select(self, _event: tk.Event[Any]) -> None:
        selection = self.chart_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        if index < len(self._chart_paths):
            self._render_chart_preview(self._chart_paths[index])

    # 响应产物选择
    def _on_artifact_select(self, _event: tk.Event[Any]) -> None:
        return

    # 重新加载状态
    def reload_state(self) -> None:
        self.bundle = load_inference_bundle(self.config)
        self.dashboard = load_dashboard_bundle(self.config)
        self.status_var.set(self.dashboard.get('message', '训练摘要已加载。'))
        self._render_dashboard()
        logger.info('桌面界面已刷新 dashboard。')

    # 启动训练进程
    def launch_training(self) -> None:
        mode = self.training_mode_var.get()
        if mode == 'artifacts-only':
            self.status_var.set('当前选择为“仅展示已有产物”，未启动训练。')
            self.reload_state()
            return
        command = [sys.executable, str(Path(self.config['project_root']) / 'main.py'), mode]
        try:
            subprocess.Popen(command, cwd=self.config['project_root'])
            self.status_var.set(f'已启动训练：python main.py {mode}')
            self.training_process_text.insert(tk.END, f"\n\n已启动训练进程：{' '.join(command)}\n")
        except Exception as error:  # noqa: BLE001
            logger.exception('启动训练失败。')
            messagebox.showerror('训练启动失败', str(error))

    # 提交单样本预测
    def submit_prediction(self) -> None:
        try:
            payload = build_sample_payload({field_name: variable.get() for field_name, variable in self.form_vars.items()})
            result = predict_single(payload, self.config, self.bundle)
            self._replace_text(self.result_text, json.dumps(normalize_prediction_result(result), ensure_ascii=False, indent=2))
            self.result_state_var.set('预测完成。')
            logger.info('本地桌面界面完成一次预测请求。')
        except Exception as error:  # noqa: BLE001
            logger.exception('本地桌面界面预测失败。')
            messagebox.showerror('预测失败', str(error))

    # 导出当前 dashboard
    def export_dashboard(self) -> None:
        export_path = Path(self.config['output_dirs']['reports']) / 'desktop_dashboard_snapshot.json'
        write_json(export_path, self.dashboard)
        self.status_var.set(f'已导出：{export_path}')
        messagebox.showinfo('导出完成', str(export_path))

    # 替换多行文本框内容
    def _replace_text(self, widget: scrolledtext.ScrolledText, content: str, readonly: bool = True) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, content)
        widget.configure(state=tk.DISABLED if readonly else tk.NORMAL)

    # 清空表格内容
    def _clear_tree(self, tree: ttk.Treeview) -> None:
        for child in tree.get_children():
            tree.delete(child)

    # 运行桌面程序
    def run(self) -> None:
        self.root.mainloop()


# 启动本地 GUI
def run_local_gui() -> None:
    DesktopTrainingConsole().run()
