import html

import streamlit as st

from ui.constants import DISCLAIMER


# 输出统一的页面标题和一句话说明。
def page_header(title: str, subtitle: str, kicker: str = "肥胖风险预测系统") -> None:
    st.markdown(
        f'<div class="page-kicker">{html.escape(kicker)}</div>'
        f'<div class="page-title">{html.escape(title)}</div>'
        f'<div class="page-subtitle">{html.escape(subtitle)}</div>',
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
def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        '<div class="metric-card">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'<div class="metric-help">{html.escape(help_text)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


# 输出带运行圆点的低饱和状态徽标。
def status_pill(text: str) -> None:
    st.markdown(
        '<span class="status-pill"><span class="status-dot"></span>'
        f"{html.escape(text)}</span>",
        unsafe_allow_html=True,
    )


# 在无结果或无产物时输出清楚的空状态。
def empty_state(title: str, detail: str) -> None:
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">◇</div>'
        f"<strong>{html.escape(title)}</strong>"
        f'<div style="margin-top:.45rem;font-size:.82rem">{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


# 显示固定课程演示免责声明。
def disclaimer() -> None:
    st.markdown(f'<div class="notice">{html.escape(DISCLAIMER)}</div>', unsafe_allow_html=True)


# 将常见运行错误转换为不含堆栈的用户提示。
def show_error(error: Exception, action: str) -> None:
    st.error(f"{action}失败：{error}。其他已加载页面不受影响，请检查相关数据或模型产物后重试。")
