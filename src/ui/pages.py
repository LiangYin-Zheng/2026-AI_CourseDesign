import json
from datetime import datetime
from time import perf_counter, sleep

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from application.workflows import load_workflow_context
from data.loader import load_csv_readonly
from ui.components import (
    disclaimer,
    empty_state,
    metric_card,
    parameter_summary_frame,
    page_header,
    section_header,
    show_error,
)
from ui.constants import (
    CATEGORY_LABELS,
    CLASS_LABELS,
    FIELD_INFO,
    MODEL_INFO,
    TARGET_DISPLAY_LABELS,
)
from ui.services import (
    activate_model,
    classification_report_frame,
    load_dashboard_data,
    load_example_sample,
    load_input_metadata,
    load_model_metrics,
    predict_sample,
    project_relative_path,
    read_json,
    train_selected_model,
)


# 将数值格式化为适合指标卡展示的百分比。
def _percent(value: float) -> str:
    return f"{float(value) * 100:.2f}%"


# 将 Unix 时间转换为简洁的本地更新时间。
def _format_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


# 通过会话状态切换侧边导航页面。
def _navigate(page_name: str) -> None:
    st.session_state["navigation"] = page_name


# 绘制统一主色的模型指标对比图。
def _comparison_chart(
    results: list[dict], metric: str, label: str, selected_model: str
) -> None:
    rows = []
    for result in results:
        value = (
            float(result["training_time_seconds"])
            if metric == "training_time_seconds"
            else float(result["test_metrics"][metric])
        )
        rows.append(
            {
                "model_name": result["model_name"],
                "display_name": result["display_name"],
                "value": value,
            }
        )
    rows.sort(key=lambda item: item["value"])
    is_time = metric == "training_time_seconds"
    text = [
        f"{row['value']:.3f} 秒" if is_time else f"{row['value'] * 100:.2f}%"
        for row in rows
    ]
    colors = [
        "#2563EB" if row["model_name"] == selected_model else "#B8CAE6"
        for row in rows
    ]
    figure = go.Figure(
        go.Bar(
            x=[row["value"] for row in rows],
            y=[row["display_name"] for row in rows],
            orientation="h",
            marker={"color": colors, "line": {"width": 0}},
            text=text,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>%{text}<extra></extra>",
        )
    )
    upper = max(row["value"] for row in rows) * 1.16
    figure.update_layout(
        height=292,
        margin={"l": 8, "r": 70, "t": 12, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif", "color": "#64748B", "size": 12},
        showlegend=False,
        xaxis={"range": [0, upper], "showgrid": True, "gridcolor": "#EEF2F7", "zeroline": False, "showticklabels": False, "title": None},
        yaxis={"showgrid": False, "automargin": True, "tickfont": {"color": "#334155", "size": 12}},
        bargap=0.38,
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


# 展示系统概览首页。
def render_overview() -> None:
    page_header("系统概览", "集中查看数据规模、活动模型、核心表现与常用操作。")
    try:
        dashboard = load_dashboard_data()
    except (FileNotFoundError, OSError, ValueError) as error:
        show_error(error, "系统概览加载")
        return
    active_name = dashboard["active_model"]
    active_info = MODEL_INFO[active_name]
    active_metrics = dashboard["active_metrics"]
    test_metrics = active_metrics["test_metrics"]
    validation_metrics = active_metrics["validation_metrics"]

    with st.container(border=True, key="overview_banner"):
        banner_left, banner_right = st.columns([1.55, 0.45], gap="large")
        with banner_left:
            st.markdown(
                '<span class="status-pill"><span class="status-dot"></span>系统运行正常</span>'
                '<h2 style="font-size:1.55rem;margin:.8rem 0 .45rem">肥胖风险预测系统</h2>'
                '<p style="color:#64748B;font-size:.86rem;line-height:1.65;margin:0">'
                '基于真实课程数据完成七分类预测、四模型对比、探索性分析与可控模型训练。'
                '结果面向算法课程演示，不用于医学判断。</p>',
                unsafe_allow_html=True,
            )
        with banner_right:
            st.markdown(
                f'<div class="metric-label">当前活动模型</div>'
                f'<div class="banner-model">{active_info["name"]}</div>'
                f'<span class="badge">{active_info["implementation"]}</span>'
                f'<div class="banner-time" style="margin-top:.65rem">更新于 {_format_time(dashboard["model_updated_at"])}</div>',
                unsafe_allow_html=True,
            )
            st.button(
                "开始预测",
                type="primary",
                width="stretch",
                key="overview_predict",
                on_click=_navigate,
                args=("肥胖风险预测",),
            )

    section_header("数据与模型概览", "核心规模和当前活动模型。")
    columns = st.columns(4)
    cards = (
        ("数据样本", f"{dashboard['sample_count']:,}", "真实 CSV 记录数"),
        ("输入特征", str(dashboard["feature_count"]), "排除标识与目标字段"),
        ("肥胖等级", str(dashboard["class_count"]), "当前目标类别数"),
        ("当前活动模型", active_info["name"], active_info["implementation"]),
    )
    for index, (column, card) in enumerate(zip(columns, cards)):
        with column:
            metric_card(*card, model_value=index == 3)

    score_columns = st.columns(3)
    scores = (
        ("验证集 Macro F1", _percent(validation_metrics["macro_f1"]), "活动模型选择依据"),
        ("测试集 Accuracy", _percent(test_metrics["accuracy"]), "仅用于最终评价"),
        ("测试集 Macro F1", _percent(test_metrics["macro_f1"]), "七类别等权平均"),
    )
    for column, score in zip(score_columns, scores):
        with column:
            metric_card(*score)

    section_header("当前模型摘要与排名", "摘要不重复核心指标；右侧按测试集 Macro F1 展示排名。")
    left, right = st.columns([0.8, 1.2], gap="large")
    with left:
        st.markdown(
            '<div class="card">'
            f'<div class="metric-label">模型信息</div><h3 style="margin:.45rem 0 .3rem">{active_info["name"]}</h3>'
            f'<span class="badge">{active_info["implementation"]}</span>'
            f'<div style="color:#64748B;font-size:.78rem;line-height:1.8;margin-top:.8rem">'
            f'模型类型：{active_info["kind"]}<br>'
            f'更新时间：{_format_time(dashboard["model_updated_at"])}<br>'
            f'参数数量：{len(active_metrics["parameters"])} 项</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        with st.container(border=True, key="overview_rank_chart"):
            _comparison_chart(dashboard["comparison"], "macro_f1", "Macro F1", active_name)

    section_header("快捷入口", "从常用任务直接进入对应页面。")
    quick_columns = st.columns(4)
    quick_actions = (
        ("开始预测", "填写一条样本并查看七类概率", "肥胖风险预测"),
        ("模型对比", "查看完整指标和分类报告", "模型性能分析"),
        ("数据分析", "浏览六张真实 EDA 图表", "数据探索分析"),
        ("训练模型", "配置参数并保留新实验", "模型训练中心"),
    )
    for column, (title, detail, target) in zip(quick_columns, quick_actions):
        with column:
            st.markdown(f'<div class="card"><strong>{title}</strong><div class="metric-help" style="margin-top:.4rem">{detail}</div></div>', unsafe_allow_html=True)
            st.button(f"进入{title}", key=f"quick_{target}", width="stretch", on_click=_navigate, args=(target,))


# 将真实示例写入全部预测控件会话状态。
def _set_prediction_sample(sample: dict) -> None:
    for field, value in sample.items():
        st.session_state[f"input_{field}"] = value
    st.session_state.pop("prediction_result", None)


# 重置预测表单为真实 CSV 首行对应的稳定默认值。
def _reset_prediction_inputs() -> None:
    _set_prediction_sample(load_example_sample(0))


# 确保预测控件在第一次打开时具有完整默认值。
def _initialize_prediction_inputs() -> None:
    if "input_Age" not in st.session_state:
        _reset_prediction_inputs()


# 渲染一个带真实范围或真实类别选项的输入控件。
def _render_input(field: str, metadata: dict) -> object:
    info = FIELD_INFO[field]
    label = info["label"]
    help_text = info.get("help", info.get("unit", "来自活动模型输入元数据"))
    help_text = f"原始字段：{field}；{help_text}"
    if field in metadata["numeric_columns"]:
        bounds = metadata["numeric_ranges"][field]
        common_options = {
            "label": label,
            "min_value": float(bounds["minimum"]),
            "max_value": float(bounds["maximum"]),
            "step": float(info.get("step", 0.1)),
            "key": f"input_{field}",
            "help": f"{help_text}；活动模型允许范围 {bounds['minimum']}–{bounds['maximum']}",
        }
        if field in {"FCVC", "NCP", "CH2O", "FAF", "TUE"}:
            return st.slider(**common_options)
        return st.number_input(
            **common_options,
        )
    options = metadata["categorical_options"][field]
    if len(options) == 2:
        compact_labels = {
            "Female": "女性",
            "Male": "男性",
            0: "否",
            1: "是",
        }
        return st.segmented_control(
            label,
            options=options,
            key=f"input_{field}",
            format_func=lambda value: compact_labels.get(value, str(value)),
            help=help_text,
            width="stretch",
        )
    return st.selectbox(
        label,
        options=options,
        key=f"input_{field}",
        format_func=lambda value: CATEGORY_LABELS.get(value, str(value)),
        help=help_text,
    )


# 从预测控件收集与活动模型字段顺序一致的单条样本。
def _collect_prediction_sample(metadata: dict) -> dict:
    return {
        field: st.session_state[f"input_{field}"]
        for field in metadata["input_columns"]
    }


# 绘制中文标签完整且带末端数值的七类别概率图。
def _probability_chart(probability_rows: list[dict]) -> None:
    rows = list(reversed(probability_rows))
    figure = go.Figure(
        go.Bar(
            x=[row["预测概率"] for row in rows],
            y=[row["类别"] for row in rows],
            orientation="h",
            marker={"color": ["#2563EB" if index == len(rows) - 1 else "#B8CAE6" for index in range(len(rows))]},
            text=[_percent(row["预测概率"]) for row in rows],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>%{text}<extra></extra>",
        )
    )
    figure.update_layout(
        height=350,
        margin={"l": 8, "r": 68, "t": 10, "b": 18},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif", "color": "#64748B", "size": 11},
        xaxis={"range": [0, max(row["预测概率"] for row in rows) * 1.2], "showticklabels": False, "showgrid": True, "gridcolor": "#EEF2F7", "zeroline": False},
        yaxis={"showgrid": False, "automargin": True},
        showlegend=False,
        bargap=0.38,
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


# 展示预测结果、模型信息与排序后的七类概率。
def _render_prediction_result(result: dict) -> None:
    predicted = result["predicted_class"]
    st.markdown(
        '<div class="result-card"><div class="result-label">预测结果</div>'
        f'<div class="result-class">{CLASS_LABELS[predicted]}</div>'
        f'<div class="result-original">英文标签：{TARGET_DISPLAY_LABELS[predicted]}</div>'
        f'<div class="result-confidence">{_percent(result["highest_probability"])}</div>'
        '<div class="metric-help">最高预测概率</div></div>',
        unsafe_allow_html=True,
    )
    details = st.columns(3)
    with details[0]:
        metric_card("当前模型", MODEL_INFO[result["model_name"]]["kind"], result["model_name"])
    with details[1]:
        metric_card("实现方式", result["implementation"], "已加载活动模型")
    with details[2]:
        metric_card("预测时间", f"{result['elapsed_ms']:.2f} ms", "单条模型推理")
    section_header("七类别概率", "按预测概率从高到低排列，最高类别使用同一主色突出。")
    probability_rows = [
        {
            "类别": CLASS_LABELS[label],
            "英文标签": TARGET_DISPLAY_LABELS[label],
            "预测概率": float(probability),
        }
        for label, probability in sorted(
            result["probabilities"].items(), key=lambda item: item[1], reverse=True
        )
    ]
    _probability_chart(probability_rows)
    display_rows = pd.DataFrame(probability_rows)
    display_rows["预测概率"] = display_rows["预测概率"].map(_percent)
    st.dataframe(display_rows, hide_index=True, width="stretch")
    disclaimer()


# 展示分组输入与结果双栏预测页面。
def render_prediction() -> None:
    page_header("肥胖风险预测", "填写一条完整样本，使用当前活动模型生成七个课程类别的概率。")
    try:
        metadata = load_input_metadata()
        _initialize_prediction_inputs()
    except (FileNotFoundError, OSError, ValueError) as error:
        show_error(error, "预测页面初始化")
        return
    input_column, result_column = st.columns([1.08, 0.92], gap="large")
    with input_column:
        section_header("输入样本", "使用中文选项填写身体、饮食和生活习惯；帮助提示中可查看原始字段与范围。")
        action_columns = st.columns([0.72, 0.28])
        with action_columns[0]:
            if st.button("加载示例", width="content", key="load_prediction_example"):
                _set_prediction_sample(load_example_sample(1))
                st.rerun()
        with action_columns[1]:
            if st.button("重置输入", type="tertiary", width="content", key="reset_prediction"):
                _reset_prediction_inputs()
                st.rerun()
        with st.form("prediction_form", border=False):
            for group in ("基本身体信息", "饮食习惯", "生活习惯"):
                with st.expander(group, expanded=True):
                    fields = [field for field in metadata["input_columns"] if FIELD_INFO[field]["group"] == group]
                    field_columns = st.columns(2)
                    for index, field in enumerate(fields):
                        with field_columns[index % 2]:
                            _render_input(field, metadata)
            submitted = st.form_submit_button("开始预测", type="primary", width="stretch")
        if submitted:
            try:
                with st.spinner("正在校验输入并调用活动模型……"):
                    st.session_state["prediction_result"] = predict_sample(
                        _collect_prediction_sample(metadata)
                    )
                st.success("预测已完成。")
            except (FileNotFoundError, OSError, ValueError, RuntimeError) as error:
                show_error(error, "预测")
    with result_column:
        section_header("预测结果", "查看最高类别、模型信息和完整概率分布。")
        result = st.session_state.get("prediction_result")
        if result is None:
            empty_state(
                "等待预测",
                "填写左侧信息并点击“开始预测”。",
                (
                    "使用当前活动模型，不触发重新训练",
                    "返回七个课程类别的完整概率",
                    "输入仅用于本次页面预测",
                ),
            )
            disclaimer()
        else:
            _render_prediction_result(result)


# 将分类报告类别名称转换为中英文并列形式。
def _localized_report(metrics: dict) -> pd.DataFrame:
    frame = classification_report_frame(metrics)
    summary_labels = {"macro avg": "宏平均", "weighted avg": "加权平均"}
    frame["类别"] = frame["类别"].map(
        lambda value: f"{CLASS_LABELS[value]} · {TARGET_DISPLAY_LABELS[value]}"
        if value in CLASS_LABELS
        else summary_labels.get(value, value)
    )
    frame = frame.rename(
        columns={"precision": "Precision", "recall": "Recall", "f1-score": "F1", "support": "样本数"}
    )
    return frame


# 展示四模型指标、图表和详细评估产物。
def render_performance() -> None:
    page_header("模型性能分析", "统一查看四种模型的测试指标、混淆矩阵、分类报告与参数。")
    model_name = st.selectbox(
        "选择分析模型",
        options=list(MODEL_INFO),
        format_func=lambda value: MODEL_INFO[value]["name"],
    )
    try:
        metrics = load_model_metrics(model_name)
        all_metrics = [load_model_metrics(name) for name in MODEL_INFO]
        _, paths = load_workflow_context()
    except (FileNotFoundError, OSError, ValueError) as error:
        show_error(error, "模型指标加载")
        return
    test = metrics["test_metrics"]
    section_header("核心指标", "以下为固定测试集最终评价结果，训练时间为当前保存实验的实测值。")
    cards = st.columns(6)
    values = (
        ("准确率", _percent(test["accuracy"]), "Accuracy"),
        ("宏平均精确率", _percent(test["macro_precision"]), "Macro Precision"),
        ("宏平均召回率", _percent(test["macro_recall"]), "Macro Recall"),
        ("宏平均 F1", _percent(test["macro_f1"]), "Macro F1"),
        ("加权 F1", _percent(test["weighted_f1"]), "Weighted F1"),
        ("训练时间", f"{metrics['training_time_seconds']:.3f} 秒", "保存实验实测"),
    )
    for column, value in zip(cards, values):
        with column:
            metric_card(*value)

    section_header("模型对比", "切换指标以避免多个图表同时堆叠。")
    metric_label = st.segmented_control(
        "对比指标",
        options=["Accuracy", "Macro F1", "Weighted F1", "训练时间"],
        default="Macro F1",
        label_visibility="collapsed",
    )
    metric_map = {
        "Accuracy": ("accuracy", "Accuracy"),
        "Macro F1": ("macro_f1", "Macro F1"),
        "Weighted F1": ("weighted_f1", "Weighted F1"),
    }
    with st.container(border=True, key="performance_chart"):
        if metric_label == "训练时间":
            _comparison_chart(
                all_metrics,
                "training_time_seconds",
                "训练时间（秒）",
                model_name,
            )
        else:
            metric_key, chart_label = metric_map[metric_label or "Macro F1"]
            _comparison_chart(all_metrics, metric_key, chart_label, model_name)

    section_header("详细结果", "通过选项卡切换内容，避免连续图像和大段原始文本。")
    confusion_tab, report_tab, curve_tab, parameters_tab = st.tabs(
        ["混淆矩阵", "分类报告", "训练曲线", "参数信息"]
    )
    with confusion_tab:
        image_path = paths["metrics_dir"] / f"{model_name}_confusion_matrix.png"
        if image_path.is_file():
            st.image(str(image_path), caption=f"{metrics['display_name']} · 测试集混淆矩阵", width="stretch")
        else:
            empty_state("暂无混淆矩阵", "请在训练中心重新训练该模型。")
    with report_tab:
        report = _localized_report(metrics)
        numeric_columns = [column for column in ("Precision", "Recall", "F1") if column in report]
        st.dataframe(
            report.style.format({column: "{:.4f}" for column in numeric_columns}),
            hide_index=True,
            width="stretch",
        )
    with curve_tab:
        curve_path = paths["metrics_dir"] / f"{model_name}_loss_curve.png"
        if curve_path.is_file():
            st.image(str(curve_path), caption=f"{metrics['display_name']} · 训练与验证损失", width="stretch")
        else:
            empty_state("没有逐轮训练曲线", "该 sklearn 模型未保存逐轮训练曲线。")
    with parameters_tab:
        st.markdown("**最佳或当前保存参数**")
        st.dataframe(
            parameter_summary_frame(metrics["display_name"], metrics["parameters"]),
            hide_index=True,
            width="stretch",
        )
        st.caption(metrics["selection_reason"])

    st.info("部署模型依据验证集 Macro F1 选择；测试集只用于最终评价。模型比较不能只看 Accuracy，手写模型主要用于展示核心算法实现过程。")


# 从相关矩阵中找出绝对值最大的非对角特征对。
def _strongest_correlation(summary: dict) -> tuple[str, str, float]:
    correlations = summary["numeric_correlations"]
    candidates = []
    for left, row in correlations.items():
        for right, value in row.items():
            if left < right:
                candidates.append((left, right, float(value)))
    return max(candidates, key=lambda item: abs(item[2]))


# 将 EDA 图表统一为适合课程展示的蓝灰视觉样式。
def _style_eda_figure(figure: go.Figure, height: int = 500) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 34, "r": 28, "t": 52, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
            "color": "#64748B",
            "size": 12,
        },
        hoverlabel={"bgcolor": "#172033", "font_color": "#FFFFFF"},
        showlegend=False,
    )
    figure.update_xaxes(
        showgrid=True,
        gridcolor="#EEF2F7",
        zeroline=False,
        linecolor="#E2E8F0",
        tickfont={"size": 11},
        title_font={"size": 12},
    )
    figure.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#E2E8F0",
        tickfont={"size": 11},
        title_font={"size": 12},
        automargin=True,
    )
    return figure


# 使用只读真实数据和结构化摘要生成当前 EDA 展示图。
def _eda_figure(chart_name: str, frame: pd.DataFrame, summary: dict) -> go.Figure:
    feature_labels = {
        "Age": "年龄",
        "Height": "身高",
        "Weight": "体重",
        "FCVC": "蔬菜摄入频率",
        "NCP": "每日主要进餐次数",
        "CH2O": "每日饮水水平",
        "FAF": "身体活动频率",
        "TUE": "电子设备使用时长",
    }
    target_column = frame.columns[-1]
    numeric_charts = {
        "年龄分布": ("Age", "年龄（岁）"),
        "身高分布": ("Height", "身高（米）"),
        "体重分布": ("Weight", "体重（千克）"),
    }
    if chart_name in numeric_charts:
        field, axis_title = numeric_charts[chart_name]
        figure = go.Figure(
            go.Histogram(
                x=frame[field],
                marker={"color": "#6B9CE8", "line": {"width": 0}},
                opacity=0.9,
                nbinsx=32,
                hovertemplate="区间：%{x}<br>样本数：%{y:,}<extra></extra>",
            )
        )
        figure.update_xaxes(title_text=axis_title)
        figure.update_yaxes(title_text="样本数")
        return _style_eda_figure(figure, 470)
    if chart_name == "目标类别分布":
        rows = sorted(
            summary["target_distribution"].items(),
            key=lambda item: item[1]["count"],
        )
        figure = go.Figure(
            go.Bar(
                x=[value["count"] for _, value in rows],
                y=[CLASS_LABELS[label] for label, _ in rows],
                orientation="h",
                marker={"color": "#6B9CE8"},
                text=[f'{value["count"]:,} · {value["ratio"] * 100:.1f}%' for _, value in rows],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{y}<br>%{text}<extra></extra>",
            )
        )
        figure.update_xaxes(title_text="样本数")
        return _style_eda_figure(figure, 470)
    if chart_name == "类别特征频数":
        fields = (
            ("Gender", "性别"),
            ("family_history_with_overweight", "超重家族史"),
            ("FAVC", "高热量食物摄入"),
            ("MTRANS", "主要交通方式"),
        )
        figure = make_subplots(rows=2, cols=2, subplot_titles=[label for _, label in fields])
        for index, (field, _) in enumerate(fields):
            counts = frame[field].value_counts().sort_values(ascending=False)
            row = index // 2 + 1
            column = index % 2 + 1
            figure.add_trace(
                go.Bar(
                    x=[CATEGORY_LABELS.get(value, str(value)) for value in counts.index],
                    y=counts.values,
                    marker={"color": "#7EA7E8"},
                    text=[f"{value:,}" for value in counts.values],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="%{x}<br>样本数：%{y:,}<extra></extra>",
                ),
                row=row,
                col=column,
            )
        return _style_eda_figure(figure, 610)
    if chart_name == "关键特征分组关系":
        grouped = summary["grouped_numeric_means"]
        labels = sorted(grouped, key=lambda label: grouped[label]["Weight"])
        figure = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("各类别平均年龄", "各类别平均体重"),
            horizontal_spacing=0.24,
        )
        for column, field in enumerate(("Age", "Weight"), start=1):
            figure.add_trace(
                go.Bar(
                    x=[grouped[label][field] for label in labels],
                    y=[CLASS_LABELS[label] for label in labels],
                    orientation="h",
                    marker={"color": "#6B9CE8"},
                    text=[f'{grouped[label][field]:.1f}' for label in labels],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="%{y}<br>均值：%{x:.2f}<extra></extra>",
                ),
                row=1,
                col=column,
            )
        return _style_eda_figure(figure, 520)
    if chart_name == "年龄身高体重关系":
        sample = frame.sample(n=min(len(frame), 2400), random_state=42)
        figure = go.Figure(
            go.Scattergl(
                x=sample["Height"],
                y=sample["Weight"],
                mode="markers",
                marker={
                    "size": 7,
                    "color": sample["Age"],
                    "colorscale": [[0, "#DCE9FA"], [1, "#2563EB"]],
                    "opacity": 0.62,
                    "colorbar": {"title": "年龄", "thickness": 12},
                },
                customdata=[CLASS_LABELS[value] for value in sample[target_column]],
                hovertemplate="身高：%{x:.2f} 米<br>体重：%{y:.1f} 千克<br>类别：%{customdata}<extra></extra>",
            )
        )
        figure.update_xaxes(title_text="身高（米）")
        figure.update_yaxes(title_text="体重（千克）")
        return _style_eda_figure(figure, 540)
    correlations = summary["numeric_correlations"]
    fields = list(correlations)
    values = [[correlations[row][column] for column in fields] for row in fields]
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=[feature_labels[field] for field in fields],
            y=[feature_labels[field] for field in fields],
            zmin=-1,
            zmax=1,
            colorscale=[[0, "#B7CBEA"], [0.5, "#FFFFFF"], [1, "#2563EB"]],
            text=[[f"{value:.2f}" for value in row] for row in values],
            texttemplate="%{text}",
            hovertemplate="%{y} × %{x}<br>相关系数：%{z:.3f}<extra></extra>",
            colorbar={"title": "相关系数", "thickness": 12},
        )
    )
    figure.update_yaxes(autorange="reversed")
    return _style_eda_figure(figure, 590)


# 展示按类别浏览的 EDA 图表中心。
def render_eda() -> None:
    page_header("数据探索分析", "按分析主题浏览真实数据图表、图表目的和简短结论。")
    try:
        _, paths = load_workflow_context()
        frame = load_csv_readonly(paths["raw_data"])
        summary = read_json(paths["figures_dir"].parent / "eda_summary.json")
        audit = read_json(paths["audit_report_dir"] / "data_audit.json")
    except (FileNotFoundError, OSError, ValueError) as error:
        show_error(error, "EDA 产物加载")
        return
    left, middle, right = st.columns(3)
    with left:
        metric_card("数据规模", f"{summary['row_count']:,} 条", "当前真实 CSV")
    with middle:
        metric_card("字段数量", str(audit["dataset_summary"]["column_count"]), "含标识与目标字段")
    with right:
        metric_card("缺失单元格", str(audit["missing_summary"]["total_missing"]), "数据审查结果")

    left_feature, right_feature, correlation = _strongest_correlation(summary)
    figures = {
        "数据分布": {
            "年龄分布": ("numeric_distributions.png", "观察年龄的集中趋势和离散程度。", "样本年龄主要集中在青年阶段，建模前已仅用训练集拟合标准化。"),
            "身高分布": ("numeric_distributions.png", "观察身高的集中趋势和离散程度。", "身高分布相对集中，但不同目标类别之间仍存在重叠。"),
            "体重分布": ("numeric_distributions.png", "观察体重的集中趋势和离散程度。", "体重的分布范围较宽，是区分类别的重要特征之一，但不能单独决定类别。"),
        },
        "类别分布": {
            "目标类别分布": ("target_distribution.png", "检查七个目标类别的样本量与比例。", f"当前最大类别占比为 {max(value['ratio'] for value in summary['target_distribution'].values()) * 100:.2f}%，模型评价同时报告宏平均指标。"),
            "类别特征频数": ("categorical_frequencies.png", "查看类别输入字段的实际取值频数。", "部分二元或交通方式取值样本较少，未知类别由预处理器安全忽略。"),
        },
        "特征与目标关系": {
            "关键特征分组关系": ("key_features_by_target.png", "比较不同目标类别下关键数值特征的分布。", "Weight 的目标组均值跨度较明显，但该关系仅描述当前数据集。"),
        },
        "多变量关系": {
            "年龄身高体重关系": ("age_height_weight_relationship.png", "联合观察 Age、Height、Weight 与目标类别。", "多变量图用于发现群组结构与重叠区域，不代表类别形成的因果机制。"),
        },
        "相关性分析": {
            "相关性热力图": ("correlation_heatmap.png", "比较数值字段之间的线性相关程度。", f"绝对相关性最高的非对角特征对为 {left_feature} 与 {right_feature}（r={correlation:.3f}）。相关性不能直接解释为因果关系。"),
        },
    }
    section_header("图表浏览器", "每次聚焦一张主图，便于课堂讲解和报告截图。")
    category = st.pills(
        "分析类别",
        options=list(figures),
        default="数据分布",
        required=True,
        key="eda_category",
        width="stretch",
        label_visibility="collapsed",
    )
    category_column, chart_column = st.columns([0.32, 0.68], gap="large")
    with category_column:
        st.markdown("**当前分类图表**")
        chart_name = st.pills(
            "选择图表",
            options=list(figures[category]),
            default=list(figures[category])[0],
            required=True,
            key="eda_chart",
            width="stretch",
            label_visibility="collapsed",
        )
        file_name, purpose, conclusion = figures[category][chart_name]
        st.markdown(
            f'<div class="card"><div class="metric-label">图表目的</div><div style="margin-top:.4rem;font-size:.84rem;line-height:1.65">{purpose}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="card"><div class="metric-label">结果摘要</div><div style="margin-top:.4rem;font-size:.84rem;line-height:1.65">{conclusion}</div></div>',
            unsafe_allow_html=True,
        )
    with chart_column:
        image_path = paths["figures_dir"] / file_name
        with st.container(border=True, key="eda_figure_card"):
            st.markdown(f"**{chart_name}**")
            try:
                figure = _eda_figure(chart_name, frame, summary)
                st.plotly_chart(
                    figure,
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                    key=f"eda_plot_{file_name}",
                )
            except (KeyError, TypeError, ValueError):
                if image_path.is_file():
                    st.image(str(image_path), width="stretch")
                else:
                    empty_state("图表文件不存在", "请先运行探索性数据分析流程。")
            st.caption("注意：展示图由只读课程数据生成，仅描述当前数据集；相关性与分组差异不代表因果关系。")


# 解析逗号分隔的隐藏层结构并校验正整数。
def _parse_hidden_layers(value: str) -> tuple[int, ...]:
    try:
        layers = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as error:
        raise ValueError("隐藏层结构必须使用逗号分隔的正整数") from error
    if not layers or any(size <= 0 for size in layers):
        raise ValueError("隐藏层结构必须至少包含一个正整数")
    return layers


# 根据模型类型显示其真实支持的训练参数。
def _training_parameters(model_name: str, config: dict) -> dict:
    defaults = config["training"][model_name]
    if model_name == "sklearn_logistic":
        candidate = defaults["candidates"][1]
        regularization = st.number_input(
            "正则化倒数 C",
            0.01,
            20.0,
            float(candidate["C"]),
            0.1,
            help="值越小，正则化越强。",
        )
        class_weight = st.selectbox(
            "类别权重",
            [None, "balanced"],
            format_func=lambda value: "不加权" if value is None else "自动平衡",
        )
        with st.expander("高级参数", expanded=False):
            max_iter = st.number_input(
                "最大迭代次数", 50, 2000, int(defaults["max_iter"]), 50
            )
        return {"C": regularization, "class_weight": class_weight, "max_iter": max_iter}
    if model_name == "sklearn_mlp":
        candidate = defaults["candidates"][0]
        layer_text = st.text_input(
            "隐藏层结构",
            value=",".join(str(value) for value in candidate["hidden_layer_sizes"]),
            help="使用逗号分隔，如 128,64。",
        )
        activation = st.segmented_control(
            "激活函数", ["relu", "tanh"], default="relu", width="stretch"
        )
        with st.expander("高级参数", expanded=False):
            alpha = st.number_input(
                "L2 正则化系数",
                0.00001,
                0.1,
                float(candidate["alpha"]),
                format="%.5f",
            )
            learning_rate = st.number_input(
                "初始学习率",
                0.0001,
                0.1,
                float(candidate["learning_rate_init"]),
                format="%.4f",
            )
            max_iter = st.number_input(
                "最大迭代次数", 50, 1000, int(defaults["max_iter"]), 25
            )
        return {
            "hidden_layer_sizes": _parse_hidden_layers(layer_text),
            "activation": activation,
            "alpha": alpha,
            "learning_rate_init": learning_rate,
            "max_iter": max_iter,
        }
    if model_name == "manual_logistic":
        learning_rate = st.number_input(
            "学习率", 0.001, 1.0, float(defaults["learning_rate"]), format="%.3f"
        )
        max_epochs = st.number_input(
            "最大训练轮数", 10, 2000, int(defaults["max_epochs"]), 10
        )
        with st.expander("高级参数", expanded=False):
            l2 = st.number_input(
                "L2 正则化系数", 0.0, 0.1, float(defaults["l2"]), format="%.4f"
            )
            patience = st.number_input(
                "早停耐心轮数", 2, 200, int(defaults["patience"]), 1
            )
            tolerance = st.number_input(
                "最小改进阈值",
                0.000001,
                0.01,
                float(defaults["tolerance"]),
                format="%.6f",
            )
        return {
            "learning_rate": learning_rate,
            "l2": l2,
            "max_epochs": max_epochs,
            "patience": patience,
            "tolerance": tolerance,
        }
    hidden_size = st.number_input(
        "隐藏层神经元数", 4, 512, int(defaults["hidden_size"]), 4
    )
    max_epochs = st.number_input(
        "最大训练轮数", 10, 1000, int(defaults["max_epochs"]), 10
    )
    with st.expander("高级参数", expanded=False):
        learning_rate = st.number_input(
            "学习率",
            0.0001,
            0.5,
            float(defaults["learning_rate"]),
            format="%.4f",
        )
        l2 = st.number_input(
            "L2 正则化系数", 0.0, 0.1, float(defaults["l2"]), format="%.4f"
        )
        batch_size = st.number_input(
            "批次大小", 16, 2048, int(defaults["batch_size"]), 16
        )
        patience = st.number_input(
            "早停耐心轮数", 2, 200, int(defaults["patience"]), 1
        )
        tolerance = st.number_input(
            "最小改进阈值",
            0.000001,
            0.01,
            float(defaults["tolerance"]),
            format="%.6f",
        )
    return {
        "hidden_size": hidden_size,
        "learning_rate": learning_rate,
        "l2": l2,
        "max_epochs": max_epochs,
        "batch_size": batch_size,
        "patience": patience,
        "tolerance": tolerance,
    }


# 展示训练完成后的核心指标、产物和显式应用操作。
def _render_training_result(result: dict) -> None:
    section_header("训练结果", "新实验已保存，但不会自动替换预测页面的活动模型。")
    test = result["test_metrics"]
    columns = st.columns(4)
    values = (
        ("模型", result["display_name"], "本次训练"),
        ("Accuracy", _percent(test["accuracy"]), "测试集最终评价"),
        ("Macro F1", _percent(test["macro_f1"]), "测试集最终评价"),
        ("训练时间", f"{result['training_time_seconds']:.3f} 秒", "本次实测"),
    )
    for column, value in zip(columns, values):
        with column:
            metric_card(*value)
    _, paths = load_workflow_context()
    tabs = st.tabs(["评估摘要", "混淆矩阵", "分类报告", "训练曲线", "参数摘要"])
    with tabs[0]:
        metric_card("Weighted F1", _percent(test["weighted_f1"]), "测试集加权指标")
        st.info(f"产物位置：{project_relative_path(paths['models_dir'] / (result['model_name'] + '.joblib'))}")
    with tabs[1]:
        st.image(str(paths["metrics_dir"] / f"{result['model_name']}_confusion_matrix.png"), width="stretch")
    with tabs[2]:
        st.dataframe(_localized_report(result), hide_index=True, width="stretch")
    with tabs[3]:
        curve = paths["metrics_dir"] / f"{result['model_name']}_loss_curve.png"
        if curve.is_file():
            st.image(str(curve), width="stretch")
        else:
            empty_state("没有逐轮训练曲线", "该 sklearn 模型未保存逐轮训练曲线。")
    with tabs[4]:
        st.dataframe(
            parameter_summary_frame(result["display_name"], result["parameters"]),
            hide_index=True,
            width="stretch",
        )
    action_columns = st.columns(2)
    with action_columns[0]:
        if st.button("保留为实验结果", width="stretch"):
            st.success("实验结果已保留在统一模型与指标目录中。")
    with action_columns[1]:
        if st.button("应用到预测页面", type="primary", width="stretch"):
            try:
                activate_model(result["model_name"])
                st.session_state.pop("prediction_result", None)
                st.success("活动模型已更新，预测页面将使用该模型。")
            except (FileNotFoundError, OSError, ValueError) as error:
                show_error(error, "活动模型更新")


# 展示动态参数、真实训练状态和结果应用流程。
def render_training() -> None:
    page_header("模型训练中心", "按模型配置真实训练参数，保存实验后再决定是否应用到预测。")
    result_step_class = "step-item active" if st.session_state.get("training_result") else "step-item"
    st.markdown(
        '<div class="step-strip">'
        '<div class="step-item active"><span class="step-number">1</span><span>选择模型与参数</span></div>'
        '<div class="step-item"><span class="step-number">2</span><span>确认训练配置</span></div>'
        f'<div class="{result_step_class}"><span class="step-number">3</span><span>查看训练结果</span></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    try:
        config, _ = load_workflow_context()
    except (FileNotFoundError, OSError, ValueError) as error:
        show_error(error, "训练配置加载")
        return
    config_column, summary_column = st.columns([1.15, 0.85], gap="large")
    with config_column:
        section_header("1 · 模型与参数配置", "只显示当前模型实际支持的参数，默认值来自 config/default.yaml。")
        model_name = st.selectbox(
            "模型类型",
            options=list(MODEL_INFO),
            format_func=lambda value: MODEL_INFO[value]["name"],
        )
        try:
            parameters = _training_parameters(model_name, config)
        except ValueError as error:
            show_error(error, "参数解析")
            return
    with summary_column:
        section_header("2 · 训练前确认", "训练会更新该模型的实验产物，但不会自动替换活动模型。")
        estimate = "通常较快，实际时间取决于参数和设备" if model_name.startswith("sklearn_") else "逐轮 NumPy 训练，轮数越高耗时越长"
        st.markdown(
            f'<div class="card"><div class="metric-label">模型</div><strong>{MODEL_INFO[model_name]["name"]}</strong>'
            f'<div class="metric-help" style="margin-top:.7rem">实现：{MODEL_INFO[model_name]["implementation"]}<br>耗时提示：{estimate}<br>选择依据：验证集指标或验证损失早停</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("**参数摘要**")
        st.dataframe(
            parameter_summary_frame(MODEL_INFO[model_name]["name"], parameters),
            hide_index=True,
            width="stretch",
        )
        with st.expander("查看原始配置", expanded=False):
            st.code(json.dumps(parameters, ensure_ascii=False, indent=2), language="json")
        confirmed = st.checkbox("我已确认参数，并了解测试集不参与调参或活动模型选择。")
        start = st.button("开始训练", type="primary", width="stretch", disabled=not confirmed)
    if start:
        section_header("3 · 训练过程", "sklearn 模型无法提供可靠逐轮回调，因此使用真实阶段式状态。")
        progress = st.progress(0, text="正在加载并校验数据……")
        status = st.status("训练任务进行中", expanded=True)
        started_at = perf_counter()
        elapsed_placeholder = st.empty()
        try:
            elapsed_placeholder.caption("已运行时间：0.00 秒")
            status.write("正在加载数据并复用固定分层划分。")
            progress.progress(15, text="正在准备训练集与预处理器……")
            sleep(0.05)
            status.write("正在构建模型并执行训练、验证与测试评估。")
            progress.progress(35, text="正在训练模型；此阶段使用真实算法运行时间……")
            result = train_selected_model(model_name, parameters)
            elapsed_placeholder.caption(f"已运行时间：{perf_counter() - started_at:.2f} 秒")
            status.write("训练完成，正在读取已保存的评估产物。")
            progress.progress(85, text="正在整理混淆矩阵、分类报告与参数摘要……")
            sleep(0.05)
            progress.progress(100, text="训练与产物保存完成。")
            status.update(label="训练任务已完成", state="complete", expanded=False)
            st.session_state["training_result"] = result
            st.success("训练完成。实验结果已保存，活动模型保持不变。")
        except (FileNotFoundError, OSError, ValueError, RuntimeError, FloatingPointError) as error:
            status.update(label="训练任务未完成", state="error", expanded=True)
            progress.empty()
            show_error(error, "模型训练")
    result = st.session_state.get("training_result")
    if result is None:
        section_header("训练结果", "完成一次训练后，这里会显示真实指标、图表和模型应用操作。")
        empty_state(
            "暂无本次训练结果",
            "确认参数后点击“开始训练”，或查看最近保存的正式实验。",
            ("页面打开不会自动训练", "训练完成后活动模型保持不变"),
        )
        if st.button("查看最近已保存结果", key="show_saved_training_result"):
            try:
                st.session_state["training_result"] = load_model_metrics(model_name)
                st.rerun()
            except (FileNotFoundError, OSError, ValueError) as error:
                show_error(error, "最近训练结果加载")
    else:
        _render_training_result(result)


# 展示项目定位、技术流程、模型差异与使用边界。
def render_about() -> None:
    page_header("项目说明", "用一页内容了解项目目标、技术流程、四模型设计和系统使用方法。")
    st.markdown(
        '<div class="hero"><span class="page-kicker">《人工智能综合实践》课程设计</span>'
        '<h2>从真实数据到可解释的多分类演示系统</h2>'
        '<p>项目使用固定随机种子、目标分层划分和训练集拟合预处理，统一比较 sklearn 与 NumPy 手写实现，并通过交互界面展示预测与实验结果。</p></div>',
        unsafe_allow_html=True,
    )
    section_header("技术流程", "测试集只在最后评价阶段使用，不进入预处理拟合、调参或部署选择。")
    steps = ["原始数据", "数据审查", "数据清洗", "特征预处理", "分层划分", "模型训练", "模型评估", "交互预测"]
    flow = []
    for index, step in enumerate(steps):
        flow.append(f'<span class="flow-step">{step}</span>')
        if index < len(steps) - 1:
            flow.append('<span class="flow-arrow">→</span>')
    st.markdown(f'<div class="flow">{"".join(flow)}</div>', unsafe_allow_html=True)

    section_header("设计目标与模型结构")
    columns = st.columns(2)
    with columns[0]:
        st.markdown('<div class="card feature-card"><span class="badge">01</span><strong>设计目标</strong><div class="metric-help" style="margin-top:.55rem;line-height:1.65;white-space:normal">基于真实 CSV 完成可复现、可解释、可测试的七类别系统；统一数据入口、划分、预处理和评估标准。</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card feature-card"><span class="badge">03</span><strong>sklearn 实现</strong><div class="metric-help" style="margin-top:.55rem;line-height:1.65;white-space:normal">使用 LogisticRegression 与 MLPClassifier，侧重成熟优化、稳定基线和工程化 Pipeline。</div></div>', unsafe_allow_html=True)
    with columns[1]:
        st.markdown('<div class="card feature-card"><span class="badge">02</span><strong>数据泄漏防护</strong><div class="metric-help" style="margin-top:.55rem;line-height:1.65;white-space:normal">训练集拟合全部预处理器，验证集用于参数与早停，测试集仅用于最终指标、矩阵和报告。</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card feature-card"><span class="badge">04</span><strong>NumPy 手写实现</strong><div class="metric-help" style="margin-top:.55rem;line-height:1.65;white-space:normal">实现 Softmax、交叉熵、梯度下降、反向传播、L2、mini-batch 与早停，侧重算法过程展示。</div></div>', unsafe_allow_html=True)

    section_header("四模型结构对比", "成熟库实现用于稳定基线，手写实现用于展示核心算法过程。")
    model_columns = st.columns(4)
    model_details = (
        ("sklearn 逻辑回归", "线性分类", "成熟优化 · 稳定基线"),
        ("sklearn 神经网络", "多层感知机", "非线性表达 · 自动早停"),
        ("NumPy 手写逻辑回归", "Softmax", "梯度下降 · L2"),
        ("NumPy 手写神经网络", "单隐藏层", "反向传播 · mini-batch"),
    )
    for column, (name, structure, detail) in zip(model_columns, model_details):
        with column:
            metric_card(name, structure, detail, model_value=True)

    section_header("评价指标", "类别分布存在差异，因此不能只看 Accuracy。")
    metric_columns = st.columns(4)
    explanations = (
        ("Accuracy", "整体预测正确比例"),
        ("Precision / Recall", "分别观察预测准确性与类别覆盖"),
        ("Macro F1", "七个类别等权平均，作为部署主指标"),
        ("Weighted F1", "按各类别样本量加权"),
    )
    for column, (title, detail) in zip(metric_columns, explanations):
        with column:
            metric_card(title, title, detail)

    section_header("系统使用方法")
    st.markdown("1. 在预测页填写或加载一条样本，查看七类概率。  \n2. 在性能页切换模型，阅读指标、混淆矩阵和分类报告。  \n3. 在 EDA 页按主题浏览图表。  \n4. 在训练中心确认参数并训练；只有点击“应用到预测页面”才会更新活动模型。")
    disclaimer()


PAGE_RENDERERS = {
    "系统概览": render_overview,
    "肥胖风险预测": render_prediction,
    "模型性能分析": render_performance,
    "数据探索分析": render_eda,
    "模型训练中心": render_training,
    "项目说明": render_about,
}
