APP_CSS = """
<style>
:root {
    --color-primary: #2563EB;
    --color-primary-dark: #1D4ED8;
    --color-primary-soft: #EFF6FF;
    --color-background: #F6F8FB;
    --color-surface: #FFFFFF;
    --color-surface-soft: #F8FAFC;
    --color-text: #172033;
    --color-text-secondary: #64748B;
    --color-text-muted: #94A3B8;
    --color-border: #E2E8F0;
    --color-border-strong: #CBD5E1;
    --color-success: #16865C;
    --color-success-soft: #ECFDF5;
    --color-warning: #B76E00;
    --color-warning-soft: #FFF7E6;
    --color-danger: #C53B46;
    --color-danger-soft: #FFF1F2;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --radius-xl: 22px;
    --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
    --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.06);
    --shadow-hover: 0 12px 30px rgba(15, 23, 42, 0.09);
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --font-system: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
}

@keyframes ui-fade-up {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes status-breathe {
    0%, 100% { box-shadow: 0 0 0 0 rgba(22, 134, 92, 0); }
    50% { box-shadow: 0 0 0 4px rgba(22, 134, 92, .10); }
}

html, body, .stApp, button, input, textarea, [data-baseweb] {
    font-family: var(--font-system);
}
.stApp {
    background: var(--color-background);
    color: var(--color-text);
}
[data-testid="stHeader"] {
    background: transparent;
    height: 2.6rem;
}
[data-testid="stMainBlockContainer"] {
    max-width: 1320px;
    padding: 1.65rem 2.25rem 4rem;
}
#MainMenu, footer { visibility: hidden; }
h1, h2, h3, p { color: var(--color-text); }
h1, h2, h3 { letter-spacing: -0.018em; }

[data-testid="stSidebar"] {
    min-width: 17rem;
    max-width: 17rem;
    background: var(--color-surface);
    border-right: 1px solid var(--color-border);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1.15rem .9rem .85rem;
}
.brand {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr);
    column-gap: var(--space-3);
    align-items: center;
    padding: var(--space-2) var(--space-2) var(--space-4);
    border-bottom: 1px solid var(--color-border);
    margin-bottom: var(--space-3);
}
.brand-mark {
    grid-row: span 2;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    background: var(--color-primary);
    box-shadow: 0 7px 18px rgba(37, 99, 235, 0.2);
    font-size: .82rem;
    font-weight: 760;
}
.brand-name {
    color: var(--color-text);
    font-size: .96rem;
    font-weight: 740;
    line-height: 1.3;
}
.brand-sub {
    color: var(--color-text-secondary);
    font-size: .76rem;
    line-height: 1.4;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { gap: var(--space-1); }
[data-testid="stSidebar"] label[data-testid="stRadioOption"] {
    position: relative;
    min-height: 44px;
    padding: 0 var(--space-3);
    border-radius: 11px;
    color: var(--color-text-secondary);
    transition: background-color .16s ease, color .16s ease, box-shadow .16s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div > div:not([data-testid]) {
    display: none;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] p {
    color: inherit;
    font-size: .86rem;
    font-weight: 590;
    line-height: 1.2;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] [data-testid="stIconMaterial"] {
    font-size: 18px;
    width: 18px;
    min-width: 18px;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover {
    background: var(--color-surface-soft);
    color: var(--color-text);
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {
    background: var(--color-primary-soft);
    color: var(--color-primary-dark);
    box-shadow: inset 3px 0 0 var(--color-primary);
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:focus-within {
    outline: none;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] span:focus-visible {
    outline: none;
}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:focus-within:not([data-selected="true"]) {
    background: var(--color-surface-soft);
    box-shadow: inset 0 0 0 1px var(--color-border-strong);
}
.sidebar-footer {
    margin-top: var(--space-5);
    padding: var(--space-3);
    background: var(--color-surface-soft);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}
.sidebar-footer .label {
    color: var(--color-text-muted);
    font-size: .68rem;
    font-weight: 650;
    letter-spacing: .03em;
}
.sidebar-footer .model-row {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin: var(--space-1) 0 var(--space-2);
    min-width: 0;
}
.sidebar-footer .model-name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text);
    font-size: .8rem;
    font-weight: 710;
}
.badge, .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    padding: 5px 9px;
    font-size: .68rem;
    font-weight: 680;
    line-height: 1;
}
.badge {
    flex: 0 0 auto;
    color: var(--color-primary-dark);
    background: var(--color-primary-soft);
    border: 1px solid #D9E8FF;
}
.status-pill {
    color: var(--color-success);
    background: var(--color-success-soft);
    border: 1px solid #CDEEDF;
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--color-success);
    animation: status-breathe 3.2s ease-in-out infinite;
}
.sidebar-footer .status-row {
    display: flex;
    align-items: center;
    gap: 7px;
    color: var(--color-success);
    font-size: .76rem;
    font-weight: 650;
    margin: var(--space-2) 0 0;
}
.sidebar-footer .legal {
    color: var(--color-text-secondary);
    font-size: .65rem;
    line-height: 1.4;
    margin-top: 2px;
}

.page-header { margin-bottom: var(--space-5); animation: ui-fade-up 190ms ease-out both; }
.page-kicker {
    color: var(--color-primary);
    font-size: .76rem;
    font-weight: 680;
    letter-spacing: .055em;
}
.page-title {
    color: var(--color-text);
    font-size: clamp(2rem, 3vw, 2.35rem);
    font-weight: 760;
    line-height: 1.18;
    margin: 7px 0 8px;
}
.page-subtitle {
    color: var(--color-text-secondary);
    font-size: 1rem;
    line-height: 1.55;
    margin: 0;
}
.section-title {
    font-size: 1.08rem;
    font-weight: 720;
    color: var(--color-text);
    margin: var(--space-6) 0 5px;
}
.section-subtitle {
    color: var(--color-text-secondary);
    font-size: .8rem;
    line-height: 1.55;
    margin-bottom: var(--space-3);
}

.hero, .overview-banner, .card, .metric-card, .empty-state, .result-card, .notice, .chart-card, .step-strip {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    box-shadow: var(--shadow-sm);
}
.hero, .overview-banner { border-radius: var(--radius-xl); }
.card, .metric-card, .empty-state, .result-card, .chart-card, .step-strip { border-radius: var(--radius-lg); }
.card, .metric-card, .chart-card {
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
.card:hover, .metric-card:hover, .chart-card:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-hover);
    transform: translateY(-1px);
}
.hero {
    padding: var(--space-6) var(--space-8);
    margin-bottom: var(--space-5);
    background: linear-gradient(120deg, #FFFFFF 0%, #F3F7FF 100%);
}
.hero h2 { font-size: 1.45rem; margin: var(--space-2) 0; }
.hero p {
    color: var(--color-text-secondary);
    max-width: 800px;
    margin: 0;
    line-height: 1.65;
    font-size: .88rem;
}
.overview-banner {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-8);
    align-items: center;
    min-height: 176px;
    padding: var(--space-6) var(--space-8);
    background: linear-gradient(120deg, #FFFFFF 0%, #F3F7FF 100%);
}
.overview-banner h2 { font-size: 1.5rem; margin: var(--space-3) 0 var(--space-2); }
.overview-banner p {
    color: var(--color-text-secondary);
    font-size: .86rem;
    line-height: 1.65;
    margin: 0;
    max-width: 650px;
}
.banner-meta {
    min-width: 245px;
    padding-left: var(--space-6);
    border-left: 1px solid var(--color-border);
}
.banner-model {
    color: var(--color-text);
    font-size: 1rem;
    font-weight: 720;
    margin: var(--space-1) 0 var(--space-2);
    white-space: nowrap;
}
.banner-time { color: var(--color-text-secondary); font-size: .72rem; }
.card { padding: var(--space-5); margin-bottom: var(--space-3); }
.feature-card { min-height: 132px; }
.feature-card .badge { margin-right: var(--space-2); }
.metric-card {
    min-height: 126px;
    height: 100%;
    padding: var(--space-5);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
}
.metric-label {
    color: var(--color-text-secondary);
    font-size: .75rem;
    font-weight: 650;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-value {
    color: var(--color-text);
    font-size: clamp(1.32rem, 2.1vw, 1.72rem);
    font-weight: 760;
    font-variant-numeric: tabular-nums;
    line-height: 1.18;
    margin: var(--space-2) 0;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
}
.metric-value.is-model { font-size: 1.12rem; white-space: nowrap; text-overflow: ellipsis; display: block; }
.metric-help {
    color: var(--color-text-muted);
    font-size: .7rem;
    line-height: 1.45;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.result-card {
    padding: var(--space-5);
    border-top: 3px solid var(--color-primary);
    box-shadow: var(--shadow-md);
}
.result-enter { animation: ui-fade-up 210ms ease-out both; }
.result-label { color: var(--color-text-secondary); font-size: .76rem; }
.result-summary {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
    gap: var(--space-5);
    margin-top: var(--space-4);
}
.result-class { color: var(--color-primary-dark); font-weight: 780; font-size: clamp(2rem, 3vw, 2.3rem); line-height: 1.12; margin: var(--space-1) 0; }
.result-original { color: var(--color-text-secondary); font-size: .82rem; white-space: nowrap; }
.result-score { text-align: right; }
.result-confidence { font-size: clamp(1.75rem, 2.6vw, 2.05rem); line-height: 1.1; font-weight: 760; color: var(--color-text); margin-top: var(--space-1); font-variant-numeric: tabular-nums; white-space: nowrap; }
.result-divider { height: 1px; background: var(--color-border); margin: var(--space-4) 0; }
.result-meta-grid {
    display: grid;
    grid-template-columns: 1.35fr 1fr .75fr;
    gap: var(--space-4);
}
.result-meta-grid div { min-width: 0; }
.result-meta-grid span { display: block; color: var(--color-text-muted); font-size: .75rem; margin-bottom: 4px; }
.result-meta-grid strong { display: block; color: var(--color-text); font-size: .9rem; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.empty-state {
    padding: var(--space-8) var(--space-6);
    text-align: center;
    color: var(--color-text-secondary);
}
.empty-icon {
    width: 52px;
    height: 52px;
    margin: 0 auto var(--space-3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary-soft);
    color: var(--color-primary);
    font-size: 1.25rem;
}
.empty-features {
    display: grid;
    gap: var(--space-2);
    max-width: 330px;
    margin: var(--space-5) auto 0;
    text-align: left;
}
.empty-feature {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--color-text-secondary);
    font-size: .75rem;
}
.empty-feature::before {
    content: "✓";
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    color: var(--color-primary);
    background: var(--color-primary-soft);
    font-size: .65rem;
    font-weight: 800;
}
.notice {
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-4);
    color: var(--color-text-secondary);
    font-size: .75rem;
    line-height: 1.55;
}
.chart-card { padding: var(--space-4) var(--space-5) var(--space-2); }
.chart-title { color: var(--color-text); font-size: .88rem; font-weight: 700; }
.chart-note { color: var(--color-text-secondary); font-size: .72rem; margin-top: 3px; }

.step-strip {
    display: flex;
    align-items: center;
    min-height: 66px;
    gap: var(--space-2);
    padding: var(--space-3) var(--space-4);
    margin-bottom: var(--space-5);
    animation: ui-fade-up 190ms ease-out both;
}
.training-step {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex: 0 0 auto;
    color: var(--color-text-secondary);
}
.training-step-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    color: var(--color-text-secondary);
    background: var(--color-surface);
    border: 1.5px solid var(--color-border-strong);
    font-size: .72rem;
    font-weight: 720;
    transition: color 150ms ease, background-color 150ms ease, border-color 150ms ease;
}
.training-step-text { font-size: .78rem; font-weight: 650; white-space: nowrap; }
.training-step.active { color: var(--color-primary-dark); }
.training-step.active .training-step-dot { color: #FFFFFF; background: var(--color-primary); border-color: var(--color-primary); }
.training-step.complete { color: var(--color-success); }
.training-step.complete .training-step-dot { color: #FFFFFF; background: var(--color-success); border-color: var(--color-success); }
.training-step.error { color: var(--color-danger); }
.training-step.error .training-step-dot { color: #FFFFFF; background: var(--color-danger); border-color: var(--color-danger); }
.training-step-line { flex: 1 1 70px; min-width: 26px; height: 1.5px; background: var(--color-border); transition: background-color 200ms ease; }
.training-step-line.complete { background: #9BD7BE; }
.parameter-table { width: 100%; border-collapse: collapse; font-size: .78rem; }
.parameter-table td { padding: 9px 4px; border-bottom: 1px solid var(--color-border); }
.parameter-table td:first-child { color: var(--color-text-secondary); width: 44%; }
.parameter-table td:last-child { color: var(--color-text); font-weight: 640; text-align: right; }

.flow {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin: var(--space-4) 0;
    padding: var(--space-4);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
}
.flow-step {
    background: var(--color-primary-soft);
    color: var(--color-primary-dark);
    border: 1px solid #D9E8FF;
    border-radius: var(--radius-sm);
    padding: 9px 12px;
    font-size: .75rem;
    font-weight: 650;
    white-space: nowrap;
}
.flow-arrow { color: var(--color-text-muted); line-height: 1; }

.stButton > button, .stFormSubmitButton > button {
    min-height: 44px;
    border-radius: 12px;
    border-color: var(--color-border-strong);
    color: var(--color-text);
    background: var(--color-surface);
    font-weight: 650;
    box-shadow: var(--shadow-sm);
    transition: background-color .16s ease, border-color .16s ease, box-shadow .16s ease, transform .12s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    color: var(--color-primary-dark);
    border-color: #AFC8F8;
    background: var(--color-primary-soft);
    box-shadow: var(--shadow-md);
}
.stButton > button:not(:disabled):active, .stFormSubmitButton > button:not(:disabled):active { transform: scale(.99); }
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    color: #FFFFFF;
    background: var(--color-primary);
    border-color: var(--color-primary);
}
.stButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p {
    color: #FFFFFF;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    color: #FFFFFF;
    background: var(--color-primary-dark);
    border-color: var(--color-primary-dark);
}
.stButton > button:disabled, .stFormSubmitButton > button:disabled {
    color: var(--color-text-muted);
    background: #EEF2F7;
    border-color: var(--color-border);
    opacity: .78;
    box-shadow: none;
}
.stButton > button:disabled p, .stFormSubmitButton > button:disabled p { color: var(--color-text-muted); }
[data-baseweb="input"], [data-baseweb="select"] > div {
    min-height: 44px;
    border-radius: 12px;
    background: var(--color-surface);
    border-color: var(--color-border-strong);
    transition: border-color .16s ease, box-shadow .16s ease;
}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
}
[data-testid="stWidgetLabel"] p { color: var(--color-text); font-size: .79rem; font-weight: 620; }
[data-testid="stExpander"] {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}
[data-testid="stExpander"] summary {
    min-height: 52px;
    background: var(--color-surface-soft);
    color: var(--color-text);
}
[data-testid="stExpander"] details[open] summary { background: var(--color-primary-soft); }
[data-baseweb="tab-list"] {
    gap: var(--space-1);
    padding: var(--space-1);
    background: var(--color-surface-soft);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
}
[data-baseweb="tab"] {
    border-radius: var(--radius-sm);
    padding: .58rem .9rem;
    color: var(--color-text-secondary);
}
[data-baseweb="tab"][aria-selected="true"] {
    color: var(--color-primary-dark);
    background: var(--color-surface);
    box-shadow: var(--shadow-sm);
}
[data-testid="stSegmentedControl"] [role="radiogroup"], [data-testid="stPills"] [role="radiogroup"] {
    padding: var(--space-1);
    background: var(--color-surface-soft);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
}
[data-testid="stDataFrame"] { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--color-border); }
[data-testid="stAlert"] { border-radius: var(--radius-md); border: 1px solid var(--color-border); }
[class*="st-key-overview_banner"] [data-testid="stVerticalBlockBorderWrapper"] {
    min-height: 176px;
    padding: var(--space-6) var(--space-8);
    background: linear-gradient(120deg, #FFFFFF 0%, #F3F7FF 100%);
    border-radius: var(--radius-xl);
    border-color: var(--color-border);
    box-shadow: var(--shadow-sm);
}
[class*="st-key-overview_banner"] .stButton { margin-top: var(--space-4); }
[class*="st-key-overview_rank_chart"] [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-performance_chart"] [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-eda_figure_card"] [data-testid="stVerticalBlockBorderWrapper"] {
    padding: var(--space-4);
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    border-color: var(--color-border);
    box-shadow: var(--shadow-sm);
}
[class*="st-key-training_result_actions"] [data-testid="stVerticalBlockBorderWrapper"] {
    margin-top: var(--space-5);
    padding: var(--space-4);
    background: var(--color-surface-soft);
    border-radius: var(--radius-lg);
    border-color: var(--color-border);
}

@media (max-width: 1100px) {
    [data-testid="stSidebar"] { min-width: 15rem; max-width: 15rem; }
    [data-testid="stMainBlockContainer"] { padding: 1.4rem 1.35rem 3rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 245px; flex: 1 1 42%; }
    .overview-banner { grid-template-columns: 1fr; min-height: auto; gap: var(--space-5); }
    .banner-meta { padding-left: 0; padding-top: var(--space-4); border-left: 0; border-top: 1px solid var(--color-border); }
    .metric-card { min-height: 116px; }
    .result-summary, .result-meta-grid { grid-template-columns: 1fr; }
    .result-score { text-align: left; }
}

@media (max-width: 760px) {
    [data-testid="stSidebar"] { min-width: 16rem; max-width: 16rem; }
    [data-testid="stMainBlockContainer"] { padding: 1.2rem .9rem 2.5rem; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100%; flex-basis: 100%; }
    .page-title { font-size: 1.85rem; }
    .page-subtitle { font-size: .9rem; }
    .hero, .overview-banner { padding: var(--space-5); border-radius: var(--radius-lg); }
    .step-strip { flex-direction: column; align-items: stretch; gap: var(--space-1); }
    .training-step-line { flex: 0 0 12px; width: 1.5px; min-width: 1.5px; height: 12px; margin-left: 11px; }
    .flow { align-items: stretch; }
    .flow-step { flex: 1 1 42%; text-align: center; }
    .flow-arrow { display: none; }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
</style>
"""
