# Muay Thai Matchmaker

import streamlit as st
import pandas as pd
from utils.auth import require_auth, logout, get_current_user
from utils.translations import translations
from tabs import (
    render_data_import_tab,
    render_pairing_tab,
    render_manual_edits_tab,
    render_export_tab,
    render_fighter_management_tab,
    render_tournament_bracket_tab,
)


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def apply_global_theme():
    """Inject global theme CSS with CSS variables for light/dark themes."""
    theme_css = """
    <style>
    /* CSS Variables for Theme System */
    :root {
        /* Light Theme Variables */
        --primary-bg: #ffffff;
        --secondary-bg: #f8f9fa;
        --tertiary-bg: #e9ecef;
        --sidebar-bg: #f8f9fa;
        --text-primary: #212529;
        --text-secondary: #6c757d;
        --text-muted: #868e96;
        --border-color: #dee2e6;
        --border-light: #f1f3f4;
        --accent-primary: #007bff;
        --accent-secondary: #6c757d;
        --accent-success: #28a745;
        --accent-danger: #dc3545;
        --accent-warning: #ffc107;
        --accent-info: #17a2b8;
        --shadow-light: rgba(0, 0, 0, 0.1);
        --shadow-medium: rgba(0, 0, 0, 0.15);
        --shadow-strong: rgba(0, 0, 0, 0.2);
        --radius-small: 4px;
        --radius-medium: 8px;
        --radius-large: 12px;
    }

    /* Dark Theme Overrides */
    [data-theme="dark"] {
        --primary-bg: #1a1a1a;
        --secondary-bg: #2d2d2d;
        --tertiary-bg: #404040;
        --sidebar-bg: #2d2d2d;
        --text-primary: #ffffff;
        --text-secondary: #cccccc;
        --text-muted: #999999;
        --border-color: #555555;
        --border-light: #404040;
        --accent-primary: #4dabf7;
        --accent-secondary: #adb5bd;
        --accent-success: #51cf66;
        --accent-danger: #ff6b6b;
        --accent-warning: #ffd43b;
        --accent-info: #74c0fc;
        --shadow-light: rgba(0, 0, 0, 0.3);
        --shadow-medium: rgba(0, 0, 0, 0.4);
        --shadow-strong: rgba(0, 0, 0, 0.5);
    }

    /* Global Theme Application */
    .stApp {
        background-color: var(--primary-bg);
        color: var(--text-primary);
        transition: background-color 0.3s ease, color 0.3s ease;
    }

    .stSidebar {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
        transition: background-color 0.3s ease;
    }

    .stSidebar .stMarkdown, .stSidebar .stText {
        color: var(--text-primary) !important;
    }

    /* Form Elements */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: var(--secondary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-medium) !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25) !important;
    }

    /* Buttons */
    .stButton button {
        background-color: var(--accent-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-medium) !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }

    .stButton button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-medium) !important;
    }

    /* DataFrames and Tables */
    .dataframe {
        background-color: var(--secondary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-medium) !important;
    }

    .dataframe th {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-primary) !important;
        border-bottom: 2px solid var(--border-color) !important;
        font-weight: 600 !important;
    }

    .dataframe td {
        border-bottom: 1px solid var(--border-light) !important;
        color: var(--text-primary) !important;
    }

    .dataframe tbody tr:hover {
        background-color: var(--tertiary-bg) !important;
    }

    /* Headers and Text */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    .stMarkdown p, .stText {
        color: var(--text-primary) !important;
    }

    /* Cards and Containers */
    .stContainer {
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-large) !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-light) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--secondary-bg) !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        background-color: transparent !important;
        border-radius: var(--radius-small) var(--radius-small) 0 0 !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-primary) !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--accent-primary) !important;
        color: white !important;
    }

    /* Progress Bars */
    .stProgress > div > div {
        background-color: var(--accent-primary) !important;
    }

    /* Metrics */
    .stMetric {
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-large) !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-light) !important;
    }

    .stMetric .stMarkdown {
        color: var(--text-primary) !important;
    }

    .stMetric .stMarkdown p {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--secondary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-medium) !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: var(--tertiary-bg) !important;
    }

    /* Smooth transitions for theme changes */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }

    /* Dark theme specific adjustments */
    [data-theme="dark"] .stButton button {
        background-color: var(--accent-primary) !important;
    }

    [data-theme="dark"] .stButton button:hover {
        background-color: #6bb6ff !important;
    }

    /* Ensure proper contrast for accessibility */
    [data-theme="dark"] .stTextInput input::placeholder,
    [data-theme="dark"] .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)


def set_theme(theme):
    """Set the application theme and persist to session state."""
    st.session_state.theme = theme

    # Apply theme to document for CSS variable access
    theme_script = f"""
    <script>
        // Set theme attribute on document
        document.documentElement.setAttribute('data-theme', '{theme}');

        // Persist theme preference
        localStorage.setItem('streamlit-theme', '{theme}');

        // Handle auto theme based on system preference
        if ('{theme}' === 'auto') {{
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        }}

        // Listen for system theme changes when in auto mode
        if ('{theme}' === 'auto') {{
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {{
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
            }});
        }}
    </script>
    """
    st.markdown(theme_script, unsafe_allow_html=True)


def initialize_theme():
    """Initialize theme on app startup."""
    # Load saved theme or default to auto
    saved_theme = st.session_state.get("theme", "auto")
    set_theme(saved_theme)


# Require authentication
require_auth()

# Initialize theme system
initialize_theme()

# Apply global theme CSS
apply_global_theme()

# Language selector and user info in sidebar
with st.sidebar:
    st.header(t("language"))
    lang = st.selectbox(
        t("select_language"),
        ["ru", "en"],
        index=0 if st.session_state.get("language", "ru") == "ru" else 1,
    )
    if lang != st.session_state.get("language", "en"):
        st.session_state["language"] = lang
        st.rerun()

    st.divider()

    # Theme selector
    st.header("🎨 " + t("theme", "Theme"))
    theme_options = {
        "auto": "🔄 " + t("theme_auto", "Auto (System)"),
        "light": "☀️ " + t("theme_light", "Light"),
        "dark": "🌙 " + t("theme_dark", "Dark"),
    }

    current_theme = st.session_state.get("theme", "auto")
    selected_theme = st.selectbox(
        t("select_theme", "Choose Theme"),
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_theme),
        key="theme_selector",
    )

    if selected_theme != current_theme:
        set_theme(selected_theme)
        st.rerun()

    st.divider()

    user = get_current_user()
    if user:
        email = getattr(user, "email", "Unknown")
        st.write("{}: {}".format(t("user_display"), email))
        if st.button(t("logout")):
            logout()

st.title(t("title"))

# Initialize session state
if "fighters_df" not in st.session_state:
    st.session_state["fighters_df"] = pd.DataFrame()
if "matches" not in st.session_state:
    st.session_state["matches"] = pd.DataFrame()
if "unmatched" not in st.session_state:
    st.session_state["unmatched"] = pd.DataFrame()
if "bracket_winners" not in st.session_state:
    st.session_state["bracket_winners"] = {}

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        t("tab_data"),
        t("tab_generate"),
        t("tab_manual"),
        t("tab_export"),
        "👥 Manage Fighters",
        t("tab_bracket"),
    ]
)

with tab1:
    render_data_import_tab()


with tab2:
    render_pairing_tab()

with tab3:
    render_manual_edits_tab()

with tab4:
    render_export_tab()

with tab5:
    render_fighter_management_tab()

with tab6:
    render_tournament_bracket_tab()
