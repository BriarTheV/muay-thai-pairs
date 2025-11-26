import streamlit as st
import pandas as pd
from streamlit_elements import elements, dashboard, mui, html
from utils.translations import translations
from utils.pairing import is_valid_pair, Fighter


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def render_manual_edits_tab():
    """Manual adjustments tab using Match_ID method for reliable pair management."""
    st.header(t("header_manual"))

    if st.session_state["matches"].empty and st.session_state["unmatched"].empty:
        st.warning(t("manual_warning"))
        return

    # Single interface using Match_ID method
    render_match_id_editor()


def render_match_id_editor():
    """Main Match_ID based editor for pair adjustments."""
    st.markdown("""
    **Match ID Method**: Edit the `Match_ID` column to assign fighters to pairs.
    - `0` = Unmatched fighter
    - `1`, `2`, `3`... = Pair group numbers
    - Same Match_ID = Same pair
    """)

    # Create combined dataframe with Match_ID column
    combined_df = create_combined_fighters_dataframe()

    if combined_df.empty:
        st.info("No fighters available for editing.")
        return

    # Display editable dataframe
    st.subheader("Fighter Assignments")

    # Add helpful instructions
    with st.expander("📖 How to use Match_ID", expanded=False):
        st.markdown("""
        **Match_ID Column:**
        - `0` = Fighter is unmatched (available for pairing)
        - `1`, `2`, `3`... = Fighter belongs to pair group with that number
        - Fighters with the same Match_ID > 0 are paired together

        **How to pair fighters:**
        1. Find two fighters you want to pair
        2. Change both their Match_ID to the same number (e.g., 1)
        3. The system will automatically create the pair

        **How to unpair fighters:**
        1. Change their Match_ID back to 0
        2. They will become available for new pairings

        **Validation:**
        - Pairs are automatically validated for weight/age compatibility
        - Invalid pairs are highlighted in the summary below
        """)

    edited_df = st.data_editor(
        combined_df,
        num_rows="fixed",
        use_container_width=True,
        key="match_id_editor",
        column_config={
            "Match_ID": st.column_config.NumberColumn(
                "Match ID",
                help="0 = unmatched, 1+ = pair numbers",
                min_value=0,
                step=1,
                width="small",
            ),
            "Name": st.column_config.TextColumn("Name", disabled=True, width="medium"),
            "Gender": st.column_config.TextColumn(
                "Gender", disabled=True, width="small"
            ),
            "Age": st.column_config.TextColumn("Age", disabled=True, width="small"),
            "Weight": st.column_config.TextColumn(
                "Weight", disabled=True, width="small"
            ),
            "Club": st.column_config.TextColumn("Club", disabled=True, width="large"),
            "Status": st.column_config.TextColumn(
                "Status", disabled=True, width="small"
            ),
        },
    )

    # Check for changes and update session state
    if not edited_df.equals(combined_df):
        update_session_state_from_match_id(edited_df)
        st.success("✅ Pair assignments updated!")
        st.rerun()

    # Display summary statistics
    display_pairing_summary()


def create_combined_fighters_dataframe():
    """Create a combined dataframe with all fighters and their Match_ID assignments."""
    matches_df = st.session_state.get("matches", pd.DataFrame())
    unmatched_df = st.session_state.get("unmatched", pd.DataFrame())

    # Start building the combined dataframe
    all_fighters = []

    # Add matched fighters
    for match_idx, match in matches_df.iterrows():
        # Fighter 1
        fighter1 = {
            "Name": match.get("Fighter_1", ""),
            "Gender": match.get("Gender", ""),
            "Age": match.get("Age_1", 0),
            "Weight": match.get("Weight_1", 0),
            "Club": match.get("Club_1", ""),
            "Match_ID": match_idx + 1,  # 1-based indexing for matches
            "Status": "Matched",
        }
        all_fighters.append(fighter1)

        # Fighter 2
        fighter2 = {
            "Name": match.get("Fighter_2", ""),
            "Gender": match.get("Gender", ""),
            "Age": match.get("Age_2", 0),
            "Weight": match.get("Weight_2", 0),
            "Club": match.get("Club_2", ""),
            "Match_ID": match_idx + 1,  # Same Match_ID for pair
            "Status": "Matched",
        }
        all_fighters.append(fighter2)

    # Add unmatched fighters
    for _, fighter in unmatched_df.iterrows():
        fighter_data = {
            "Name": fighter.get("Name", ""),
            "Gender": fighter.get("Gender", ""),
            "Age": fighter.get("Age", 0),
            "Weight": fighter.get("Weight", "").split("-")[0]
            if "-" in str(fighter.get("Weight", ""))
            else fighter.get("Weight", 0),
            "Club": fighter.get("Club", ""),
            "Match_ID": 0,  # 0 = unmatched
            "Status": "Unmatched",
        }
        all_fighters.append(fighter_data)

    return pd.DataFrame(all_fighters)


def update_session_state_from_match_id(edited_df):
    """Update session state based on Match_ID changes."""
    # Group fighters by Match_ID
    match_groups = {}
    unmatched_fighters = []

    for _, fighter in edited_df.iterrows():
        match_id = int(fighter.get("Match_ID", 0))
        name = fighter.get("Name", "")

        if match_id == 0:
            # Unmatched fighter
            unmatched_fighters.append(fighter)
        else:
            # Matched fighter
            if match_id not in match_groups:
                match_groups[match_id] = []
            match_groups[match_id].append(fighter)

    # Rebuild matches dataframe
    new_matches = []
    for match_id, fighters in match_groups.items():
        if len(fighters) >= 2:
            # Create match record for first two fighters
            f1, f2 = fighters[0], fighters[1]

            match_record = {
                "Match_ID": match_id,
                "Fighter_1": f1["Name"],
                "Fighter_2": f2["Name"],
                "Gender": f1["Gender"],
                "Age_1": f1["Age"],
                "Age_2": f2["Age"],
                "Weight_1": f1["Weight"],
                "Weight_2": f2["Weight"],
                "Club_1": f1["Club"],
                "Club_2": f2["Club"],
                "Weight_Diff": abs(f1["Weight"] - f2["Weight"]),
            }
            new_matches.append(match_record)

    # Update session state
    st.session_state["matches"] = pd.DataFrame(new_matches)

    # Rebuild unmatched dataframe
    new_unmatched = []
    for fighter in unmatched_fighters:
        unmatched_record = {
            "Name": fighter["Name"],
            "Gender": fighter["Gender"],
            "Age": fighter["Age"],
            "Weight": f"{fighter['Weight']}-{fighter['Weight']}",  # Simple range
            "Club": fighter["Club"],
            "Record": 0,  # Default
        }
        new_unmatched.append(unmatched_record)

    st.session_state["unmatched"] = pd.DataFrame(new_unmatched)


def display_pairing_summary():
    """Display summary statistics of current pairings."""
    matches_df = st.session_state.get("matches", pd.DataFrame())
    unmatched_df = st.session_state.get("unmatched", pd.DataFrame())

    st.subheader("Pairing Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_fighters = len(matches_df) * 2 + len(unmatched_df)
        st.metric("Total Fighters", total_fighters)

    with col2:
        matched_fighters = len(matches_df) * 2
        st.metric("Matched Fighters", matched_fighters)

    with col3:
        st.metric("Unmatched Fighters", len(unmatched_df))

    with col4:
        total_pairs = len(matches_df)
        st.metric("Total Pairs", total_pairs)

    # Show detailed validation summary
    if not matches_df.empty:
        st.subheader("Pair Validation & Details")

        # Create validation details
        validation_data = []
        valid_pairs = 0
        warning_pairs = 0

        for idx, match in matches_df.iterrows():
            weight_diff = match.get("Weight_Diff", 0)
            age1 = match.get("Age_1", 0)
            age2 = match.get("Age_2", 0)
            age_diff = abs(age1 - age2)

            # Validation logic
            weight_valid = weight_diff <= 3
            age_valid = age_diff <= 3

            if weight_valid and age_valid:
                status = "✅ Valid"
                valid_pairs += 1
            elif weight_diff <= 5 or age_diff <= 5:  # Allow some flexibility
                status = "⚠️ Warning"
                warning_pairs += 1
            else:
                status = "❌ Invalid"
                warning_pairs += 1

            validation_data.append(
                {
                    "Pair": idx + 1,
                    "Fighter 1": match.get("Fighter_1", ""),
                    "Fighter 2": match.get("Fighter_2", ""),
                    "Weight Diff": f"{weight_diff}kg",
                    "Age Diff": f"{age_diff}y",
                    "Status": status,
                }
            )

        # Display validation table
        validation_df = pd.DataFrame(validation_data)
        st.dataframe(
            validation_df,
            use_container_width=True,
            column_config={
                "Pair": st.column_config.NumberColumn("Pair", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Valid Pairs", valid_pairs)
        with col2:
            st.metric("Pairs Needing Attention", warning_pairs)
        with col3:
            pairing_efficiency = (
                (valid_pairs / total_pairs * 100) if total_pairs > 0 else 0
            )
            st.metric("Pairing Efficiency", f"{pairing_efficiency:.1f}%")

        # Show warnings for pairs needing attention
        if warning_pairs > 0:
            st.warning(
                "⚠️ Some pairs may need adjustment. Check weight and age differences."
            )
            with st.expander("View pairs needing attention"):
                attention_pairs = [
                    row
                    for row in validation_data
                    if "⚠️" in row["Status"] or "❌" in row["Status"]
                ]
                if attention_pairs:
                    attention_df = pd.DataFrame(attention_pairs)
                    st.dataframe(attention_df, use_container_width=True)
