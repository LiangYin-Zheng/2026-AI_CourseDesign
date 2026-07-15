import html

import pandas as pd
import streamlit as st

from ui.constants import DISCLAIMER


# 输出统一的页面标题和一句话说明。
def page_header(title: str, subtitle: str, kicker: str = "肥胖风险预测系统") -> None:
    st.markdown(
        '<div class="page-header">'
        f'<div class="page-kicker">{html.escape(kicker)}</div>'
        f'<div class="page-title">{html.escape(title)}</div>'
        f'<div class="page-subtitle">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


# 输出统一的模块标题与可选说明。
def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>'
        f'<div class="section-subtitle">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


# 输出层级统一的核心指标卡片。
def metric_card(
    label: str, value: str, help_text: str = "", model_value: bool = False
) -> None:
    value_class = "metric-value is-model" if model_value else "metric-value"
    st.markdown(
        '<div class="metric-card">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="{value_class}">{html.escape(value)}</div>'
        f'<div class="metric-help">{html.escape(help_text)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


# 生成紧凑预测结果卡的安全 HTML。
def prediction_result_card_html(
    chinese_label: str,
    english_label: str,
    confidence: str,
    model_name: str,
    model_kind: str,
    elapsed: str,
    animate: bool = False,
) -> str:
    card_class = "result-card result-enter" if animate else "result-card"
    return (
        f'<div class="{card_class}">'
        '<span class="status-pill"><span class="status-dot"></span>预测完成</span>'
        '<div class="result-summary">'
        '<div class="result-primary"><div class="result-label">预测结果</div>'
        f'<div class="result-class">{html.escape(chinese_label)}</div>'
        f'<div class="result-original">{html.escape(english_label)}</div></div>'
        '<div class="result-score"><div class="result-label">模型置信度</div>'
        f'<div class="result-confidence">{html.escape(confidence)}</div></div></div>'
        '<div class="result-divider"></div><div class="result-meta-grid">'
        '<div><span>使用模型</span>'
        f'<strong>{html.escape(model_name)}</strong></div>'
        '<div><span>模型类型</span>'
        f'<strong>{html.escape(model_kind)}</strong></div>'
        '<div><span>推理耗时</span>'
        f'<strong>{html.escape(elapsed)}</strong></div>'
        '</div></div>'
    )


# 输出带运行圆点的低饱和状态徽标。
def status_pill(text: str) -> None:
    st.markdown(
        '<span class="status-pill"><span class="status-dot"></span>'
        f"{html.escape(text)}</span>",
        unsafe_allow_html=True,
    )


# 在无结果或无产物时输出清楚的空状态。
def empty_state(
    title: str, detail: str, features: tuple[str, ...] = ()
) -> None:
    feature_html = ""
    if features:
        feature_items = "".join(
            f'<div class="empty-feature">{html.escape(item)}</div>' for item in features
        )
        feature_html = f'<div class="empty-features">{feature_items}</div>'
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">⌁</div>'
        f"<strong>{html.escape(title)}</strong>"
        f'<div style="margin-top:.45rem;font-size:.8rem">{html.escape(detail)}</div>'
        f"{feature_html}</div>",
        unsafe_allow_html=True,
    )


# 显示固定课程演示免责声明。
def disclaimer() -> None:
    st.markdown(f'<div class="notice">{html.escape(DISCLAIMER)}</div>', unsafe_allow_html=True)


# 将常见运行错误转换为不含堆栈的用户提示。
def show_error(error: Exception, action: str) -> None:
    st.error(f"{action}失败：{error}。其他已加载页面不受影响，请检查相关数据或模型产物后重试。")


# 将训练参数转换为适合确认区阅读的中文表格。
def parameter_summary_frame(model_name: str, parameters: dict) -> pd.DataFrame:
    labels = {
        "C": "正则化倒数 C",
        "class_weight": "类别权重",
        "max_iter": "最大迭代次数",
        "hidden_layer_sizes": "隐藏层结构",
        "activation": "激活函数",
        "alpha": "L2 正则化系数",
        "learning_rate_init": "初始学习率",
        "learning_rate": "学习率",
        "l2": "L2 正则化系数",
        "max_epochs": "最大训练轮数",
        "patience": "早停耐心轮数",
        "tolerance": "最小改进阈值",
        "hidden_size": "隐藏层神经元数",
        "batch_size": "批次大小",
    }
    rows = [{"参数": "模型", "当前设置": model_name}]
    for key, value in parameters.items():
        if key == "class_weight":
            value = "不加权" if value is None else "自动平衡"
        elif isinstance(value, (tuple, list)):
            value = " × ".join(str(item) for item in value)
        rows.append({"参数": labels.get(key, key), "当前设置": str(value)})
    return pd.DataFrame(rows)
