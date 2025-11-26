import streamlit as st
import pandas as pd
from streamlit_elements import elements, dashboard, mui, html
from utils.translations import translations
from utils.pairing import is_valid_pair, Fighter


def safe_int_conversion(value) -> int:
    """Safely convert various data types to integer, handling strings, bytes, floats, etc."""
    if pd.isna(value) or value == "" or value is None:
        return 0

    try:
        # Handle bytes objects (decode if needed)
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")

        # Convert to string first to handle all cases
        str_val = str(value).strip()

        # Remove any non-numeric characters except decimal point
        import re

        numeric_str = re.sub(r"[^\d.]", "", str_val)

        # If empty after cleaning, return 0
        if not numeric_str:
            return 0

        # Convert to float first, then int (handles "5.0" -> 5)
        return int(float(numeric_str))

    except (ValueError, TypeError, AttributeError):
        # If conversion fails, return 0
        return 0


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def build_master_fighter_registry():
    """Build and maintain master registry of complete fighter data."""
    registry = {}

    # Add fighters from matches
    matches_df = st.session_state.get("matches", pd.DataFrame())
    for idx, match in matches_df.iterrows():
        # Fighter 1
        fighter1_name = match.get("Fighter_1", "")
        if fighter1_name:
            registry[fighter1_name] = {
                "name": fighter1_name,
                "gender": match.get("Gender", ""),
                "age": match.get("Age_1", 0),
                "weight_min": match.get("Weight_1", 0),
                "weight_max": match.get("Weight_1", 0),  # Assume exact weight
                "club": match.get("Club_1", ""),
                "trainer": "",  # Not stored in matches
                "record": match.get("Red_Record", 0)
                if fighter1_name == match.get("Fighter_1")
                else match.get("Blue_Record", 0),
                "total_fights": match.get("Red_Total_Fights", 0)
                if fighter1_name == match.get("Fighter_1")
                else match.get("Blue_Total_Fights", 0),
                "weight_class": match.get("Weight_Class", ""),
                "current_match_id": idx + 1,  # 1-based
                "status": "matched",
            }

        # Fighter 2
        fighter2_name = match.get("Fighter_2", "")
        if fighter2_name:
            registry[fighter2_name] = {
                "name": fighter2_name,
                "gender": match.get("Gender", ""),
                "age": match.get("Age_2", 0),
                "weight_min": match.get("Weight_2", 0),
                "weight_max": match.get("Weight_2", 0),  # Assume exact weight
                "club": match.get("Club_2", ""),
                "trainer": "",  # Not stored in matches
                "record": match.get("Blue_Record", 0)
                if fighter2_name == match.get("Fighter_2")
                else match.get("Red_Record", 0),
                "total_fights": match.get("Blue_Total_Fights", 0)
                if fighter2_name == match.get("Fighter_2")
                else match.get("Red_Total_Fights", 0),
                "weight_class": match.get("Weight_Class", ""),
                "current_match_id": idx + 1,  # 1-based
                "status": "matched",
            }

    # Add fighters from unmatched
    unmatched_df = st.session_state.get("unmatched", pd.DataFrame())
    for _, fighter in unmatched_df.iterrows():
        name = fighter.get("Name", "")
        if name:
            # Parse weight range for unmatched fighters
            weight_str = str(fighter.get("Weight", ""))
            if "-" in weight_str:
                parts = weight_str.split("-")
                weight_min = safe_int_conversion(parts[0])
                weight_max = (
                    safe_int_conversion(parts[1]) if len(parts) > 1 else weight_min
                )
            elif weight_str.startswith(">="):
                weight_min = safe_int_conversion(weight_str[2:])
                weight_max = weight_min
            else:
                weight_min = safe_int_conversion(weight_str)
                weight_max = weight_min

            registry[name] = {
                "name": name,
                "gender": fighter.get("Gender", ""),
                "age": fighter.get("Age", 0),
                "weight_min": weight_min,
                "weight_max": weight_max,
                "club": fighter.get("Club", ""),
                "trainer": fighter.get("Trainer", ""),
                "record": safe_int_conversion(fighter.get("Record", 0)),
                "total_fights": safe_int_conversion(
                    fighter.get("Record", 0)
                ),  # Fallback
                "weight_class": "",
                "current_match_id": 0,  # unmatched
                "status": "unmatched",
            }

    st.session_state["master_fighter_registry"] = registry


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

    # Ensure master fighter registry is built
    if not st.session_state.get("master_fighter_registry"):
        build_master_fighter_registry()

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
        # Validate groupings first
        invalid_groups = validate_match_id_groups(edited_df)
        if invalid_groups:
            st.error(
                f"❌ Cannot save: Match IDs {invalid_groups} don't have exactly 2 fighters each."
            )
            st.info(
                "💡 **Fix the groupings**: Each Match_ID > 0 must have exactly 2 fighters. Set extra fighters to Match_ID = 0 (unmatched)."
            )
        else:
            # Attempt to update session state
            success = update_session_state_from_match_id(edited_df)
            if success:
                st.success("✅ Pair assignments updated successfully!")
                st.rerun()
            else:
                st.error(
                    "❌ Failed to update pair assignments. Please check the data and try again."
                )

    # Display summary statistics
    display_pairing_summary()


def create_combined_fighters_dataframe():
    """Create a combined dataframe with all fighters and their Match_ID assignments."""
    registry = st.session_state.get("master_fighter_registry", {})

    if not registry:
        # Fallback if registry not built yet
        return pd.DataFrame()

    # Build from master registry
    all_fighters = []

    for fighter_name, fighter_data in registry.items():
        fighter_record = {
            "Name": fighter_data["name"],
            "Gender": fighter_data["gender"],
            "Age": fighter_data["age"],
            "Weight": fighter_data["weight_min"],  # Use min weight for display
            "Club": fighter_data["club"],
            "Match_ID": fighter_data.get("current_match_id", 0),
            "Status": fighter_data.get("status", "unknown").title(),
        }
        all_fighters.append(fighter_record)

    df = pd.DataFrame(all_fighters)

    # Ensure weights are numeric
    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce").fillna(0)

    return df


def validate_match_id_groups(edited_df):
    """Validate that all Match_ID groups have valid sizes (0 or 2 fighters)."""
    groups = edited_df.groupby("Match_ID")
    invalid_groups = []

    for match_id, group in groups:
        if match_id > 0 and len(group) != 2:
            invalid_groups.append(match_id)

    return invalid_groups


def update_session_state_from_match_id(edited_df):
    """Update session state based on Match_ID changes using master registry."""
    # First, validate group sizes
    invalid_groups = validate_match_id_groups(edited_df)
    if invalid_groups:
        st.error(
            f"❌ Invalid groupings detected! Match IDs {invalid_groups} must have exactly 2 fighters each. Please fix the groupings before saving."
        )
        return False  # Don't update session state

    # Use master registry for safe reconstruction
    registry = st.session_state.get("master_fighter_registry", {})

    # Group fighters by Match_ID from the edited dataframe
    match_groups = {}
    unmatched_fighters = []

    for _, fighter in edited_df.iterrows():
        match_id = int(fighter.get("Match_ID", 0))
        name = fighter.get("Name", "")

        if match_id == 0:
            # Unmatched fighter - use original data from registry
            if name in registry:
                unmatched_fighters.append(registry[name])
        else:
            # Matched fighter - use original data from registry
            if name in registry:
                if match_id not in match_groups:
                    match_groups[match_id] = []
                match_groups[match_id].append(registry[name])

    # Rebuild matches dataframe from original data
    new_matches = []
    for match_id, fighters in match_groups.items():
        if len(fighters) == 2:  # Should be validated, but double-check
            f1, f2 = fighters[0], fighters[1]

            match_record = {
                "Match_ID": match_id,
                "Fighter_1": f1["name"],
                "Fighter_2": f2["name"],
                "Gender": f1["gender"],
                "Age_1": f1["age"],
                "Age_2": f2["age"],
                "Weight_1": f1["weight_min"],
                "Weight_2": f2["weight_min"],
                "Club_1": f1["club"],
                "Club_2": f2["club"],
                "Weight_Diff": abs(f1["weight_min"] - f2["weight_min"]),
                "Red_Record": f1["record"],
                "Red_Total_Fights": f1["total_fights"],
                "Blue_Record": f2["record"],
                "Blue_Total_Fights": f2["total_fights"],
            }
            new_matches.append(match_record)

    # Rebuild unmatched dataframe from original data
    new_unmatched = []
    for fighter in unmatched_fighters:
        unmatched_record = {
            "Name": fighter["name"],
            "Gender": fighter["gender"],
            "Age": fighter["age"],
            "Weight": f"{fighter['weight_min']}-{fighter['weight_max']}"
            if fighter["weight_min"] != fighter["weight_max"]
            else f">={fighter['weight_max']}",
            "Club": fighter["club"],
            "Trainer": fighter["trainer"],
            "Record": fighter["record"],
        }
        new_unmatched.append(unmatched_record)

    # Update session state
    st.session_state["matches"] = pd.DataFrame(new_matches)
    st.session_state["unmatched"] = pd.DataFrame(new_unmatched)

    # Update registry with new match IDs
    for match_id, fighters in match_groups.items():
        for fighter in fighters:
            registry[fighter["name"]]["current_match_id"] = match_id
            registry[fighter["name"]]["status"] = "matched"

    for fighter in unmatched_fighters:
        registry[fighter["name"]]["current_match_id"] = 0
        registry[fighter["name"]]["status"] = "unmatched"

    st.session_state["master_fighter_registry"] = registry

    return True

    # Rebuild matches dataframe
    new_matches = []
    for match_id, fighters in match_groups.items():
        if len(fighters) >= 2:
            # Create match record for first two fighters
            f1, f2 = fighters[0], fighters[1]

            # Ensure weights are numeric
            weight1 = pd.to_numeric(f1["Weight"], errors="coerce") or 0
            weight2 = pd.to_numeric(f2["Weight"], errors="coerce") or 0

            match_record = {
                "Match_ID": match_id,
                "Fighter_1": f1["Name"],
                "Fighter_2": f2["Name"],
                "Gender": f1["Gender"],
                "Age_1": f1["Age"],
                "Age_2": f2["Age"],
                "Weight_1": weight1,
                "Weight_2": weight2,
                "Club_1": f1["Club"],
                "Club_2": f2["Club"],
                "Weight_Diff": abs(weight1 - weight2),
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
