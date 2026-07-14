import streamlit as st

from application.workflows import load_workflow_context
from ui.constants import MODEL_INFO, NAV_ITEMS
from ui.pages import PAGE_RENDERERS
from ui.services import read_json
from ui.styles import APP_CSS


# 配置应用外壳、侧边导航并渲染当前页面。
def run_app() -> None:
    st.set_page_config(
        page_title="肥胖风险预测系统",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(
            '<div class="brand"><span class="brand-mark">AI</span>'
            '<span class="brand-name">肥胖风险预测</span>'
            '<div class="brand-sub">课程数据分析应用</div></div>',
            unsafe_allow_html=True,
        )
        selected_page = st.radio(
            "页面导航",
            options=NAV_ITEMS,
            key="navigation",
            label_visibility="collapsed",
        )
        try:
            _, paths = load_workflow_context()
            active = read_json(paths["models_dir"] / "best_model.json")["model_name"]
            model_label = MODEL_INFO[active]["name"]
            system_status = "运行正常"
        except (FileNotFoundError, OSError, ValueError, KeyError):
            model_label = "尚未加载"
            system_status = "等待模型产物"
        st.markdown(
            '<div class="sidebar-footer"><div class="label">当前活动模型</div>'
            f'<div class="value">{model_label}</div><div class="label">系统状态</div>'
            f'<div class="value">● {system_status}</div>'
            '<div class="legal">仅用于课程演示，不构成医学诊断、健康评估或治疗建议。</div></div>',
            unsafe_allow_html=True,
        )
    try:
        PAGE_RENDERERS[selected_page]()
    except Exception as error:
        st.error(f"页面暂时无法显示：{error}。请检查相关产物后重试，其他页面不受影响。")
