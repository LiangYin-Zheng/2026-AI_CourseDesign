from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict

from src.config import load_project_config
from src.serving.inference import load_dashboard_bundle, load_inference_bundle, predict_single
from src.utils.logger import configure_project_logging, get_logger

logger = get_logger('desktop-gui')

FIELD_DEFINITIONS = [
    ('gender', '性别', 'Female', ['Female', 'Male']),
    ('age', '年龄', 24.0, None),
    ('height_m', '身高（米）', 1.70, None),
    ('weight_kg', '体重（千克）', 72.0, None),
    ('family_history_with_overweight', '家族肥胖史', 1, ['1', '0']),
    ('high_calorie_food_frequency', '高热量饮食偏好', 1, ['1', '0']),
    ('vegetable_intake_score', '蔬菜摄入评分', 2.5, None),
    ('main_meals_per_day', '每日正餐次数', 3.0, None),
    ('snacking_frequency', '加餐频率', 'Sometimes', ['Never', 'Sometimes', 'Frequently', 'Always']),
    ('smokes', '是否吸烟', 0, ['0', '1']),
    ('water_intake_liters', '饮水量（升）', 2.0, None),
    ('calorie_monitoring', '是否热量监测', 0, ['0', '1']),
    ('physical_activity_score', '运动评分', 1.5, None),
    ('technology_use_hours', '电子设备使用时长评分', 1.0, None),
    ('alcohol_consumption', '饮酒频率', 'Sometimes', ['Never', 'Sometimes', 'Frequently', 'Always']),
    ('transportation_mode', '出行方式', 'Automobile', ['Public_Transportation', 'Automobile', 'Walking', 'Motorbike', 'Bike']),
]


def _coerce_value(field_name: str, raw_value: str) -> Any:
    integer_fields = {'family_history_with_overweight', 'high_calorie_food_frequency', 'smokes', 'calorie_monitoring'}
    float_fields = {'age', 'height_m', 'weight_kg', 'vegetable_intake_score', 'main_meals_per_day', 'water_intake_liters', 'physical_activity_score', 'technology_use_hours'}
    if field_name in integer_fields:
        return int(float(raw_value))
    if field_name in float_fields:
        return float(raw_value)
    return raw_value


def _build_dashboard_text(dashboard: Dict[str, Any]) -> str:
    dataset = dashboard.get('dataset', {})
    recommended = dashboard.get('recommended_model', {})
    parameter_lines = []
    for row in dashboard.get('parameter_tables', [])[:4]:
        parameter_lines.append(f"- {row['family']}/{row['name']}: {row['parameters']}")
    lines = [
        f"项目：{dashboard.get('project_name', '未知项目')}",
        dashboard.get('message', '训练摘要已加载。'),
        f"样本量：{dataset.get('sample_count', '-')}",
        f"类别数：{dataset.get('class_count', '-')}",
        f"推荐模型：{recommended.get('family', '-')}/{recommended.get('name', '-')}",
        '',
        '优化后参数（前 4 项）：',
    ]
    lines.extend(parameter_lines if parameter_lines else ['- 暂无参数摘要，请先执行训练命令。'])
    return '\n'.join(lines)


def run_local_gui() -> None:
    config = load_project_config()
    configure_project_logging(config['project_root'], relative_log_path=config['output_dirs']['logs'] + '/project.log')
    bundle = load_inference_bundle(config)
    dashboard = load_dashboard_bundle(config)

    root = tk.Tk()
    root.title('肥胖风险预测系统 · 本地桌面界面')
    root.geometry('1180x820')

    container = ttk.Frame(root, padding=18)
    container.pack(fill=tk.BOTH, expand=True)

    title = ttk.Label(container, text='肥胖风险预测系统（本地桌面版）', font=('Arial', 20, 'bold'))
    title.pack(anchor=tk.W)
    subtitle = ttk.Label(container, text='该模式不依赖 HTTP 服务，直接在本地窗口中加载训练摘要并执行模型预测。')
    subtitle.pack(anchor=tk.W, pady=(4, 14))

    top = ttk.Frame(container)
    top.pack(fill=tk.BOTH, expand=False)

    summary_frame = ttk.LabelFrame(top, text='训练摘要', padding=12)
    summary_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
    summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=12)
    summary_text.pack(fill=tk.BOTH, expand=True)
    summary_text.insert(tk.END, _build_dashboard_text(dashboard))
    summary_text.configure(state=tk.DISABLED)

    result_frame = ttk.LabelFrame(top, text='预测结果', padding=12)
    result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
    result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=12)
    result_text.pack(fill=tk.BOTH, expand=True)
    result_text.insert(tk.END, '等待提交预测...')

    form_frame = ttk.LabelFrame(container, text='样本输入', padding=12)
    form_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

    variables: Dict[str, tk.StringVar] = {}
    for index, (field_name, label_text, default_value, options) in enumerate(FIELD_DEFINITIONS):
        row = index // 2
        column = index % 2
        field_container = ttk.Frame(form_frame)
        field_container.grid(row=row, column=column, sticky='ew', padx=8, pady=8)
        ttk.Label(field_container, text=label_text).pack(anchor=tk.W)
        variable = tk.StringVar(value=str(default_value))
        variables[field_name] = variable
        if options:
            widget = ttk.Combobox(field_container, textvariable=variable, values=options, state='readonly')
        else:
            widget = ttk.Entry(field_container, textvariable=variable)
        widget.pack(fill=tk.X)

    form_frame.columnconfigure(0, weight=1)
    form_frame.columnconfigure(1, weight=1)

    def submit_prediction() -> None:
        try:
            payload = {field_name: _coerce_value(field_name, variable.get()) for field_name, variable in variables.items()}
            result = predict_single(payload, config, bundle)
            result_text.configure(state=tk.NORMAL)
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, json.dumps(result, ensure_ascii=False, indent=2))
            result_text.configure(state=tk.DISABLED)
            logger.info('本地桌面界面完成一次预测请求。')
        except Exception as error:  # noqa: BLE001
            messagebox.showerror('预测失败', str(error))

    action_frame = ttk.Frame(container)
    action_frame.pack(fill=tk.X, pady=(12, 0))
    ttk.Button(action_frame, text='提交预测', command=submit_prediction).pack(side=tk.LEFT)
    ttk.Label(action_frame, text='建议先执行 train / train-sklearn / train-manual 生成模型文件后再使用。').pack(side=tk.LEFT, padx=12)

    root.mainloop()
