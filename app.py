# Muay Thai Matchmaker

import streamlit as st
import pandas as pd
from utils.data_loader import (
    validate_excel_file,
    validate_fighter_dataframe,
    get_weight_class,
)
from utils.pairing import pair_fighters
from utils.pdf_gen import (
    generate_excel_fighters,
    generate_pdf_bout_sheets,
)
from utils.auth import require_auth

# Import GSheets connection (optional, for Google Sheets mode)
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None
from utils.auth import logout, get_current_user
from utils.translations import translations


def find_best_column(available_columns: list, field_type: str) -> int:
    """Find the best matching column index based on field type."""
    keywords_map = {
        "name": ["name", "имя", "фамилия", "спортсмен"],
        "gender": ["gender", "пол", "муж", "жен", "м", "ж"],
        "weight": ["weight", "вес", "категория"],
        "age": ["age", "возраст", "лет"],
        "club": ["club", "клуб", "город"],
        "trainer": ["trainer", "тренер"],
        "record": ["record", "боев", "побед"],
        "class": ["class", "класс", "разряд"],
    }
    keywords = keywords_map.get(field_type, [])
    for i, col in enumerate(available_columns):
        col_str = str(col).lower()
        if any(keyword.lower() in col_str for keyword in keywords):
            return i
    return None  # No match found


# Translation function


def t(key):
    """Translation function"""
    lang = st.session_state.get("language", "ru")
    return translations[lang].get(key, key)


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

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        t("tab_data"),
        t("tab_generate"),
        t("tab_manual"),
        t("tab_export"),
        "👥 Manage Fighters",
    ]
)

with tab1:
    st.header(t("header_data"))

    # Data ingestion mode selection
    ingestion_mode = st.radio(
        t("data_ingestion_mode"),
        [t("file_upload"), t("google_sheets"), t("database_tournament")],
        index=0,
        horizontal=True,
    )

    if ingestion_mode == t("file_upload"):
        # File uploader
        uploaded_file = st.file_uploader(
            t("upload_help"), type=["xlsx", "ods"], help=t("upload_help")
        )

        if uploaded_file is not None:
            # Column order option
            use_standard_order = st.checkbox(
                t("use_standard_column_order"),
                value=False,
                help=t("standard_order_help"),
            )

            column_mapping = None
            if not use_standard_order:
                # Show column mapping UI
                st.subheader(t("column_mapping"))
                st.write(t("map_columns"))

                # Get available columns
                # Detect headers and get available columns
                temp_df = pd.read_excel(uploaded_file, header=None, nrows=1)
                first_row = temp_df.iloc[0].astype(str).str.lower()
                header_keywords = [
                    "name",
                    "имя",
                    "gender",
                    "пол",
                    "вес",
                    "weight",
                    "age",
                    "возраст",
                    "club",
                    "клуб",
                ]

                has_headers = any(
                    any(keyword in cell for keyword in header_keywords)
                    for cell in first_row
                )

                if has_headers:
                    available_columns = [
                        str(col)
                        for col in pd.read_excel(
                            uploaded_file, nrows=0, header=0
                        ).columns
                    ]
                else:
                    # For data files, show actual first row values
                    available_columns = list(temp_df.iloc[0].astype(str))
                if len(available_columns) < 4:
                    st.error(
                        t("error_loading_data")
                        + f": File must have at least 4 columns. Found {len(available_columns)}."
                    )
                else:
                    # Required columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        name_col = st.selectbox(
                            t("name_column"),
                            available_columns,
                            index=find_best_column(available_columns, "name"),
                        )
                    with col2:
                        gender_col = st.selectbox(
                            t("gender_column"),
                            available_columns,
                            index=find_best_column(available_columns, "gender"),
                        )
                    with col3:
                        weight_col = st.selectbox(
                            t("weight_column"),
                            available_columns,
                            index=find_best_column(available_columns, "weight"),
                        )

                    # Optional columns
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        club_col = st.selectbox(
                            t("club_column_optional"), ["None"] + available_columns
                        )
                    with col5:
                        dob_col = st.selectbox(
                            t("dob_column_optional"), ["None"] + available_columns
                        )
                    with col6:
                        age_col = st.selectbox(
                            t("age_column_optional"), ["None"] + available_columns
                        )

                    col7, col8, col9 = st.columns(3)
                    with col7:
                        trainer_col = st.selectbox(
                            t("trainer_column_optional"), ["None"] + available_columns
                        )
                    with col8:
                        record_col = st.selectbox(
                            t("record_column_optional"), ["None"] + available_columns
                        )
                    with col9:
                        wins_col = st.selectbox(
                            t("wins_column_optional"), ["None"] + available_columns
                        )

                    # Create mapping
                    column_mapping = {
                        name_col: "Name",
                        gender_col: "Gender",
                        weight_col: "Weight",
                    }
                    if club_col != "None":
                        column_mapping[club_col] = "Club"
                    if dob_col != "None":
                        column_mapping[dob_col] = "DOB"
                    if age_col != "None":
                        column_mapping[age_col] = "Age"
                    if trainer_col != "None":
                        column_mapping[trainer_col] = "Trainer"
                    if record_col != "None":
                        column_mapping[record_col] = "Record"
                    if wins_col != "None":
                        column_mapping[wins_col] = "Wins"

                    # Validate no duplicate column selections
                    selected_columns = [name_col, gender_col, weight_col]
                    if club_col != "None":
                        selected_columns.append(club_col)
                    if dob_col != "None":
                        selected_columns.append(dob_col)
                    if age_col != "None":
                        selected_columns.append(age_col)
                    if trainer_col != "None":
                        selected_columns.append(trainer_col)
                    if record_col != "None":
                        selected_columns.append(record_col)
                    if wins_col != "None":
                        selected_columns.append(wins_col)

                    if len(set(selected_columns)) < len(selected_columns):
                        st.error(t("duplicate_columns_error"))
                        st.stop()  # Don't proceed with import

            # Validate and load data
            try:
                result = validate_excel_file(uploaded_file, column_mapping)
                if isinstance(result, tuple) and len(result) == 2:
                    df, error_msg = result
                else:
                    df, error_msg = None, "Invalid return from validation function"
            except Exception as e:
                df, error_msg = (
                    None,
                    f"Unexpected error during file validation: {str(e)}",
                )

            if error_msg:
                st.error("{}: {}".format(t("error_loading_data"), error_msg))
            else:
                st.success(t("data_loaded"))

                # Add weight class
                df["Weight Class"] = df["Weight"].apply(get_weight_class)

                # Store in session state
                st.session_state["fighters_df"] = df

                # Display data
                st.subheader(t("header_matches"))  # Reuse for fighter data
                st.dataframe(df)

                st.write("{}: {}".format(t("total_fighters"), len(df)))
                st.write(
                    "{}: {}".format(t("genders"), df["Gender"].value_counts().to_dict())
                )
                st.write("{}: {} unique clubs".format(t("clubs"), df["Club"].nunique()))

    elif ingestion_mode == t("google_sheets"):
        st.subheader(t("gsheets_import"))

        if GSheetsConnection is None:
            st.error(t("gsheets_error"))
            st.info(t("gsheets_install"))
        else:
            # Sheet URL input
            sheet_url = st.text_input(
                t("google_sheets_url"),
                placeholder="https://docs.google.com/spreadsheets/d/.../edit",
                help=t("gsheets_help"),
            )

            if sheet_url:
                df_raw = pd.DataFrame()
                try:
                    # Create connection
                    conn = st.connection("gsheets", type=GSheetsConnection)

                    # Read sheet data
                    df_raw = conn.read(spreadsheet=sheet_url)

                except Exception as e:
                    st.error(f"{t('error_reading_sheet')}: {str(e)}")
                    df_raw = pd.DataFrame()

                if not df_raw.empty:
                    st.success(t("sheet_loaded"))

                    # Show raw data preview
                    st.subheader(t("raw_preview"))
                    st.dataframe(df_raw.head(10))

                    # Column mapping
                    st.subheader(t("column_mapping"))
                    st.write(t("map_columns"))

                    available_columns = [str(col) for col in df_raw.columns]

                    # Required columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        name_col = st.selectbox(
                            t("name_column"),
                            available_columns,
                            index=0
                            if any(
                                "name" in str(col).lower()
                                or "фамилия" in str(col).lower()
                                for col in available_columns[:1]
                            )
                            else None,
                        )
                        with col2:
                            gender_col = st.selectbox(
                                t("gender_column"),
                                available_columns,
                                index=1 if len(available_columns) > 1 else None,
                            )
                        with col3:
                            weight_col = st.selectbox(
                                t("weight_column"),
                                available_columns,
                                index=2 if len(available_columns) > 2 else None,
                            )

                    # Optional columns
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        club_col = st.selectbox(
                            t("club_column_optional"), ["None"] + available_columns
                        )
                    with col5:
                        dob_col = st.selectbox(
                            t("dob_column_optional"), ["None"] + available_columns
                        )
                    with col6:
                        age_col = st.selectbox(
                            t("age_column_optional"), ["None"] + available_columns
                        )

                    col7, col8, col9 = st.columns(3)
                    with col7:
                        trainer_col = st.selectbox(
                            t("trainer_column_optional"), ["None"] + available_columns
                        )
                    with col8:
                        record_col = st.selectbox(
                            t("record_column_optional"), ["None"] + available_columns
                        )
                    with col9:
                        wins_col = st.selectbox(
                            t("wins_column_optional"), ["None"] + available_columns
                        )

                    if st.button(t("import_validate_data")):
                        # Map columns
                        column_mapping = {
                            "Name": name_col,
                            "Gender": gender_col,
                            "Weight": weight_col,
                        }

                        if club_col != "None":
                            column_mapping["Club"] = club_col
                        if dob_col != "None":
                            column_mapping["DOB"] = dob_col
                        if age_col != "None":
                            column_mapping["Age"] = age_col
                        if trainer_col != "None":
                            column_mapping["Trainer"] = trainer_col
                        if record_col != "None":
                            column_mapping["Record"] = record_col
                        if wins_col != "None":
                            column_mapping["Wins"] = wins_col

                        # Create mapped dataframe
                        df = df_raw.rename(
                            columns={v: k for k, v in column_mapping.items()}
                        )

                        # Keep only mapped columns
                        df = df[list(column_mapping.keys())]

                        # Validate and clean
                        df, error_msg = validate_fighter_dataframe(df)

                        if error_msg:
                            st.error("{}: {}".format(t("validation_error"), error_msg))
                        else:
                            # Add weight class
                            df["Weight Class"] = df["Weight"].apply(get_weight_class)

                            # Store in session state
                            st.session_state["fighters_df"] = df

                            st.success(t("data_imported"))
                            st.dataframe(df)

                else:
                    st.warning(t("no_sheet_data"))

                st.info(t("gsheets_help"))

    elif ingestion_mode == t("database_tournament"):
        st.subheader(t("db_tournament"))

        try:
            from utils.database import get_events, get_fighters

            # Event selection
            events = get_events()
            if events:
                event_options = {f"{e['name']} ({e['date']})": e["id"] for e in events}
                selected_event_name = st.selectbox(
                    t("select_event"),
                    list(event_options.keys())
                    if event_options
                    else [t("no_events_db")],
                    key="selected_event",
                )

                if selected_event_name:
                    event_id = event_options[selected_event_name]

                    # Club filter
                    all_fighters = get_fighters()
                    clubs = list(
                        set(
                            f.get("clubs", {}).get("name", "Unknown")
                            for f in all_fighters
                            if f.get("clubs")
                        )
                    )
                    selected_clubs = st.multiselect(
                        t("filter_by_clubs"), clubs, default=clubs
                    )

                    # Get fighters for selected clubs
                    filtered_fighters = [
                        f
                        for f in all_fighters
                        if f.get("clubs", {}).get("name", "Unknown") in selected_clubs
                    ]

                    if filtered_fighters:
                        st.subheader(t("select_fighters"))

                        # Create checkboxes for fighter selection
                        selected_fighter_ids = []
                        for fighter in filtered_fighters:
                            club_name = fighter.get("clubs", {}).get("name", "Unknown")
                            fighter_name = f"{fighter['name']} ({club_name}, {fighter['weight_class']})"

                            if st.checkbox(
                                fighter_name, key=f"fighter_{fighter['id']}"
                            ):
                                selected_fighter_ids.append(fighter["id"])

                        if st.button(t("send_to_staging"), type="primary"):
                            if selected_fighter_ids:
                                # Create dataframe from selected fighters
                                selected_fighters_data = [
                                    f
                                    for f in filtered_fighters
                                    if f["id"] in selected_fighter_ids
                                ]

                                # Convert to dataframe format expected by pairing
                                df_data = []
                                for f in selected_fighters_data:
                                    df_data.append(
                                        {
                                            "Name": f["name"],
                                            "Gender": f["gender"],
                                            "Age": f.get(
                                                "age", 25
                                            ),  # Default if missing
                                            "Weight": f["weight"],
                                            "Club": f.get("clubs", {}).get(
                                                "name", "Unknown"
                                            ),
                                            "Trainer": f.get("trainer", ""),
                                            "Record": f.get("record_w", 0),
                                            "Weight Class": f["weight_class"],
                                        }
                                    )

                                df = pd.DataFrame(df_data)

                                # Store in session state
                                st.session_state["fighters_df"] = df

                                st.success(
                                    t("staged_fighters").format(
                                        count=len(selected_fighter_ids)
                                    )
                                )
                                st.dataframe(df)
                            else:
                                st.warning(t("select_at_least_one"))
                    else:
                        st.warning(t("no_fighters_club"))
            else:
                st.info(t("no_events_db"))

        except Exception as e:
            st.error(f"{t('db_error')}: {str(e)}")
            st.info(t("supabase_config"))


with tab2:
    st.header(t("header_generate"))

    if st.session_state["fighters_df"].empty:
        st.warning(t("no_data_warning"))
    else:
        df = st.session_state["fighters_df"]

        # Configuration
        col1, col2 = st.columns(2)
        with col1:
            weight_tolerance = st.slider(t("weight_tolerance"), 0.0, 2.0, 0.5, 0.1)
        with col2:
            allow_same_trainer = st.checkbox(t("allow_same_trainer"), value=False)

        # Generate pairings button
        if st.button(t("generate_button"), type="primary"):
            with st.spinner(t("generating")):
                matches_df, unmatched_df = pair_fighters(df)

                # Store in session state
                st.session_state["matches"] = matches_df
                st.session_state["unmatched"] = unmatched_df

            st.success(t("pairs_generated"))

        # Display results
        if not st.session_state["matches"].empty:
            matches_df = st.session_state["matches"]
            st.subheader(t("header_matches"))
            st.dataframe(matches_df)

            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(t("total_matches"), len(matches_df))
            with col2:
                avg_weight_diff = matches_df["Weight_Diff"].mean()
                st.metric(t("avg_weight_diff"), f"{avg_weight_diff:.2f} {t('kg')}")
            with col3:
                st.metric(t("unmatched_fighters"), len(st.session_state["unmatched"]))

            # Warnings
            warnings = []
            high_weight_diff = matches_df[matches_df["Weight_Diff"] > 1.0]
            if not high_weight_diff.empty:
                warnings.append(f"{len(high_weight_diff)} {t('warning_high_weight')}")

            high_age_diff = matches_df[matches_df["Age_Diff"] > 3]
            if not high_age_diff.empty:
                warnings.append(f"{len(high_age_diff)} {t('warning_high_age')}")

            if warnings:
                st.warning(" ⚠️ " + t("warnings") + ": " + "; ".join(warnings))

        if not st.session_state["unmatched"].empty:
            st.subheader(t("header_unmatched"))
            st.dataframe(st.session_state["unmatched"])

with tab3:
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

with tab4:
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

with tab5:
    st.header(t("manage_fighters"))

    try:
        from utils.database import (
            get_fighters,
            get_clubs,
            add_fighter,
            update_fighter,
            deactivate_fighter,
            add_club,
        )

        # Get data
        clubs = get_clubs()
        club_options = [""] + [club["name"] for club in clubs]

        # Tabs for different management functions
        manage_tab1, manage_tab2, manage_tab3 = st.tabs(
            [t("manage_add_fighter"), t("manage_edit_fighters"), t("manage_clubs")]
        )

        with manage_tab1:
            st.subheader(t("add_fighter"))

            with st.form("add_fighter_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(t("fighter_name"), key="add_name")
                    gender = st.selectbox(
                        t("fighter_gender"), ["M", "F"], key="add_gender"
                    )
                    weight = st.number_input(
                        t("fighter_weight"),
                        min_value=40.0,
                        max_value=150.0,
                        value=70.0,
                        step=0.1,
                        key="add_weight",
                    )
                    age = st.number_input(
                        t("fighter_age"),
                        min_value=10,
                        max_value=100,
                        value=25,
                        key="add_age",
                    )
                    club = st.selectbox(t("fighter_club"), club_options, key="add_club")
                    record = st.number_input(
                        t("fighter_record"),
                        min_value=0,
                        value=0,
                        key="add_record",
                    )
                trainer = st.text_input(
                    t("fighter_trainer_optional"), key="add_trainer"
                )
                wins = st.number_input(
                    t("fighter_wins"),
                    min_value=0,
                    value=0,
                    key="add_wins",
                )

                with col2:
                    dob = st.date_input(t("dob_optional"), key="add_dob")
                    age = st.number_input(
                        t("fighter_age"),
                        min_value=16,
                        max_value=100,
                        value=25,
                        key="add_age",
                    )
                    club_options = [""] + [club["name"] for club in get_clubs()]
                    club = st.selectbox(t("fighter_club"), club_options, key="add_club")
                    total_fights = st.number_input(
                        "Total Fights",
                        min_value=0,
                        max_value=100,
                        value=0,
                        key="add_record",
                    )

                trainer = st.text_input(t("trainer_optional"), key="add_trainer")
                wins = st.number_input(
                    t("wins_optional"),
                    min_value=0,
                    max_value=100,
                    value=0,
                    key="add_wins",
                )
                fighter_class = st.selectbox(
                    t("fighter_class"),
                    ["", "A", "B", "C"],
                    index=0,
                    key="add_class",
                )

                submitted = st.form_submit_button(t("add_fighter_button"))

                if submitted:
                    if not name or not gender or not weight:
                        st.error(t("required_fields"))
                    else:
                        fighter_data = {
                            "name": name,
                            "gender": gender,
                            "dob": str(dob) if dob else None,
                            "age": age,
                            "weight_min": weight,
                            "weight_max": weight,
                            "weight_class": get_weight_class(weight),
                            "club_id": next(
                                (c["id"] for c in get_clubs() if c["name"] == club),
                                None,
                            )
                            if club
                            else None,
                            "trainer": trainer or "",
                            "record_w": wins,
                            "record_l": total_fights - wins,
                            "class": fighter_class or None,
                        }

                        try:
                            new_fighter = add_fighter(fighter_data)
                            st.success(t("fighter_added").format(name=name))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{t('error_add_fighter')}: {str(e)}")

        with manage_tab2:
            st.subheader(t("edit_fighters"))

            fighters = get_fighters(active_only=False)
            if fighters:
                # Convert to DataFrame for editing
                fighters_df = pd.DataFrame(
                    [
                        {
                            "ID": f["id"],
                            "Name": f["name"],
                            "Gender": f["gender"],
                            "Age": f["age"],
                            "Weight": f["weight"],
                            "Club": f.get("clubs", {}).get("name", ""),
                            "Trainer": f.get("trainer", ""),
                            "Record_W": f.get("record_w", 0),
                            "Record_L": f.get("record_l", 0),
                            "Active": f.get("active_status", True),
                        }
                        for f in fighters
                    ]
                )

                st.write(t("edit_details"))

                edited_df = st.data_editor(
                    fighters_df,
                    num_rows="fixed",
                    use_container_width=True,
                    key="fighters_editor",
                    column_config={
                        "ID": st.column_config.NumberColumn(
                            t("column_id"), disabled=True
                        ),
                        "Name": st.column_config.TextColumn(
                            t("column_name"), required=True
                        ),
                        "Gender": st.column_config.SelectboxColumn(
                            t("column_gender"), options=["M", "F"], required=True
                        ),
                        "Age": st.column_config.NumberColumn(
                            t("column_age"), min_value=10, max_value=100, required=True
                        ),
                        "Weight": st.column_config.NumberColumn(
                            t("column_weight"),
                            min_value=40.0,
                            max_value=150.0,
                            required=True,
                        ),
                        "Club": st.column_config.TextColumn(t("column_club")),
                        "Trainer": st.column_config.TextColumn(t("column_trainer")),
                        "Record_W": st.column_config.NumberColumn(
                            t("column_wins"), min_value=0
                        ),
                        "Record_L": st.column_config.NumberColumn(
                            t("column_losses"), min_value=0
                        ),
                        "Active": st.column_config.CheckboxColumn(t("column_active")),
                    },
                )

                if st.button(t("save_changes"), type="primary"):
                    changes_made = 0
                    for _, row in edited_df.iterrows():
                        fighter_id = int(row["ID"])
                        original = next(
                            (f for f in fighters if f["id"] == fighter_id), None
                        )

                        if original:
                            updates = {}
                            if row["Name"] != original["name"]:
                                updates["name"] = row["Name"]
                            if row["Gender"] != original["gender"]:
                                updates["gender"] = row["Gender"]
                            if row["Age"] != original["age"]:
                                updates["age"] = int(row["Age"])
                            if row["Weight"] != original["weight"]:
                                updates["weight"] = float(row["Weight"])
                                updates["weight_class"] = get_weight_class(
                                    float(row["Weight"])
                                )
                            if row["Trainer"] != original.get("trainer", ""):
                                updates["trainer"] = row["Trainer"]
                            if row["Record_W"] != original.get("record_w", 0):
                                updates["record_w"] = int(row["Record_W"])
                            if row["Record_L"] != original.get("record_l", 0):
                                updates["record_l"] = int(row["Record_L"])
                            if row["Active"] != original.get("active_status", True):
                                updates["active_status"] = bool(row["Active"])

                            if updates:
                                try:
                                    update_fighter(fighter_id, updates)
                                    changes_made += 1
                                except Exception as e:
                                    st.error(
                                        t("error_update_fighter").format(
                                            name=row["Name"]
                                        )
                                        + f": {str(e)}"
                                    )

                    if changes_made > 0:
                        st.success(t("updated_fighters").format(count=changes_made))
                        st.rerun()
                    else:
                        st.info(t("no_changes"))

                # Deactivate fighters section
                st.divider()
                st.subheader(t("deactivate_fighters"))

                active_fighters = [f for f in fighters if f.get("active_status", True)]
                if active_fighters:
                    fighter_names = [f["name"] for f in active_fighters]
                    selected_to_deactivate = st.multiselect(
                        t("select_deactivate"),
                        fighter_names,
                        help="Deactivated fighters won't appear in tournament selections",
                    )

                    if st.button(t("deactivate_selected"), type="secondary"):
                        deactivated_count = 0
                        for name in selected_to_deactivate:
                            fighter = next(
                                (f for f in active_fighters if f["name"] == name), None
                            )
                            if fighter:
                                try:
                                    deactivate_fighter(fighter["id"])
                                    deactivated_count += 1
                                except Exception as e:
                                    st.error(
                                        f"{t('error_deactivating')} {name}: {str(e)}"
                                    )

                        if deactivated_count > 0:
                            st.success(
                                t("deactivated_fighters").format(
                                    count=deactivated_count
                                )
                            )
                            st.rerun()
                else:
                    st.info(t("no_active_fighters"))
            else:
                st.info(t("no_fighters_db"))

        with manage_tab3:
            st.subheader(t("manage_clubs"))

            clubs = get_clubs()

            # Add new club
            with st.form("add_club_form"):
                st.write(t("add_club"))
                club_name = st.text_input(t("club_name"), key="club_name")
                contact_info = st.text_area(
                    t("contact_info_json"),
                    placeholder='{"phone": "+1234567890", "email": "club@example.com"}',
                    key="club_contact",
                )

                submitted = st.form_submit_button(t("add_club_button"))

                if submitted and club_name:
                    try:
                        new_club = add_club(
                            club_name,
                            {"contact": contact_info} if contact_info else None,
                        )
                        st.success(t("club_added").format(name=club_name))
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_add_club')}: {str(e)}")

            # List existing clubs
            if clubs:
                st.subheader(t("existing_clubs"))
                clubs_df = pd.DataFrame(
                    [
                        {
                            "ID": c["id"],
                            "Name": c["name"],
                            "Contact Info": c.get("contact_info", {}),
                        }
                        for c in clubs
                    ]
                )
                st.dataframe(clubs_df)
            else:
                st.info(t("no_clubs"))

    except Exception as e:
        st.error(f"{t('db_conn_error')}: {str(e)}")
        st.info(t("supabase_config"))

        # Fallback: show current session data
        if not st.session_state["fighters_df"].empty:
            st.subheader(t("current_fighter_data"))
            st.dataframe(st.session_state["fighters_df"])
        else:
            st.warning(t("no_fighter_data"))
