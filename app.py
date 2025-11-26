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


# Require authentication
require_auth()

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

    # Theme instructions
    st.markdown("**🎨 Theme**")
    st.markdown(
        "Switch between light and dark themes using the ⚙️ **Settings** menu in the top-right corner."
    )
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
if "master_fighter_registry" not in st.session_state:
    st.session_state["master_fighter_registry"] = {}

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
