import streamlit as st
from utils.translations import translations


def t(key):
    """Translation function"""
    lang = st.session_state.get("language", "ru")
    return translations[lang].get(key, key)


def render_manual_edits_tab():
    st.header(t("header_manual"))

    if st.session_state["matches"].empty:
        st.warning(t("manual_warning"))
    else:
        st.write(t("manual_edit"))

        # Editable data editor
        edited_matches = st.data_editor(
            st.session_state["matches"],
            num_rows="dynamic",
            use_container_width=True,
            key="matches_editor",
        )

        # Update session state with edits
        st.session_state["matches"] = edited_matches

        st.success(t("matches_updated"))

        # Display current matches
        st.subheader(t("current_matches"))
        st.dataframe(edited_matches)
