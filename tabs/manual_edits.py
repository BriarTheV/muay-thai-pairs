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
    """Main manual edits tab with two sub-tabs for different adjustment methods."""
    st.header(t("header_manual"))

    if st.session_state["matches"].empty and st.session_state["unmatched"].empty:
        st.warning(t("manual_warning"))
        return

    # Create tabs for different adjustment methods
    tab1, tab2 = st.tabs(
        [
            t("existing_pairs_adjustments", "Adjust Existing Pairs"),
            t("drag_drop_pairing", "Drag & Drop Pairing"),
        ]
    )

    with tab1:
        render_existing_pairs_editor()

    with tab2:
        render_drag_drop_pairing()


def render_existing_pairs_editor():
    """Enhanced data editor for adjusting existing pairs."""
    if st.session_state["matches"].empty:
        st.info(
            "No existing pairs to adjust. Generate pairs first or use drag-and-drop pairing."
        )
        return

    st.write(t("manual_edit"))

    # Editable data editor with validation
    edited_matches = st.data_editor(
        st.session_state["matches"],
        num_rows="dynamic",
        use_container_width=True,
        key="matches_editor",
    )

    # Update session state with edits
    if not edited_matches.equals(st.session_state["matches"]):
        st.session_state["matches"] = edited_matches
        st.success(t("matches_updated"))
        st.rerun()

    # Display current matches
    st.subheader(t("current_matches"))
    st.dataframe(edited_matches, use_container_width=True)


def render_drag_drop_pairing():
    """Visual drag-and-drop interface for pairing unmatched fighters."""
    if st.session_state["unmatched"].empty:
        st.info(
            "No unmatched fighters available. All fighters are already paired or no data has been loaded."
        )
        return

    st.write(t("drag_drop_instructions"))

    # Initialize session state for drag-and-drop
    if "drag_drop_layout" not in st.session_state:
        st.session_state.drag_drop_layout = []
    if "pending_pairs" not in st.session_state:
        st.session_state.pending_pairs = {}
    if "pair_validation" not in st.session_state:
        st.session_state.pair_validation = {}

    # Create the drag-and-drop interface
    with elements("drag_drop_pairing"):
        # Layout definition
        layout = create_drag_drop_layout()

        # Handle layout changes (drag and drop events)
        def handle_layout_change(updated_layout):
            process_layout_change(updated_layout)

        # Render the dashboard
        with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
            # Render unmatched fighters pool
            render_unmatched_pool()

            # Render pairing workspace
            render_pairing_workspace()


def create_drag_drop_layout():
    """Create the dashboard layout for drag-and-drop interface."""
    layout = []

    # Unmatched fighters pool (top section)
    unmatched_count = len(st.session_state["unmatched"])
    pool_items = min(unmatched_count, 20)  # Limit for performance

    for i in range(pool_items):
        layout.append(
            dashboard.Item(f"unmatched_{i}", i % 5, i // 5, 1, 1, isDraggable=True)
        )

    # Pairing workspace (bottom section)
    workspace_start_y = (pool_items // 5) + 2

    # Create drop zones for potential pairs
    for i in range(10):  # 10 potential pairing slots
        layout.append(
            dashboard.Item(
                f"pair_slot_{i}",
                (i % 5) * 2,
                workspace_start_y + (i // 5) * 2,
                2,
                1,
                isDraggable=False,
                isResizable=False,
            )
        )

    return layout


def render_unmatched_pool():
    """Render the pool of unmatched fighters as draggable cards."""
    unmatched_df = st.session_state["unmatched"]

    for idx, (_, fighter) in enumerate(unmatched_df.iterrows()):
        if idx >= 20:  # Performance limit
            break

        fighter_obj = create_fighter_object(fighter)
        card_content = create_fighter_card_content(fighter_obj, idx)

        with mui.Paper(
            card_content,
            key=f"unmatched_{idx}",
            sx={
                "p": 1,
                "cursor": "grab",
                "border": "2px solid #e0e0e0",
                "borderRadius": 2,
                "&:hover": {
                    "borderColor": "#007bff",
                    "boxShadow": "0 2px 8px rgba(0,123,255,0.2)",
                },
            },
        ):
            pass


def render_pairing_workspace():
    """Render the pairing workspace with drop zones."""
    for i in range(10):
        slot_key = f"pair_slot_{i}"

        # Check if this slot has a pending pair
        pending_fighter = st.session_state.pending_pairs.get(slot_key)

        if pending_fighter is not None:
            # Show the fighter in this slot
            card_content = create_fighter_card_content(pending_fighter, f"slot_{i}")
            with mui.Paper(
                card_content,
                key=slot_key,
                sx={
                    "p": 1,
                    "border": "2px solid #28a745",
                    "borderRadius": 2,
                    "backgroundColor": "#f8fff9",
                },
            ):
                pass
        else:
            # Show empty drop zone
            with mui.Paper(
                mui.Typography(
                    t("drop_here"),
                    sx={"textAlign": "center", "color": "#666", "fontStyle": "italic"},
                ),
                key=slot_key,
                sx={
                    "p": 2,
                    "border": "2px dashed #dee2e6",
                    "borderRadius": 2,
                    "backgroundColor": "#f8f9fa",
                    "minHeight": "60px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
            ):
                pass


def create_fighter_object(fighter_row):
    """Create a Fighter object from a dataframe row."""
    # Parse weight range (e.g., "50-55" or ">=55")
    weight_str = fighter_row.get("Weight", "")
    if "-" in weight_str:
        weight_parts = weight_str.split("-")
        weight_min = float(weight_parts[0])
        weight_max = float(weight_parts[1])
    elif weight_str.startswith(">="):
        weight_min = float(weight_str[2:])
        weight_max = weight_min
    else:
        weight_min = 0.0
        weight_max = 0.0

    return Fighter(
        index=fighter_row.name if hasattr(fighter_row, "name") else 0,
        name=fighter_row.get("Name", ""),
        gender=fighter_row.get("Gender", ""),
        age=int(fighter_row.get("Age", 0)),
        weight_min=weight_min,
        weight_max=weight_max,
        club=fighter_row.get("Club", ""),
        trainer=fighter_row.get("Trainer", ""),
        record=int(fighter_row.get("Record", 0)),
        total_fights=int(
            fighter_row.get("Record", 0)
        ),  # Using record as total_fights for now
        weight_class="",  # Will be determined later if needed
    )


def create_fighter_card_content(fighter, card_id):
    """Create the content for a fighter card."""
    gender_color = (
        "#007bff" if fighter.gender.lower() in ["м", "m", "male"] else "#e83e8c"
    )

    return mui.Box(
        mui.Typography(fighter.name, sx={"fontWeight": "bold", "fontSize": "0.9rem"}),
        mui.Typography(
            f"{fighter.age} лет, {fighter.weight_min} кг",
            sx={"fontSize": "0.8rem", "color": "#666"},
        ),
        mui.Typography(fighter.club, sx={"fontSize": "0.7rem", "color": "#888"}),
        sx={
            "backgroundColor": gender_color + "15",  # Light background tint
            "borderLeft": f"4px solid {gender_color}",
            "minWidth": "150px",
        },
    )


def process_layout_change(updated_layout):
    """Process layout changes from drag and drop events."""
    # Find which items have moved
    for item in updated_layout:
        item_id = item["i"]

        # Check if this is an unmatched fighter being moved
        if item_id.startswith("unmatched_"):
            fighter_idx = int(item_id.split("_")[1])
            target_x, target_y = item["x"], item["y"]

            # Determine which slot this was dropped into
            slot_x = target_x // 2  # Each slot is 2 units wide
            slot_y = target_y - 4  # Workspace starts at y=4

            if slot_y >= 0:
                slot_idx = slot_x + (slot_y // 2) * 5
                if 0 <= slot_idx < 10:
                    handle_fighter_drop(fighter_idx, slot_idx)


def handle_fighter_drop(fighter_idx, slot_idx):
    """Handle when a fighter is dropped into a pairing slot."""
    unmatched_df = st.session_state["unmatched"]

    if fighter_idx >= len(unmatched_df):
        return

    fighter_row = unmatched_df.iloc[fighter_idx]
    fighter_obj = create_fighter_object(fighter_row)
    slot_key = f"pair_slot_{slot_idx}"

    # Check if slot already has a fighter
    existing_fighter = st.session_state.pending_pairs.get(slot_key)

    if existing_fighter is None:
        # First fighter in this slot
        st.session_state.pending_pairs[slot_key] = fighter_obj
        st.success(f"{fighter_obj.name} added to pairing slot {slot_idx + 1}")
    else:
        # Second fighter - attempt to create pair
        valid, message = is_valid_pair(existing_fighter, fighter_obj)

        if valid:
            # Create the pair
            create_pair(existing_fighter, fighter_obj, fighter_row)

            # Clear the pending pair
            del st.session_state.pending_pairs[slot_key]

            st.success(
                t("pairing_success") + f" {existing_fighter.name} vs {fighter_obj.name}"
            )
        else:
            # Invalid pair - show error
            error_msg = get_validation_error_message(message)
            st.error(f"{t('pairing_error')} {error_msg}")

            # Keep the first fighter, reject the second
            st.warning(f"Kept {existing_fighter.name}, rejected {fighter_obj.name}")


def create_pair(fighter1, fighter2, fighter2_row):
    """Create a pair and move fighters from unmatched to matches."""
    # Create match record
    match_record = {
        "Fighter_1": fighter1.name,
        "Fighter_2": fighter2.name,
        "Gender": fighter1.gender,
        "Age_1": fighter1.age,
        "Age_2": fighter2.age,
        "Weight_1": fighter1.weight_min,
        "Weight_2": fighter2.weight_min,
        "Club_1": fighter1.club,
        "Club_2": fighter2.club,
        "Weight_Diff": abs(fighter1.weight_min - fighter2.weight_min),
    }

    # Add to matches
    new_match = pd.DataFrame([match_record])
    st.session_state["matches"] = pd.concat(
        [st.session_state["matches"], new_match], ignore_index=True
    )

    # Remove from unmatched (both fighters)
    unmatched_df = st.session_state["unmatched"]

    # Find and remove fighter1
    fighter1_mask = (unmatched_df["Name"] == fighter1.name) & (
        unmatched_df["Club"] == fighter1.club
    )
    unmatched_df = unmatched_df[~fighter1_mask]

    # Find and remove fighter2
    fighter2_mask = (unmatched_df["Name"] == fighter2.name) & (
        unmatched_df["Club"] == fighter2.club
    )
    unmatched_df = unmatched_df[~fighter2_mask]

    st.session_state["unmatched"] = unmatched_df


def get_validation_error_message(validation_message):
    """Convert validation message to user-friendly error message."""
    message_map = {
        "Gender mismatch": t("gender_mismatch"),
        "Different age divisions": t("age_division_mismatch"),
        "Weight diff": t("weight_diff_too_large"),
        "Same trainer": t("club_conflict_warning"),
    }

    for key, translation in message_map.items():
        if key in validation_message:
            return translation

    return validation_message  # Fallback to original message
