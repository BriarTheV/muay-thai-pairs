# Muay Thai Matchmaker

import streamlit as st
import pandas as pd
from utils.data_loader import validate_excel_file, get_weight_class
from utils.pairing import pair_fighters
from utils.pdf_gen import generate_excel_matches, generate_pdf_bout_sheets
from utils.auth import require_auth, logout_user
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
    },
}


def t(key):
    """Translation function"""
    lang = st.session_state.get("language", "en")
    return translations[lang].get(key, key)


# Require authentication
require_auth()

# Language selector and user info in sidebar
with st.sidebar:
    st.header(t("language"))
    lang = st.selectbox(
        t("select_language"),
        ["en", "ru"],
        index=0 if st.session_state.get("language", "en") == "en" else 1,
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
                excel_data = generate_excel_matches(matches_df)
                st.download_button(
                    label=t("download_excel"),
                    data=excel_data,
                    file_name=f"{event_name.replace(' ', '_')}_matches.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        with col2:
            if st.button(t("export_pdf")):
                pdf_data = generate_pdf_bout_sheets(matches_df, event_name)
                st.download_button(
                    label=t("download_pdf"),
                    data=pdf_data,
                    file_name=f"{event_name.replace(' ', '_')}_bout_sheets.pdf",
                    mime="application/pdf",
                )

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
    st.header("👥 Manage Fighters")

    st.info(
        "Database integration coming soon! This tab will allow CRUD operations for fighters and clubs."
    )

    # Placeholder for future database integration
    st.write("**Planned Features:**")
    st.write("- Add/Edit/Delete fighters")
    st.write("- Manage clubs and gyms")
    st.write("- Bulk import/export from database")
    st.write("- Archive inactive fighters")

    # Show current data if available
    if not st.session_state["fighters_df"].empty:
        st.subheader("Current Fighter Data (from uploaded file)")
        st.dataframe(st.session_state["fighters_df"])
    else:
        st.warning(
            "No fighter data available. Upload data in the Data Upload tab first."
        )
