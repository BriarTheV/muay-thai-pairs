import streamlit as st
import pandas as pd
from utils.translations import translations
from utils.type_helpers import safe_int_conversion


def format_weight_string(fighter):
    """Format weight string to match pairing algorithm output."""
    # Ensure we have a dictionary with the expected keys
    if not isinstance(fighter, dict):
        # Handle case where individual weight values are passed
        if isinstance(fighter, (int, float)) and len(locals()) > 1:
            # This shouldn't happen, but handle gracefully
            return f">={fighter}"
        raise TypeError(f"format_weight_string expects a dict, got {type(fighter)}")

    weight_min = fighter.get("weight_min", fighter.get("Weight", 0))
    weight_max = fighter.get("weight_max", weight_min)

    if weight_min <= 0 or weight_min == weight_max:
        return f">={weight_max}"
    else:
        return f"{weight_min}-{weight_max}"


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def build_master_fighter_registry():
    """Build master registry of complete fighter data (optimized O(n) implementation)."""
    registry = {}

    # Add fighters from matches (O(m) where m = number of matches)
    matches_df = st.session_state.get("matches", pd.DataFrame())
    for idx, match in matches_df.iterrows():
        match_id = idx + 1  # 1-based

        # Fighter 1 (Red Corner)
        fighter1_name = match.get("Red_Corner", "")
        if fighter1_name:
            registry[fighter1_name] = {
                "name": fighter1_name,
                "gender": match.get("Gender", ""),
                "age": match.get("Red_Age", 0),
                "weight_min": match.get("Red_Weight", 0),
                "weight_max": match.get("Red_Weight", 0),  # Assume exact weight
                "club": match.get("Red_Club", ""),
                "trainer": "",  # Not stored in matches
                "record": match.get("Red_Record", 0),
                "total_fights": match.get("Red_Total_Fights", 0),
                "weight_class": match.get("Weight_Class", ""),
                "current_match_id": match_id,
                "status": "matched",
            }

        # Fighter 2 (Blue Corner)
        fighter2_name = match.get("Blue_Corner", "")
        if fighter2_name:
            registry[fighter2_name] = {
                "name": fighter2_name,
                "gender": match.get("Gender", ""),
                "age": match.get("Blue_Age", 0),
                "weight_min": match.get("Blue_Weight", 0),
                "weight_max": match.get("Blue_Weight", 0),  # Assume exact weight
                "club": match.get("Blue_Club", ""),
                "trainer": "",  # Not stored in matches
                "record": match.get("Blue_Record", 0),
                "total_fights": match.get("Blue_Total_Fights", 0),
                "weight_class": match.get("Weight_Class", ""),
                "current_match_id": match_id,
                "status": "matched",
            }

    # Add fighters from unmatched (O(u) where u = number of unmatched)
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


def update_fighter_in_registry(fighter_name: str, updates: dict):
    """Incremental update to registry instead of full rebuild (O(1) operation)."""
    registry = st.session_state.get("master_fighter_registry", {})

    if fighter_name not in registry:
        # Fighter not in registry, add them
        registry[fighter_name] = {
            "name": fighter_name,
            "gender": "",
            "age": 0,
            "weight_min": 0,
            "weight_max": 0,
            "club": "",
            "trainer": "",
            "record": 0,
            "total_fights": 0,
            "weight_class": "",
            "current_match_id": 0,
            "status": "unknown",
        }

    # Apply updates
    registry[fighter_name].update(updates)
    st.session_state["master_fighter_registry"] = registry


def validate_fighter_registry() -> list[str]:
    """Check registry for data consistency issues (O(n) validation)."""
    registry = st.session_state.get("master_fighter_registry", {})
    issues = []

    # Check for missing fighters
    matches_df = st.session_state.get("matches", pd.DataFrame())
    unmatched_df = st.session_state.get("unmatched", pd.DataFrame())

    # Collect all expected fighter names
    expected_fighters = set()

    # From matches
    for _, match in matches_df.iterrows():
        expected_fighters.add(match.get("Red_Corner", ""))
        expected_fighters.add(match.get("Blue_Corner", ""))

    # From unmatched
    for _, fighter in unmatched_df.iterrows():
        expected_fighters.add(fighter.get("Name", ""))

    expected_fighters.discard("")  # Remove empty names

    # Check for missing fighters in registry
    registry_fighters = set(registry.keys())
    missing_fighters = expected_fighters - registry_fighters
    if missing_fighters:
        issues.append(f"Missing fighters in registry: {sorted(missing_fighters)}")

    # Check for duplicate match IDs
    match_id_counts = {}
    for fighter_data in registry.values():
        match_id = fighter_data.get("current_match_id", 0)
        if match_id > 0:
            match_id_counts[match_id] = match_id_counts.get(match_id, 0) + 1

    duplicate_match_ids = [mid for mid, count in match_id_counts.items() if count != 2]
    if duplicate_match_ids:
        issues.append(
            f"Invalid match IDs (must have exactly 2 fighters): {duplicate_match_ids}"
        )

    # Check for orphaned records (fighters in registry but not in data)
    orphaned_fighters = registry_fighters - expected_fighters
    if orphaned_fighters:
        issues.append(f"Orphaned fighters in registry: {sorted(orphaned_fighters)}")

    return issues


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

    # Ensure master fighter registry is built and in sync
    registry = st.session_state.get("master_fighter_registry", {})
    if not registry:
        # First time initialization
        build_master_fighter_registry()
    else:
        # Validate registry is in sync with current data
        issues = validate_fighter_registry()
        if issues:
            st.warning("Registry sync issues detected, rebuilding...")
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
            "Weight": format_weight_string(
                fighter_data
            ),  # Consistent weight formatting
            "Club": fighter_data["club"],
            "Match_ID": fighter_data.get("current_match_id", 0),
            "Status": fighter_data.get("status", "unknown").title(),
        }
        all_fighters.append(fighter_record)

    df = pd.DataFrame(all_fighters)

    # Weights are now formatted strings (e.g., ">=60", "55-60"), no numeric conversion needed

    return df


def validate_match_id_groups(edited_df):
    """Validate that all Match_ID groups have valid sizes (0 or 2 fighters)."""
    groups = edited_df.groupby("Match_ID")
    invalid_groups = []

    for match_id, group in groups:
        if match_id > 0 and len(group) != 2:
            invalid_groups.append(match_id)

    return invalid_groups


def validate_before_save(edited_df) -> tuple[bool, list[str]]:
    """Comprehensive pre-save validation with detailed error messages."""
    errors = []

    # Check same-club violations
    registry = st.session_state.get("master_fighter_registry", {})

    # Group by Match_ID to check pairings
    match_groups = {}
    for _, fighter in edited_df.iterrows():
        match_id = int(fighter.get("Match_ID", 0))
        name = fighter.get("Name", "")

        if match_id > 0:
            if match_id not in match_groups:
                match_groups[match_id] = []
            if name in registry:
                match_groups[match_id].append(registry[name])

    # Validate each match group
    for match_id, fighters in match_groups.items():
        if len(fighters) != 2:
            errors.append(
                f"Match ID {match_id}: Must have exactly 2 fighters (found {len(fighters)})"
            )
            continue

        f1, f2 = fighters

        # Gender check
        if f1["gender"] != f2["gender"]:
            errors.append(
                f"Match ID {match_id}: Gender mismatch between {f1['name']} ({f1['gender']}) and {f2['name']} ({f2['gender']})"
            )

        # Age division check
        from utils.pairing import get_age_division

        if get_age_division(f1["age"]) != get_age_division(f2["age"]):
            errors.append(
                f"Match ID {match_id}: Age division mismatch - {f1['name']} ({get_age_division(f1['age'])}) vs {f2['name']} ({get_age_division(f2['age'])})"
            )

        # Weight compatibility check (using dynamic weight-dependent limits)
        from utils.pairing import get_max_diff_12_15, get_max_diff_16_17

        weight_diff = abs(f1["weight_min"] - f2["weight_min"])
        age_group = get_age_division(f1["age"])
        avg_weight = (f1["weight_min"] + f2["weight_min"]) / 2

        if age_group in ["12-13", "14-15"]:
            max_allowed = get_max_diff_12_15(avg_weight)
        elif age_group in ["16-17"]:
            max_allowed = get_max_diff_16_17(avg_weight)
        else:
            # Adult rules - use simplified limit since adult validation is more complex
            max_allowed = 3.0  # kg for adults

        if weight_diff > max_allowed:
            errors.append(
                f"Match ID {match_id}: Weight difference {weight_diff:.1f}kg exceeds limit {max_allowed:.1f}kg for {age_group} age group (avg weight: {avg_weight:.1f}kg)"
            )

        # Club conflict check (level 1 - exact match)
        if f1["club"] and f2["club"] and f1["club"] == f2["club"]:
            errors.append(
                f"Match ID {match_id}: Same club conflict - {f1['name']} and {f2['name']} are both from '{f1['club']}'"
            )

    return (len(errors) == 0, errors)


def update_session_state_from_match_id(edited_df):
    """Transaction-like behavior with rollback on validation failures."""
    # Comprehensive pre-save validation
    is_valid, errors = validate_before_save(edited_df)
    if not is_valid:
        st.error("❌ Cannot save changes due to validation errors:")
        for error in errors:
            st.error(f"  • {error}")
        st.info("💡 **Please fix these issues before saving.**")
        return False

    # Create backup of current state for rollback
    backup_matches = st.session_state.get("matches", pd.DataFrame()).copy()
    backup_unmatched = st.session_state.get("unmatched", pd.DataFrame()).copy()
    backup_registry = st.session_state.get("master_fighter_registry", {}).copy()

    try:
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
                    "Red_Corner": f1["name"],
                    "Blue_Corner": f2["name"],
                    "Gender": f1["gender"],
                    "Red_Age": f1["age"],
                    "Blue_Age": f2["age"],
                    "Red_Weight": format_weight_string(f1),
                    "Blue_Weight": format_weight_string(f2),
                    "Red_Club": f1["club"],
                    "Blue_Club": f2["club"],
                    "Weight_Diff": abs(f1["weight_min"] - f2["weight_min"]),
                    "Age_Diff": abs(f1["age"] - f2["age"]),
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

        # Apply changes to session state
        st.session_state["matches"] = pd.DataFrame(new_matches)
        st.session_state["unmatched"] = pd.DataFrame(new_unmatched)

        # Update registry with new match IDs (incremental updates)
        for match_id, fighters in match_groups.items():
            for fighter in fighters:
                update_fighter_in_registry(
                    fighter["name"], {"current_match_id": match_id, "status": "matched"}
                )

        for fighter in unmatched_fighters:
            update_fighter_in_registry(
                fighter["name"], {"current_match_id": 0, "status": "unmatched"}
            )

        # Final validation of registry integrity
        registry_issues = validate_fighter_registry()
        if registry_issues:
            raise ValueError(f"Registry integrity issues: {registry_issues}")

        return True

    except Exception as e:
        # Rollback on any error
        st.session_state["matches"] = backup_matches
        st.session_state["unmatched"] = backup_unmatched
        st.session_state["master_fighter_registry"] = backup_registry

        st.error(f"❌ Update failed and was rolled back: {str(e)}")
        st.info("💡 **Your previous pairings have been restored.**")
        return False


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
