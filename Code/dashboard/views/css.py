CUSTOM_CSS = """
<style>
    /* Global */
    .stApp { 
        background: #F7F8FA; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
    }
    header[data-testid="stHeader"] { background: transparent; height: 0; }
    #MainMenu, footer { visibility: hidden; }
    .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 2rem; 
        max-width: 1400px; 
    }

    /* ============ SIDEBAR ============ */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #ECEEF2;
    }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 0; }

    .pi-logo {
        display: flex; align-items: center; gap: 10px;
        font-size: 20px; font-weight: 700; color: #111827;
        padding: 1.25rem 1rem 1rem 1rem;
        letter-spacing: -0.4px;
    }
    .pi-logo-dot {
        width: 26px; height: 26px; border-radius: 8px;
        background: linear-gradient(135deg, #4338CA, #6366F1);
        display: inline-block;
        flex-shrink: 0;
    }

    /* Hide radio circles completely */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child,
    section[data-testid="stSidebar"] .stRadio input[type="radio"],
    section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] > div > div:first-child {
        display: none !important;
    }

    /* Vertical tabs in sidebar */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
        gap: 2px; display: flex; flex-direction: column;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex; align-items: center;
        padding: 10px 14px 10px 16px;
        border-radius: 8px;
        color: #4B5563;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease;
        border-left: 3px solid transparent;
        margin: 0;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        background: #F3F4F6;
    }
    /* Active tab */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) {
        background: #EEF2FF;
        color: #4338CA;
        border-left: 3px solid #4338CA;
        font-weight: 600;
    }
    /* Material icon in label */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label [data-testid="stIconMaterial"] {
        font-size: 18px;
        margin-right: 10px;
        color: inherit;
    }

    /* ============ CARDS ============ */
    .pi-card {
        background: #FFFFFF;
        border: 1px solid #ECEEF2;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 1px 2px rgba(16,24,40,0.03);
        margin-bottom: 1rem;
    }
    .pi-card-title {
        display: flex; align-items: center; gap: 10px;
        font-size: 15px; font-weight: 600; color: #111827;
        margin-bottom: 14px;
    }
    .pi-kpi-row { display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px; }
    .pi-kpi-label { color: #6B7280; }
    .pi-kpi-value { font-weight: 600; color: #111827; }
    .pi-kpi-value.green { color: #10B981; }
    .pi-kpi-value.red { color: #EF4444; }
    .pi-kpi-value.muted { color: #9CA3AF; }

    .pi-big { font-size: 32px; font-weight: 700; color: #111827; line-height: 1.1; }
    .pi-page-title { font-size: 24px; font-weight: 700; color: #111827; letter-spacing: -0.4px; }
    .pi-sub { font-size: 13px; color: #6B7280; }

    .pi-badge {
        display: inline-block; padding: 4px 10px; border-radius: 999px;
        font-size: 12px; font-weight: 500; background: #F3F4F6;
        color: #4B5563; margin-right: 6px;
    }

    .pi-pipeline-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 14px; border-radius: 999px;
        font-size: 13px; font-weight: 600; background: #FFFFFF;
        border: 1px solid #E5E7EB; color: #374151;
    }
    .pi-pipeline-active {
        background: #EEF2FF; border-color: #C7D2FE; color: #4338CA;
    }

    .pi-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .pi-table th {
        text-align: left; padding: 12px 16px; color: #6B7280;
        font-weight: 500; border-bottom: 1px solid #ECEEF2;
        background: #FAFAFB; font-size: 13px;
    }
    .pi-table td {
        padding: 13px 16px; border-bottom: 1px solid #F3F4F6;
        color: #111827; vertical-align: middle;
    }
    .pi-table tr:last-child td { border-bottom: none; }
    .pi-table tr.highlight td { background: #FFFBEB; }

    .pi-progress { height: 6px; background: #F3F4F6; border-radius: 999px; overflow: hidden; }
    .pi-progress > div { height: 100%; background: linear-gradient(90deg, #4338CA, #6366F1); }

    .pi-sec { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 4px; }
    .pi-sec-sub { font-size: 13px; color: #6B7280; margin-bottom: 14px; }

    /* Streamlit buttons - match design */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background: #FFFFFF;
        color: #374151;
        font-weight: 500;
        font-size: 14px;
        padding: 0.45rem 1rem;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        border-color: #C7D2FE;
        background: #F9FAFB;
    }
    .stButton > button[kind="primary"] {
        background: #4338CA;
        color: #FFFFFF;
        border-color: #4338CA;
    }
    .stButton > button[kind="primary"]:hover {
        background: #3730A3;
        border-color: #3730A3;
    }
    .stDownloadButton > button {
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background: #FFFFFF;
        color: #374151;
        font-weight: 500;
        font-size: 14px;
    }
</style>
"""
