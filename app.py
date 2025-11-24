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
    generate_excel_matches,
    generate_excel_fighters,
    generate_pdf_bout_sheets,
)
from utils.auth import require_auth, logout_user

# Import GSheets connection (optional, for Google Sheets mode)
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None
from utils.auth import require_auth, logout, get_current_user

# Translation dictionaries
translations = {
    "en": {
        "title": "🥊 Muay Thai Matchmaker",
        "tab_data": "📊 Data Upload",
        "tab_generate": "🤝 Generate Pairs",
        "tab_manual": "✏️ Manual Adjustments",
        "tab_export": "📤 Export",
        "header_data": "Data Upload & Validation",
        "upload_help": "Excel file must contain columns: Name, Gender, Age, Weight, Club, Trainer, Record",
        "data_loaded": "Data loaded successfully!",
        "total_fighters": "Total fighters",
        "genders": "Genders",
        "clubs": "Clubs",
        "header_generate": "Generate Automatic Pairings",
        "no_data_warning": "Please upload fighter data first in the Data Upload tab.",
        "weight_tolerance": "Weight Tolerance (kg)",
        "allow_same_trainer": "Allow same trainer matches",
        "generate_button": "Generate Pairings",
        "generating": "Generating pairings...",
        "pairs_generated": "Pairings generated!",
        "header_matches": "Generated Matches",
        "total_matches": "Total Matches",
        "avg_weight_diff": "Avg Weight Diff",
        "unmatched_fighters": "Unmatched Fighters",
        "warning_high_weight": "matches with weight diff > 1kg",
        "warning_high_age": "matches with age diff > 3 years",
        "header_unmatched": "Unmatched Fighters",
        "header_manual": "Manual Adjustments",
        "manual_warning": "Please generate pairings first in the Generate Pairs tab.",
        "manual_edit": "Edit the matches table below. Changes are saved automatically.",
        "matches_updated": "Matches updated!",
        "current_matches": "Current Matches",
        "header_export": "Export Results",
        "export_warning": "No matches to export. Generate pairings first.",
        "event_name": "Event Name",
        "default_event": "Muay Thai Competition",
        "export_excel": "📊 Export to Excel",
        "download_excel": "Download Excel",
        "export_pdf": "📄 Export to PDF",
        "download_pdf": "Download PDF",
        "stats_header": "Competition Statistics",
        "total_fighters_metric": "Total Fighters",
        "matched_fighters": "Matched Fighters",
        "details_header": "Match Details",
        "avg_weight_diff_text": "Average weight difference",
        "avg_age_diff_text": "Average age difference",
        "kg": "kg",
        "years": "years",
        "language": "Language",
        "select_language": "Select Language",
        "gsheets_import": "Google Sheets Import",
        "gsheets_error": "Google Sheets connection not available. Please install streamlit-gsheets-connection.",
        "sheet_loaded": "Sheet data loaded successfully!",
        "raw_preview": "Raw Sheet Data Preview",
        "column_mapping": "Column Mapping",
        "map_columns": "Map sheet columns to required fields:",
        "data_imported": "Data imported and validated successfully!",
        "no_sheet_data": "No data found in the sheet. Please check the URL and sharing settings.",
        "gsheets_conn_error": "Error connecting to Google Sheets",
        "gsheets_help": "Make sure the sheet is publicly accessible or you have proper authentication set up.",
        "db_tournament": "Database Tournament Selection",
        "select_fighters": "Select Present Fighters",
        "staged_fighters": "Staged {count} fighters for pairing!",
        "select_at_least_one": "Please select at least one fighter.",
        "no_fighters_club": "No fighters found for selected clubs.",
        "no_events_db": "No events found in database. Please create events first.",
        "db_error": "Database error",
        "supabase_config": "Make sure Supabase is properly configured.",
        "manage_fighters": "👥 Manage Fighters",
        "add_fighter": "Add New Fighter",
        "required_fields": "Please fill in required fields: Name, Gender, Weight",
        "fighter_added": "Fighter '{name}' added successfully!",
        "error_add_fighter": "Error adding fighter",
        "edit_fighters": "Edit Existing Fighters",
        "edit_details": "Edit fighter details below. Changes are saved automatically.",
        "error_update_fighter": "Error updating fighter {name}",
        "updated_fighters": "Updated {count} fighter(s) successfully!",
        "no_changes": "No changes detected.",
        "deactivate_fighters": "Deactivate Fighters",
        "select_deactivate": "Select fighters to deactivate:",
        "deactivated_fighters": "Deactivated {count} fighter(s)!",
        "no_active_fighters": "No active fighters to deactivate.",
        "no_fighters_db": "No fighters found in database. Add fighters using the 'Add Fighter' tab.",
        "manage_clubs": "Manage Clubs",
        "add_club": "Add New Club",
        "club_added": "Club '{name}' added successfully!",
        "error_add_club": "Error adding club",
        "existing_clubs": "Existing Clubs",
        "no_clubs": "No clubs found. Add your first club above.",
        "db_conn_error": "Database connection error",
        "current_fighter_data": "Current Fighter Data (from uploaded file)",
        "no_fighter_data": "No fighter data available. Upload data in the Data Upload tab first.",
        "save_history": "💾 Save to Database History",
        "create_event": "Create New Event",
        "event_created": "Event '{name}' created and matches saved successfully!",
        "error_create_event": "Error creating event",
        "save_matches_event": "Save Matches to Selected Event",
        "matches_saved": "Matches saved to event '{name}' successfully!",
        "error_save_matches": "Error saving matches",
    },
    "ru": {
        "title": "🥊 Сопоставитель бойцов Муай Тай",
        "tab_data": "📊 Загрузка данных",
        "tab_generate": "🤝 Генерация пар",
        "tab_manual": "✏️ Ручные корректировки",
        "tab_export": "📤 Экспорт",
        "header_data": "Загрузка и валидация данных",
        "upload_help": "Файл Excel должен содержать столбцы: Name, Gender, Age, Weight, Club, Trainer, Record",
        "data_loaded": "Данные загружены успешно!",
        "total_fighters": "Всего бойцов",
        "genders": "Пол",
        "clubs": "Клубы",
        "header_generate": "Генерация автоматических пар",
        "no_data_warning": "Пожалуйста, загрузите данные бойцов сначала на вкладке Загрузка данных.",
        "weight_tolerance": "Допуск по весу (кг)",
        "allow_same_trainer": "Разрешить матчи с одним тренером",
        "generate_button": "Генерировать пары",
        "generating": "Генерация пар...",
        "pairs_generated": "Пары сгенерированы!",
        "header_matches": "Сгенерированные пары",
        "total_matches": "Всего матчей",
        "avg_weight_diff": "Средняя разница веса",
        "unmatched_fighters": "Непарные бойцы",
        "warning_high_weight": "матчей с разницей веса > 1кг",
        "warning_high_age": "матчей с разницей возраста > 3 лет",
        "header_unmatched": "Непарные бойцы",
        "header_manual": "Ручные корректировки",
        "manual_warning": "Пожалуйста, сгенерируйте пары сначала на вкладке Генерация пар.",
        "manual_edit": "Редактируйте таблицу матчей ниже. Изменения сохраняются автоматически.",
        "matches_updated": "Матчи обновлены!",
        "current_matches": "Текущие матчи",
        "header_export": "Экспорт результатов",
        "export_warning": "Нет матчей для экспорта. Сгенерируйте пары сначала.",
        "event_name": "Название события",
        "default_event": "Соревнования по Муай Тай",
        "export_excel": "📊 Экспорт в Excel",
        "download_excel": "Скачать Excel",
        "export_pdf": "📄 Экспорт в PDF",
        "download_pdf": "Скачать PDF",
        "stats_header": "Статистика соревнований",
        "total_fighters_metric": "Всего бойцов",
        "matched_fighters": "Сопоставленные бойцы",
        "details_header": "Детали матчей",
        "avg_weight_diff_text": "Средняя разница веса",
        "avg_age_diff_text": "Средняя разница возраста",
        "kg": "кг",
        "years": "лет",
        "language": "Язык",
        "select_language": "Выберите язык",
        "gsheets_import": "Импорт из Google Sheets",
        "gsheets_error": "Подключение к Google Sheets недоступно. Установите streamlit-gsheets-connection.",
        "sheet_loaded": "Данные из таблицы загружены успешно!",
        "raw_preview": "Предварительный просмотр сырых данных",
        "column_mapping": "Сопоставление столбцов",
        "map_columns": "Сопоставьте столбцы таблицы с требуемыми полями:",
        "data_imported": "Данные импортированы и проверены успешно!",
        "no_sheet_data": "Данные в таблице не найдены. Проверьте URL и настройки доступа.",
        "gsheets_conn_error": "Ошибка подключения к Google Sheets",
        "gsheets_help": "Убедитесь, что таблица общедоступна или настроена аутентификация.",
        "db_tournament": "Выбор турнира из базы данных",
        "select_fighters": "Выберите присутствующих бойцов",
        "staged_fighters": "Подготовлено {count} бойцов для генерации пар!",
        "select_at_least_one": "Пожалуйста, выберите хотя бы одного бойца.",
        "no_fighters_club": "Бойцы для выбранных клубов не найдены.",
        "no_events_db": "События в базе данных не найдены. Создайте события сначала.",
        "db_error": "Ошибка базы данных",
        "supabase_config": "Убедитесь, что Supabase настроен правильно.",
        "manage_fighters": "👥 Управление бойцами",
        "add_fighter": "Добавить нового бойца",
        "required_fields": "Заполните обязательные поля: Имя, Пол, Вес",
        "fighter_added": "Боец '{name}' добавлен успешно!",
        "error_add_fighter": "Ошибка добавления бойца",
        "edit_fighters": "Редактировать бойцов",
        "edit_details": "Редактируйте данные бойцов ниже. Изменения сохраняются автоматически.",
        "error_update_fighter": "Ошибка обновления бойца {name}",
        "updated_fighters": "Обновлено {count} бойцов успешно!",
        "no_changes": "Изменения не обнаружены.",
        "deactivate_fighters": "Деактивировать бойцов",
        "select_deactivate": "Выберите бойцов для деактивации:",
        "deactivated_fighters": "Деактивировано {count} бойцов!",
        "no_active_fighters": "Нет активных бойцов для деактивации.",
        "no_fighters_db": "Бойцы в базе данных не найдены. Добавьте бойцов на вкладке 'Добавить бойца'.",
        "manage_clubs": "Управление клубами",
        "add_club": "Добавить новый клуб",
        "club_added": "Клуб '{name}' добавлен успешно!",
        "error_add_club": "Ошибка добавления клуба",
        "existing_clubs": "Существующие клубы",
        "no_clubs": "Клубы не найдены. Добавьте свой первый клуб выше.",
        "db_conn_error": "Ошибка подключения к базе данных",
        "current_fighter_data": "Текущие данные бойцов (из загруженного файла)",
        "no_fighter_data": "Данные бойцов недоступны. Загрузите данные на вкладке Загрузка данных.",
        "save_history": "💾 Сохранить в историю базы данных",
        "create_event": "Создать новое событие",
        "event_created": "Событие '{name}' создано и матчи сохранены успешно!",
        "error_create_event": "Ошибка создания события",
        "save_matches_event": "Сохранить матчи в выбранное событие",
        "matches_saved": "Матчи сохранены в событие '{name}' успешно!",
        "error_save_matches": "Ошибка сохранения матчей",
    },
}


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
        st.write(f"👤 {user.email}")
        if st.button("Logout"):
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
        "Select Data Source:",
        ["File Upload", "Google Sheets", "Database Tournament"],
        index=0,
        help="Choose how to load fighter data",
    )

    if ingestion_mode == "File Upload":
        # File uploader
        uploaded_file = st.file_uploader(
            t("upload_help"), type=["xlsx"], help=t("upload_help")
        )

        if uploaded_file is not None:
            # Validate and load data
            df, error_msg = validate_excel_file(uploaded_file)

            if error_msg:
                st.error(f"Error loading data: {error_msg}")
            else:
                st.success(t("data_loaded"))

                # Add weight class
                df["Weight Class"] = df["Weight"].apply(get_weight_class)

                # Store in session state
                st.session_state["fighters_df"] = df

                # Display data
                st.subheader(t("header_matches"))  # Reuse for fighter data
                st.dataframe(df)

                st.write(f"{t('total_fighters')}: {len(df)}")
                st.write(f"{t('genders')}: {df['Gender'].value_counts().to_dict()}")
                st.write(f"{t('clubs')}: {df['Club'].nunique()} unique clubs")

    elif ingestion_mode == "Google Sheets":
        st.subheader(t("gsheets_import"))

        if GSheetsConnection is None:
            st.error(t("gsheets_error"))
            return

        # Sheet URL input
        sheet_url = st.text_input(
            "Google Sheets URL",
            placeholder="https://docs.google.com/spreadsheets/d/.../edit",
            help="Paste the full URL of your Google Sheet",
        )

        if sheet_url:
            try:
                # Create connection
                conn = st.connection("gsheets", type=GSheetsConnection)

                # Read sheet data
                df_raw = conn.read(spreadsheet=sheet_url)

                if not df_raw.empty:
                    st.success(t("sheet_loaded"))

                    # Show raw data preview
                    st.subheader(t("raw_preview"))
                    st.dataframe(df_raw.head(10))

                    # Column mapping
                    st.subheader(t("column_mapping"))
                    st.write(t("map_columns"))

                    available_columns = list(df_raw.columns)

                    # Required columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        name_col = st.selectbox(
                            "Name Column",
                            available_columns,
                            index=0
                            if any(
                                "name" in col.lower() or "фамилия" in col.lower()
                                for col in available_columns[:1]
                            )
                            else None,
                        )
                    with col2:
                        gender_col = st.selectbox(
                            "Gender Column",
                            available_columns,
                            index=1 if len(available_columns) > 1 else None,
                        )
                    with col3:
                        weight_col = st.selectbox(
                            "Weight Column",
                            available_columns,
                            index=2 if len(available_columns) > 2 else None,
                        )

                    # Optional columns
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        club_col = st.selectbox(
                            "Club Column (optional)", ["None"] + available_columns
                        )
                    with col5:
                        dob_col = st.selectbox(
                            "DOB Column (optional)", ["None"] + available_columns
                        )
                    with col6:
                        age_col = st.selectbox(
                            "Age Column (optional)", ["None"] + available_columns
                        )

                    col7, col8, col9 = st.columns(3)
                    with col7:
                        trainer_col = st.selectbox(
                            "Trainer Column (optional)", ["None"] + available_columns
                        )
                    with col8:
                        record_col = st.selectbox(
                            "Record Column (optional)", ["None"] + available_columns
                        )
                    with col9:
                        wins_col = st.selectbox(
                            "Wins Column (optional)", ["None"] + available_columns
                        )

                    if st.button("Import & Validate Data"):
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
                            st.error(f"Validation error: {error_msg}")
                        else:
                            # Add weight class
                            df["Weight Class"] = df["Weight"].apply(get_weight_class)

                            # Store in session state
                            st.session_state["fighters_df"] = df

                            st.success(t("data_imported"))
                            st.dataframe(df)

                else:
                    st.warning(t("no_sheet_data"))

            except Exception as e:
                st.error(f"{t('gsheets_conn_error')}: {str(e)}")
                st.info(t("gsheets_help"))

    elif ingestion_mode == "Database Tournament":
        st.subheader(t("db_tournament"))

        try:
            from utils.database import get_events, get_fighters

            # Event selection
            events = get_events()
            if events:
                event_options = {f"{e['name']} ({e['date']})": e["id"] for e in events}
                selected_event_name = st.selectbox(
                    "Select Event", list(event_options.keys())
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
                        "Filter by Clubs", clubs, default=clubs
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

                        if st.button("Send to Staging for Pairing", type="primary"):
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

    if uploaded_file is not None:
        # Validate and load data
        df, error_msg = validate_excel_file(uploaded_file)

        if error_msg:
            st.error(f"Error loading data: {error_msg}")
        else:
            st.success(t("data_loaded"))

            # Add weight class
            df["Weight Class"] = df["Weight"].apply(get_weight_class)

            # Store in session state
            st.session_state["fighters_df"] = df

            # Display data
            st.subheader(t("header_matches"))  # Reuse for fighter data
            st.dataframe(df)

            st.write(f"{t('total_fighters')}: {len(df)}")
            st.write(f"{t('genders')}: {df['Gender'].value_counts().to_dict()}")
            st.write(f"{t('clubs')}: {df['Club'].nunique()} unique clubs")

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
                st.warning(" ⚠️ " + "; ".join(warnings))

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
                    st.warning("No fighter data to export.")

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
                    new_event_name = st.text_input("Event Name")
                    new_event_date = st.date_input("Event Date")
                    new_event_location = st.text_input("Location (optional)")

                    create_submitted = st.form_submit_button(
                        "Create Event & Save Matches"
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

        # Tabs for different management functions
        manage_tab1, manage_tab2, manage_tab3 = st.tabs(
            ["➕ Add Fighter", "📝 Edit Fighters", "🏛️ Manage Clubs"]
        )

        with manage_tab1:
            st.subheader(t("add_fighter"))

            with st.form("add_fighter_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name", key="add_name")
                    gender = st.selectbox("Gender", ["M", "F"], key="add_gender")
                    weight = st.number_input(
                        "Weight (kg)",
                        min_value=40.0,
                        max_value=150.0,
                        value=70.0,
                        key="add_weight",
                    )

                with col2:
                    dob = st.date_input("Date of Birth (optional)", key="add_dob")
                    age = st.number_input(
                        "Age", min_value=16, max_value=100, value=25, key="add_age"
                    )
                    club_options = [""] + [club["name"] for club in get_clubs()]
                    club = st.selectbox("Club", club_options, key="add_club")
                    record = st.number_input(
                        "Record (wins)",
                        min_value=0,
                        max_value=100,
                        value=0,
                        key="add_record",
                    )

                trainer = st.text_input("Trainer (optional)", key="add_trainer")
                wins = st.number_input(
                    "Wins (optional)",
                    min_value=0,
                    max_value=100,
                    value=0,
                    key="add_wins",
                )

                submitted = st.form_submit_button("Add Fighter")

                if submitted:
                    if not name or not gender or not weight:
                        st.error(t("required_fields"))
                    else:
                        fighter_data = {
                            "name": name,
                            "gender": gender,
                            "dob": str(dob) if dob else None,
                            "age": age,
                            "weight": weight,
                            "weight_class": get_weight_class(weight),
                            "club_id": next(
                                (c["id"] for c in get_clubs() if c["name"] == club),
                                None,
                            )
                            if club
                            else None,
                            "trainer": trainer or "",
                            "record_w": record,
                            "record_l": max(0, record - wins),  # Calculate losses
                            "active_status": True,
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
                        "ID": st.column_config.NumberColumn("ID", disabled=True),
                        "Name": st.column_config.TextColumn("Name", required=True),
                        "Gender": st.column_config.SelectboxColumn(
                            "Gender", options=["M", "F"], required=True
                        ),
                        "Age": st.column_config.NumberColumn(
                            "Age", min_value=16, max_value=100, required=True
                        ),
                        "Weight": st.column_config.NumberColumn(
                            "Weight", min_value=40.0, max_value=150.0, required=True
                        ),
                        "Club": st.column_config.TextColumn("Club"),
                        "Trainer": st.column_config.TextColumn("Trainer"),
                        "Record_W": st.column_config.NumberColumn("Wins", min_value=0),
                        "Record_L": st.column_config.NumberColumn(
                            "Losses", min_value=0
                        ),
                        "Active": st.column_config.CheckboxColumn("Active"),
                    },
                )

                if st.button("Save Changes", type="primary"):
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

                    if st.button("Deactivate Selected Fighters", type="secondary"):
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
                                    st.error(f"Error deactivating {name}: {str(e)}")

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
                club_name = st.text_input("Club Name", key="club_name")
                contact_info = st.text_area(
                    "Contact Info (optional)", key="club_contact"
                )

                submitted = st.form_submit_button("Add Club")

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
