import streamlit as st
import pandas as pd
from utils.pdf_gen import generate_excel_fighters, generate_pdf_bout_sheets
from utils.translations import translations


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def render_export_tab():
    st.header(t("header_export"))

    if st.session_state["matches"].empty:
        st.warning(t("export_warning"))
    else:
        matches_df = st.session_state["matches"]

        # Event name input
        event_name = st.text_input(t("event_name"), value=t("default_event"))

        # Export buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button(t("export_excel")):
                # Export fighter data instead of matches
                fighters_df = st.session_state.get("fighters_df", pd.DataFrame())
                if not fighters_df.empty:
                    excel_data = generate_excel_fighters(fighters_df)
                    st.download_button(
                        label=t("download_excel"),
                        data=excel_data,
                        file_name=f"{event_name.replace(' ', '_')}_fighters.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.warning(t("no_fighter_data_export"))

        with col2:
            if st.button(t("export_pdf")):
                pdf_data = generate_pdf_bout_sheets(matches_df, event_name)
                st.download_button(
                    label=t("download_pdf"),
                    data=pdf_data,
                    file_name=f"{event_name.replace(' ', '_')}_bout_sheets.pdf",
                    mime="application/pdf",
                )

        # Save to Database History
        st.divider()
        st.subheader(t("save_history"))

        try:
            from utils.database import get_events, add_event, save_matches

            # Event selection/creation
            events = get_events()
            event_options = ["Create New Event..."] + [
                f"{e['name']} ({e['date']})" for e in events
            ]

            selected_event_option = st.selectbox(
                "Select Event to Save Matches",
                event_options,
                help="Choose an existing event or create a new one",
            )

            if selected_event_option == "Create New Event...":
                with st.form("create_event_form"):
                    st.write(t("create_event"))
                    new_event_name = st.text_input(t("event_name"))
                    new_event_date = st.date_input(
                        t("event_date")
                    )  # Keep as is, or translate if needed
                    new_event_location = st.text_input(t("location_optional"))

                    create_submitted = st.form_submit_button(
                        t("create_event_save_matches")
                    )

                    if create_submitted and new_event_name and new_event_date:
                        try:
                            new_event = add_event(
                                new_event_name, str(new_event_date), new_event_location
                            )
                            event_id = new_event["id"]

                            # Save matches
                            save_matches(event_id, matches_df)
                            st.success(t("event_created").format(name=new_event_name))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{t('error_create_event')}: {str(e)}")
            else:
                # Existing event selected
                event_name_selected = selected_event_option.split(" (")[0]
                event = next(
                    (e for e in events if e["name"] == event_name_selected), None
                )

                if event and st.button(t("save_matches_event"), type="primary"):
                    try:
                        save_matches(event["id"], matches_df)
                        st.success(t("matches_saved").format(name=event_name_selected))
                    except Exception as e:
                        st.error(f"{t('error_save_matches')}: {str(e)}")

        except Exception as e:
            st.error(f"{t('db_error')}: {str(e)}")
            st.info(t("supabase_config"))

        # Statistics panel
        st.subheader(t("stats_header"))
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(t("total_matches"), len(matches_df))

        with col2:
            total_fighters = len(st.session_state["fighters_df"])
            st.metric(t("total_fighters_metric"), total_fighters)

        with col3:
            matched_fighters = len(matches_df) * 2
            st.metric(t("matched_fighters"), matched_fighters)

        with col4:
            unmatched = len(st.session_state["unmatched"])
            st.metric(t("unmatched_fighters"), unmatched)

        # Detailed stats
        if not matches_df.empty:
            st.subheader(t("details_header"))
            st.write(
                f"{t('avg_weight_diff_text')}: {matches_df['Weight_Diff'].mean():.2f} {t('kg')}"
            )
            st.write(
                f"{t('avg_age_diff_text')}: {matches_df['Age_Diff'].mean():.1f} {t('years')}"
            )

            # Gender distribution
            gender_dist = matches_df["Gender"].value_counts()
            st.bar_chart(gender_dist)

            # Weight class distribution
            wc_dist = matches_df["Weight_Class"].value_counts()
            st.bar_chart(wc_dist)
