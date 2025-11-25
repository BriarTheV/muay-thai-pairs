import streamlit as st
import pandas as pd
from utils.pairing import pair_fighters
from utils.translations import translations


def t(key):
    """Translation function"""
    lang = st.session_state.get("language", "ru")
    return translations[lang].get(key, key)


def generate_matches_table(matches_df: pd.DataFrame) -> str:
    """Generate HTML table for matches display with two rows per pair, grouped by weight class."""
    html = """
    <style>
        .matches-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            margin-bottom: 20px;
        }
        .matches-table th, .matches-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .matches-table th {
            background-color: #f2f2f2;
        }
        .weight-class-header {
            background-color: #d4edda;
            font-weight: bold;
            font-size: 1.1em;
        }
        .pair-header {
            background-color: #e8f4f8;
            font-weight: bold;
        }
        .red-corner {
            background-color: #ffe6e6;
        }
        .blue-corner {
            background-color: #e6f0ff;
        }
    </style>
    """

    # Group by weight class
    if "Weight_Class" in matches_df.columns:
        grouped = matches_df.groupby("Weight_Class")
    else:
        grouped = [(t("all_classes"), matches_df)]

    for class_name, class_matches in grouped:
        # Sort by average age
        class_matches = class_matches.copy()
        class_matches["Avg_Age"] = (
            class_matches["Red_Age"] + class_matches["Blue_Age"]
        ) / 2
        class_matches = class_matches.sort_values("Avg_Age")

        html += f"<h3>{t('weight_class')}: {class_name}</h3>"
        html += f"""
        <table class="matches-table">
            <tr>
                <th>{t("pair")}</th>
            <th>{t("fighter")}</th>
            <th>{t("club")}</th>
            <th>{t("weight")}</th>
            <th>{t("age")}</th>
            <th>{t("record")}</th>
            <th>Total Fights</th>
            </tr>
        """

        for idx, match in class_matches.iterrows():
            pair_num = match.get("Match_ID", idx + 1)
            html += f"""
            <tr class="pair-header">
                <td rowspan="2">{pair_num}</td>
                <td class="red-corner">{match["Red_Corner"]}</td>
                <td class="red-corner">{match["Red_Club"]}</td>
                <td class="red-corner">{match["Red_Weight"]}</td>
                <td class="red-corner">{match["Red_Age"]}</td>
                <td class="red-corner">{match["Red_Record"]}</td>
                <td class="red-corner">{match.get("Red_Total_Fights", match["Red_Record"])}</td>
        </tr>
        <tr>
            <td class="blue-corner">{match["Blue_Corner"]}</td>
            <td class="blue-corner">{match["Blue_Club"]}</td>
            <td class="blue-corner">{match["Blue_Weight"]}</td>
            <td class="blue-corner">{match["Blue_Age"]}</td>
            <td class="blue-corner">{match["Blue_Record"]}</td>
                <td class="blue-corner">{match.get("Blue_Total_Fights", match["Blue_Record"])}</td>
            </tr>
            """

        html += "</table>"

    return html


def render_pairing_tab():
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
        matches_df = st.session_state.get("matches", pd.DataFrame())

        if not matches_df.empty:
            st.subheader("✅ " + t("header_matches"))
            matches_html = generate_matches_table(matches_df)
            st.components.v1.html(matches_html, height=400, scrolling=True)

        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Matches", len(matches_df))
        with col2:
            avg_weight_diff = (
                matches_df["Weight_Diff"].mean() if not matches_df.empty else 0
            )
            st.metric(t("avg_weight_diff"), f"{avg_weight_diff:.2f} {t('kg')}")
        with col3:
            st.metric(
                "Unmatched", len(st.session_state.get("unmatched", pd.DataFrame()))
            )

        # Warnings
        if not matches_df.empty:
            warnings = []
            high_weight_diff = matches_df[matches_df["Weight_Diff"] > 1.0]
            if not high_weight_diff.empty:
                warnings.append(f"{len(high_weight_diff)} {t('warning_high_weight')}")

            high_age_diff = matches_df[matches_df["Age_Diff"] > 2]  # Age gap >2 invalid
            if not high_age_diff.empty:
                warnings.append(f"{len(high_age_diff)} {t('warning_high_age')}")

            if warnings:
                st.warning(" ⚠️ " + t("warnings") + ": " + "; ".join(warnings))

        if not st.session_state["unmatched"].empty:
            st.subheader(t("header_unmatched"))
            st.dataframe(st.session_state["unmatched"])
