import streamlit as st
import pandas as pd
from utils.pairing import pair_fighters, parse_club_hierarchy
from utils.translations import translations


def t(key):
    """Translation function"""
    lang = st.session_state.get("language", "ru")
    return translations[lang].get(key, key)


def translate_weight_class(class_name):
    """Translate weight class names to current language."""
    if not class_name:
        return class_name

    # Create mapping from English names to translation keys
    weight_class_map = {
        "First Flyweight": "first_flyweight",
        "Flyweight": "flyweight",
        "Bantamweight": "bantamweight",
        "Featherweight": "featherweight",
        "Lightweight": "lightweight",
        "Light Welterweight": "light_welterweight",
        "Welterweight": "welterweight",
        "Light Middleweight": "light_middleweight",
        "Middleweight": "middleweight",
        "Light Heavyweight": "light_heavyweight",
        "Cruiserweight": "cruiserweight",
        "Heavyweight": "heavyweight",
        "Super Heavyweight": "super_heavyweight",
    }

    # Get the translation key for this class name
    translation_key = weight_class_map.get(class_name.strip())
    if translation_key:
        return t(translation_key)
    else:
        return class_name  # Fallback to original name


def generate_matches_table(matches_df: pd.DataFrame) -> str:
    """Generate HTML table for matches display with two rows per pair, grouped by weight class."""
    html = """
    <style>
        :root {
            --table-border: #ddd;
            --header-bg: #f8f9fa;
            --weight-header-bg: #e3f2fd;
            --pair-header-bg: #f3e5f5;
            --red-corner-bg: #ffebee;
            --blue-corner-bg: #e3f2fd;
            --text-color: #212529;
            --header-text: #495057;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --table-border: #495057;
                --header-bg: #343a40;
                --weight-header-bg: #1e3a5f;
                --pair-header-bg: #3a1f4a;
                --red-corner-bg: #4a1c1c;
                --blue-corner-bg: #1c3a4a;
                --text-color: #f8f9fa;
                --header-text: #adb5bd;
            }
        }

        .matches-table {
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin-bottom: 20px;
            background-color: var(--header-bg);
            color: var(--text-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .matches-table th, .matches-table td {
            border: 1px solid var(--table-border);
            padding: 12px;
            text-align: left;
            vertical-align: top;
        }

        .matches-table th {
            background-color: var(--header-bg);
            color: var(--header-text);
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .weight-class-header {
            background-color: var(--weight-header-bg) !important;
            font-weight: bold;
            font-size: 1.1em;
            color: var(--text-color);
            padding: 16px;
            border-bottom: 2px solid var(--table-border);
        }

        .pair-header {
            background-color: var(--pair-header-bg);
            font-weight: 600;
            color: var(--text-color);
        }

        .red-corner {
            background-color: var(--red-corner-bg);
            color: var(--text-color);
        }

        .blue-corner {
            background-color: var(--blue-corner-bg);
            color: var(--text-color);
        }

        .matches-table tbody tr:hover {
            background-color: rgba(0,0,0,0.05);
        }

        @media (prefers-color-scheme: dark) {
            .matches-table tbody tr:hover {
                background-color: rgba(255,255,255,0.05);
            }
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

        translated_class_name = translate_weight_class(class_name)
        html += f"<h3>{t('weight_class')}: {translated_class_name}</h3>"
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
        col1, col2, col3 = st.columns(3)
        with col1:
            weight_tolerance = st.slider(t("weight_tolerance"), 0.0, 2.0, 0.5, 0.1)
        with col2:
            allow_same_trainer = st.checkbox(t("allow_same_trainer"), value=False)
        with col3:
            club_conflict_level = st.selectbox(
                t("club_conflict_level"),
                [1, 2, 3, 4],
                index=2,  # Default to level 3 for this tournament
                format_func=lambda x: {
                    1: t("exact_match"),
                    2: t("same_organization"),
                    3: t("same_region"),
                    4: t("no_conflicts"),
                }[x],
                help="Level 1: Exact club name match\nLevel 2: Same region + club (ignore subgroups)\nLevel 3: Same region only\nLevel 4: Allow all pairings",
            )

        # Add subgroup pairing override
        allow_subgroup_pairings = st.checkbox(
            t("allow_subgroup_pairings"),
            value=True,  # Default enabled for this tournament
            help=t("subgroup_pairings_help"),
        )

        # Add sorting strategy selection
        sort_strategy = st.radio(
            t("pairing_priority"),
            ["quality", "quantity"],
            index=1,  # Default to quantity for max pairings
            format_func=lambda x: {
                "quality": t("optimize_quality"),
                "quantity": t("optimize_quantity"),
            }[x],
            help=t("pairing_help_text"),
        )

        # Club parsing preview
        with st.expander(t("club_parsing_expander"), expanded=False):
            st.write(t("club_parsing_preview"))
            unique_clubs = df["Club"].unique()
            club_preview = []
            for club in unique_clubs[:10]:  # Show first 10
                parsed = parse_club_hierarchy(str(club))
                club_preview.append(
                    {
                        "Original": club,
                        "Region": parsed["region"] or "N/A",
                        "Club": parsed["club"] or "N/A",
                        "Subgroup": parsed["subgroup"] or "N/A",
                    }
                )

            if len(unique_clubs) > 10:
                club_preview.append(
                    {
                        "Original": f"... and {len(unique_clubs) - 10} more",
                        "Region": "",
                        "Club": "",
                        "Subgroup": "",
                    }
                )

            st.dataframe(pd.DataFrame(club_preview), use_container_width=True)

        # Generate pairings button
        if st.button(t("generate_button"), type="primary"):
            with st.spinner(t("generating")):
                matches_df, unmatched_df = pair_fighters(
                    df, club_conflict_level, sort_strategy, allow_subgroup_pairings
                )

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
            st.metric(t("total_matches"), len(matches_df))
        with col2:
            avg_weight_diff = (
                matches_df["Weight_Diff"].mean() if not matches_df.empty else 0
            )
            st.metric(t("avg_weight_diff"), f"{avg_weight_diff:.2f} {t('kg')}")
        with col3:
            st.metric(
                t("unmatched"), len(st.session_state.get("unmatched", pd.DataFrame()))
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
