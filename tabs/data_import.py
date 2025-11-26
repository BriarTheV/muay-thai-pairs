import streamlit as st
import pandas as pd
from utils.data_loader import (
    validate_excel_file,
    validate_fighter_dataframe,
    get_weight_class,
)
from utils.translations import translations

# Import GSheets connection (optional, for Google Sheets mode)
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None


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


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def display_club_parsing_report(df: pd.DataFrame):
    """Show how clubs were parsed after upload with validation feedback."""
    from utils.pairing import parse_club_hierarchy

    if "Club" not in df.columns:
        return

    # Parse all unique clubs
    unique_clubs = df["Club"].dropna().unique()
    parsed_clubs = []

    for club in unique_clubs:
        parsed = parse_club_hierarchy(str(club))
        parsed_clubs.append(
            {
                "original": club,
                "region": parsed.get("region", "N/A"),
                "club": parsed.get("club", "N/A"),
                "subgroup": parsed.get("subgroup", "N/A"),
                "confidence": "high"
                if parsed.get("region") and parsed.get("club")
                else "medium"
                if parsed.get("club")
                else "low",
            }
        )

    # Display summary
    st.subheader("🏛️ Club Parsing Report")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Unique Clubs", len(unique_clubs))
    with col2:
        high_conf = sum(1 for p in parsed_clubs if p["confidence"] == "high")
        st.metric("Well Parsed", f"{high_conf}/{len(unique_clubs)}")
    with col3:
        low_conf = sum(1 for p in parsed_clubs if p["confidence"] == "low")
        st.metric("Need Review", low_conf)

    # Show detailed parsing results
    with st.expander("📋 Detailed Club Parsing Results", expanded=False):
        if parsed_clubs:
            # Create summary dataframe
            summary_df = pd.DataFrame(parsed_clubs)
            summary_df = summary_df.sort_values("confidence", ascending=False)

            # Add status indicators
            def get_status_indicator(confidence):
                if confidence == "high":
                    return "✅"
                elif confidence == "medium":
                    return "⚠️"
                else:
                    return "❌"

            summary_df["Status"] = summary_df["confidence"].apply(get_status_indicator)

            st.dataframe(
                summary_df[
                    ["Status", "original", "region", "club", "subgroup", "confidence"]
                ],
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "original": st.column_config.TextColumn(
                        "Original Club", width="large"
                    ),
                    "region": st.column_config.TextColumn("Region", width="medium"),
                    "club": st.column_config.TextColumn("Club Name", width="medium"),
                    "subgroup": st.column_config.TextColumn("Subgroup", width="small"),
                    "confidence": st.column_config.TextColumn(
                        "Confidence", width="small"
                    ),
                },
                use_container_width=True,
            )

            # Show parsing patterns explanation
            st.markdown("""
            **Parsing Confidence Levels:**
            - ✅ **High**: Region and club clearly identified
            - ⚠️ **Medium**: Club identified, region unclear
            - ❌ **Low**: Parsing failed, manual review needed

            **Supported Formats:**
            - `Region / Club (Subgroup)` (e.g., "Тутаев / Пламя (ФК)")
            - `Region / Club` (e.g., "Тутаев / Пламя")
            - `Club (Subgroup)` (e.g., "Пламя (ФК)")
            - `Region - Club` (e.g., "Тутаев - Пламя")
            """)

        else:
            st.info("No club data to analyze.")

    # Show potential conflict warnings
    conflict_warnings = []
    for parsed in parsed_clubs:
        if parsed["confidence"] == "low":
            conflict_warnings.append(
                f"Club '{parsed['original']}' could not be parsed reliably"
            )

    if conflict_warnings:
        st.warning("⚠️ **Potential Issues Detected:**")
        for warning in conflict_warnings[:5]:  # Show first 5
            st.write(f"• {warning}")
        if len(conflict_warnings) > 5:
            st.write(f"• ... and {len(conflict_warnings) - 5} more")


def validate_club_parsing(df: pd.DataFrame) -> dict:
    """Validate club parsing results and return analysis."""
    from utils.pairing import parse_club_hierarchy

    if "Club" not in df.columns:
        return {"valid": True, "parsed_clubs": []}

    unique_clubs = df["Club"].dropna().unique()
    parsed_clubs = []

    for club in unique_clubs:
        parsed = parse_club_hierarchy(str(club))
        confidence = (
            "high"
            if parsed.get("region") and parsed.get("club")
            else "medium"
            if parsed.get("club")
            else "low"
        )
        parsed_clubs.append(
            {"original": club, "parsed": parsed, "confidence": confidence}
        )

    low_confidence_count = sum(1 for p in parsed_clubs if p["confidence"] == "low")

    return {
        "valid": low_confidence_count == 0,
        "parsed_clubs": parsed_clubs,
        "low_confidence_count": low_confidence_count,
    }


def render_data_import_tab():
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
            # Quick import option
            use_quick_import = st.checkbox(
                t("use_standard_column_order"),
                value=True,
                help=t("standard_order_help"),
            )

            column_mapping = None
            if not use_quick_import:
                # Advanced column mapping
                with st.expander(t("column_mapping"), expanded=True):
                    st.write(t("map_columns"))

                    # Get available columns with improved detection
                    temp_df = pd.read_excel(uploaded_file, header=None, nrows=1)
                    first_row = temp_df.iloc[0].astype(str).str.lower()
                    header_keywords = [
                        "name",
                        "имя",
                        "фамилия",
                        "спортсмен",
                        "gender",
                        "пол",
                        "муж",
                        "жен",
                        "м",
                        "ж",
                        "вес",
                        "weight",
                        "категория",
                        "age",
                        "возраст",
                        "лет",
                        "года",
                        "club",
                        "клуб",
                        "город",
                        "команда",
                        "trainer",
                        "тренер",
                        "coach",
                        "record",
                        "боев",
                        "побед",
                        "wins",
                        "class",
                        "класс",
                        "разряд",
                        "уровень",
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
                        available_columns = list(temp_df.iloc[0].astype(str))

                    if len(available_columns) < 4:
                        st.error(
                            t("error_loading_data")
                            + f": File must have at least 4 columns. Found {len(available_columns)}."
                        )
                    else:
                        # Required columns
                        st.subheader(t("required_columns"))
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

                        # Optional columns in expander
                        with st.expander("Optional Columns", expanded=False):
                            col4, col5, col6 = st.columns(3)
                            with col4:
                                club_col = st.selectbox(
                                    t("club_column_optional"),
                                    ["None"] + available_columns,
                                )
                            with col5:
                                age_col = st.selectbox(
                                    t("age_column_optional"),
                                    ["None"] + available_columns,
                                )
                            with col6:
                                trainer_col = st.selectbox(
                                    t("trainer_column_optional"),
                                    ["None"] + available_columns,
                                )

                            col7, col8 = st.columns(2)
                            with col7:
                                record_col = st.selectbox(
                                    t("record_column_optional"),
                                    ["None"] + available_columns,
                                )
                            with col8:
                                wins_col = st.selectbox(
                                    t("wins_column_optional"),
                                    ["None"] + available_columns,
                                )

                        # Create mapping
                        column_mapping = {
                            name_col: "Name",
                            gender_col: "Gender",
                            weight_col: "Weight",
                        }
                        if club_col != "None":
                            column_mapping[club_col] = "Club"
                        if age_col != "None":
                            column_mapping[age_col] = "Age"
                        if trainer_col != "None":
                            column_mapping[trainer_col] = "Trainer"
                        if record_col != "None":
                            column_mapping[record_col] = "Record"
                        if wins_col != "None":
                            column_mapping[wins_col] = "Wins"

                        # Validate no duplicate column selections
                        selected_columns = list(column_mapping.keys())
                        if len(set(selected_columns)) < len(selected_columns):
                            st.error(t("duplicate_columns_error"))
                            st.stop()  # Don't proceed with import

                        # Show mapping preview
                        st.subheader(t("column_mapping_preview"))
                        mapping_df = pd.DataFrame(
                            list(column_mapping.items()),
                            columns=["File Column", "Standard Name"],
                        )
                        st.dataframe(mapping_df, use_container_width=True)

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
                df["Weight Class"] = df["Weight_Min"].apply(get_weight_class)

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

                # Club parsing validation
                display_club_parsing_report(df)

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
                            df["Weight Class"] = df["Weight_Min"].apply(
                                get_weight_class
                            )

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
                                    weight = f["weight"]
                                    df_data.append(
                                        {
                                            "Name": f["name"],
                                            "Gender": f["gender"],
                                            "Age": f.get(
                                                "age", 25
                                            ),  # Default if missing
                                            "Weight": weight,
                                            "Weight_Min": weight,
                                            "Weight_Max": weight,
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
