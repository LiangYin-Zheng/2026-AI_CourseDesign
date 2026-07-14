APP_CSS = """
<style>
:root {
    --primary: #1F4E79;
    --accent: #3A7CA5;
    --soft-blue: #EEF5FA;
    --background: #F6F8FA;
    --surface: #FFFFFF;
    --border: #DDE3E8;
    --text: #1F2933;
    --muted: #667085;
    --success: #437A63;
    --warning: #A66A2C;
}
.stApp { background: var(--background); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 1.25rem 1rem; }
[data-testid="stMainBlockContainer"] {
    max-width: 1440px;
    padding: 2.1rem 2.4rem 4rem;
}
#MainMenu, footer { visibility: hidden; }
h1, h2, h3 { color: var(--text); letter-spacing: -0.02em; }
p { color: var(--text); }
.brand {
    padding: .45rem .4rem 1.1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.brand-mark {
    width: 38px; height: 38px; border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    color: white; background: var(--primary); font-weight: 750;
    margin-right: .65rem; vertical-align: middle;
}
.brand-name { color: var(--text); font-size: 1rem; font-weight: 720; vertical-align: middle; }
.brand-sub { color: var(--muted); font-size: .75rem; margin: .55rem 0 0 3.05rem; }
.page-kicker { color: var(--accent); font-size: .76rem; font-weight: 700; letter-spacing: .09em; }
.page-title { color: var(--text); font-size: 2rem; font-weight: 760; margin: .18rem 0 .32rem; }
.page-subtitle { color: var(--muted); font-size: .96rem; margin: 0 0 1.35rem; }
.hero {
    background: linear-gradient(115deg, #FFFFFF 0%, #F2F7FB 100%);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 1.8rem 2rem; margin-bottom: 1.2rem;
    box-shadow: 0 4px 16px rgba(31, 78, 121, .045);
}
.hero h2 { font-size: 1.65rem; margin: .15rem 0 .5rem; }
.hero p { color: var(--muted); max-width: 720px; margin: 0; line-height: 1.7; }
.card, .metric-card, .empty-state, .result-card, .notice {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    box-shadow: 0 2px 10px rgba(31, 41, 51, .035);
}
.card { padding: 1.15rem 1.25rem; margin-bottom: .8rem; }
.metric-card { min-height: 116px; padding: 1rem 1.05rem; }
.metric-label { color: var(--muted); font-size: .78rem; font-weight: 650; }
.metric-value { color: var(--primary); font-size: 1.62rem; font-weight: 760; margin: .35rem 0 .2rem; }
.metric-help { color: #85909D; font-size: .72rem; line-height: 1.35; }
.section-title { font-size: 1.08rem; font-weight: 720; color: var(--text); margin: 1.6rem 0 .3rem; }
.section-subtitle { color: var(--muted); font-size: .82rem; margin-bottom: .8rem; }
.status-pill {
    display: inline-flex; align-items: center; gap: .4rem; border-radius: 99px;
    padding: .3rem .65rem; font-size: .74rem; font-weight: 650;
    background: #EAF4EF; color: var(--success); border: 1px solid #CFE3D8;
}
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.result-card { padding: 1.5rem; border-top: 4px solid var(--primary); }
.result-label { color: var(--muted); font-size: .8rem; }
.result-class { color: var(--primary); font-weight: 780; font-size: 2rem; margin: .25rem 0; }
.result-original { color: var(--muted); font-size: .78rem; }
.result-confidence { font-size: 1.45rem; font-weight: 730; color: var(--text); margin-top: 1rem; }
.empty-state { padding: 3.2rem 1.4rem; text-align: center; color: var(--muted); }
.empty-icon {
    width: 48px; height: 48px; margin: 0 auto .8rem; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    background: var(--soft-blue); color: var(--primary); font-size: 1.3rem;
}
.notice { padding: .8rem 1rem; color: var(--muted); font-size: .78rem; line-height: 1.55; }
.flow { display: flex; align-items: center; flex-wrap: wrap; gap: .45rem; margin: 1rem 0; }
.flow-step { background: var(--soft-blue); color: var(--primary); border: 1px solid #D7E7F2; border-radius: 9px; padding: .52rem .72rem; font-size: .78rem; font-weight: 650; }
.flow-arrow { color: #8AA4B8; }
.sidebar-footer { margin-top: 1.2rem; padding: .9rem; background: var(--soft-blue); border-radius: 10px; }
.sidebar-footer .label { color: var(--muted); font-size: .7rem; }
.sidebar-footer .value { color: var(--primary); font-size: .82rem; font-weight: 700; margin: .18rem 0 .65rem; }
.sidebar-footer .legal { color: var(--muted); font-size: .66rem; line-height: 1.45; border-top: 1px solid #D5E3EC; padding-top: .65rem; }
.stButton > button, .stFormSubmitButton > button { border-radius: 9px; font-weight: 650; min-height: 2.55rem; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background: var(--primary); border-color: var(--primary); }
[data-testid="stMetric"] { background: white; border: 1px solid var(--border); border-radius: 12px; padding: .85rem 1rem; }
[data-baseweb="tab-list"] { gap: .35rem; }
[data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: .65rem 1rem; }
[data-testid="stExpander"] { background: white; border: 1px solid var(--border); border-radius: 10px; }
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding: 1.4rem 1rem 3rem; }
    .page-title { font-size: 1.65rem; }
}
</style>
"""
