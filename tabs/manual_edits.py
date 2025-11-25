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
    """Enhanced data editor for adjusting existing pairs with drag-and-drop capabilities."""
    if st.session_state["matches"].empty:
        st.info(
            "No existing pairs to adjust. Generate pairs first or use drag-and-drop pairing."
        )
        return

    st.write(t("manual_edit"))

    # Add option to enable drag-and-drop editing
    enable_drag_drop = st.checkbox(
        "Enable Drag & Drop Pair Editing",
        value=False,
        help="Allow dragging fighters between pairs for quick adjustments",
    )

    if enable_drag_drop:
        # Show drag-and-drop interface for existing pairs
        render_existing_pairs_drag_drop()
    else:
        # Show traditional data editor
        render_traditional_matches_editor()

    # Display current matches summary
    st.subheader(t("current_matches"))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pairs", len(st.session_state["matches"]))
    with col2:
        avg_weight_diff = (
            st.session_state["matches"]["Weight_Diff"].mean()
            if not st.session_state["matches"].empty
            else 0
        )
        st.metric("Avg Weight Diff", ".1f")
    with col3:
        valid_pairs = sum(
            1
            for _, row in st.session_state["matches"].iterrows()
            if row.get("Weight_Diff", 0) <= 3
        )
        st.metric("Valid Pairs", f"{valid_pairs}/{len(st.session_state['matches'])}")


def render_traditional_matches_editor():
    """Traditional data editor for matches."""
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


def render_existing_pairs_drag_drop():
    """Drag-and-drop interface specifically for editing existing pairs."""
    st.write(
        "💡 **Drag & Drop Editing**: Drag fighters between pairs or to the unmatched area to modify pairings."
    )

    # Initialize drag-drop state for existing pairs
    if "existing_pairs_layout" not in st.session_state:
        st.session_state.existing_pairs_layout = []

    with elements("existing_pairs_drag_drop"):
        # Create layout for existing pairs editing
        layout = create_existing_pairs_layout()

        def handle_existing_pairs_change(updated_layout):
            process_existing_pairs_change(updated_layout)

        with dashboard.Grid(layout, onLayoutChange=handle_existing_pairs_change):
            # Render existing pairs as draggable items
            render_existing_pairs_for_editing()

            # Render unmatched drop zone
            render_unmatched_drop_zone()


def create_existing_pairs_layout():
    """Create layout for existing pairs editing interface."""
    layout = []
    matches_df = st.session_state["matches"]

    # Existing pairs (top section)
    for i, (_, match) in enumerate(matches_df.iterrows()):
        if i >= 8:  # Limit for layout
            break
        row = i // 4
        col = (i % 4) * 3
        layout.append(
            dashboard.Item(
                f"edit_pair_{i}", col, row, 3, 2, isDraggable=True, isResizable=False
            )
        )

    # Unmatched drop zone (bottom)
    layout.append(
        dashboard.Item(
            "unmatched_drop_zone", 0, 3, 12, 1, isDraggable=False, isResizable=False
        )
    )

    return layout


def render_existing_pairs_for_editing():
    """Render existing pairs as draggable cards for editing."""
    matches_df = st.session_state["matches"]

    for idx, (_, match) in enumerate(matches_df.iterrows()):
        if idx >= 8:  # Layout limit
            break

        pair_card = create_pair_card(match, idx)

        with mui.Paper(
            pair_card,
            key=f"edit_pair_{idx}",
            sx={
                "cursor": "grab",
                "&:hover": {"boxShadow": "0 4px 12px rgba(0,0,0,0.15)"},
            },
        ):
            pass


def render_unmatched_drop_zone():
    """Render a drop zone for breaking pairs."""
    with mui.Paper(
        mui.Box(
            mui.Typography(
                "🗑️ Drop pairs here to break them",
                sx={"textAlign": "center", "color": "#666", "fontWeight": "500"},
            ),
            mui.Typography(
                "Fighters will be moved back to unmatched pool",
                sx={"textAlign": "center", "color": "#888", "fontSize": "0.8rem"},
            ),
            sx={"p": 2, "textAlign": "center"},
        ),
        key="unmatched_drop_zone",
        sx={
            "border": "2px dashed #dc3545",
            "borderRadius": 2,
            "backgroundColor": "#fff5f5",
            "minHeight": "80px",
        },
    ):
        pass


def process_existing_pairs_change(updated_layout):
    """Process layout changes in existing pairs editing."""
    for item in updated_layout:
        item_id = item["i"]
        new_y = item["y"]

        # Check if pair was dropped in unmatched zone (y >= 3)
        if item_id.startswith("edit_pair_") and new_y >= 3:
            pair_idx = int(item_id.split("_")[2])
            break_pair(pair_idx)
            st.success(
                f"Pair {pair_idx + 1} broken and fighters moved to unmatched pool"
            )
            st.rerun()  # Refresh the interface


def render_drag_drop_pairing():
    """Enhanced visual drag-and-drop interface for pairing and modifying matches."""
    if st.session_state["unmatched"].empty and st.session_state["matches"].empty:
        st.info("No fighters available. Generate pairs first or load fighter data.")
        return

    st.write(t("drag_drop_instructions"))

    # Initialize enhanced session state for drag-and-drop
    initialize_drag_drop_state()

    # Create the enhanced drag-and-drop interface
    with elements("enhanced_drag_drop"):
        # Layout definition with left/right panels
        layout = create_enhanced_layout()

        # Handle layout changes (drag and drop events)
        def handle_layout_change(updated_layout):
            process_enhanced_layout_change(updated_layout)

        # Render the dashboard
        with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
            # Left panel: Unmatched fighters
            render_unmatched_pool_panel()

            # Right panel: Existing pairs grid
            render_existing_pairs_grid()


def initialize_drag_drop_state():
    """Initialize comprehensive session state for drag-and-drop operations."""
    # Core drag-drop state
    if "drag_drop_layout" not in st.session_state:
        st.session_state.drag_drop_layout = []
    if "pending_pairs" not in st.session_state:
        st.session_state.pending_pairs = {}

    # Validation and caching
    if "pair_validation" not in st.session_state:
        st.session_state.pair_validation = {}
    if "fighter_validation_cache" not in st.session_state:
        st.session_state.fighter_validation_cache = {}

    # Pair and fighter tracking
    if "pair_assignments" not in st.session_state:
        st.session_state.pair_assignments = {}
    if "fighter_locations" not in st.session_state:
        st.session_state.fighter_locations = {}  # Track where each fighter is

    # Operation history for undo/redo
    if "drag_operation_history" not in st.session_state:
        st.session_state.drag_operation_history = []
    if "operation_lock" not in st.session_state:
        st.session_state.operation_lock = False  # Prevent concurrent operations

    # Layout persistence
    if "existing_pairs_layout" not in st.session_state:
        st.session_state.existing_pairs_layout = []

    # Update fighter locations tracking
    update_fighter_locations()


def update_fighter_locations():
    """Update the tracking of where each fighter is located."""
    fighter_locations = {}

    # Track fighters in matches
    for idx, match in st.session_state["matches"].iterrows():
        fighter1 = match.get("Fighter_1", "")
        fighter2 = match.get("Fighter_2", "")
        if fighter1:
            fighter_locations[fighter1] = {
                "type": "match",
                "pair_idx": idx,
                "position": 1,
            }
        if fighter2:
            fighter_locations[fighter2] = {
                "type": "match",
                "pair_idx": idx,
                "position": 2,
            }

    # Track fighters in unmatched pool
    for idx, fighter in st.session_state["unmatched"].iterrows():
        name = fighter.get("Name", "")
        if name:
            fighter_locations[name] = {"type": "unmatched", "pool_idx": idx}

    st.session_state.fighter_locations = fighter_locations


def record_operation(operation_type, details):
    """Record an operation in the history for potential undo."""
    if st.session_state.operation_lock:
        return  # Skip if operation is locked

    operation = {
        "type": operation_type,
        "timestamp": pd.Timestamp.now(),
        "details": details,
    }

    st.session_state.drag_operation_history.append(operation)

    # Limit history size
    if len(st.session_state.drag_operation_history) > 50:
        st.session_state.drag_operation_history = (
            st.session_state.drag_operation_history[-50:]
        )


def lock_operations():
    """Lock operations to prevent concurrent modifications."""
    st.session_state.operation_lock = True


def unlock_operations():
    """Unlock operations after completion."""
    st.session_state.operation_lock = False


def create_enhanced_layout():
    """Create the enhanced dashboard layout with left/right panels."""
    layout = []

    # Left panel: Unmatched fighters (x=0-3, vertical stack)
    unmatched_count = len(st.session_state["unmatched"])
    pool_items = min(unmatched_count, 20)  # Performance limit

    for i in range(pool_items):
        layout.append(
            dashboard.Item(
                f"unmatched_{i}", 0, i, 4, 1, isDraggable=True, isResizable=False
            )
        )

    # Right panel: Existing pairs grid (x=5-11, 2x2 grid per pair)
    matches_df = st.session_state["matches"]
    pairs_count = len(matches_df)

    for i in range(min(pairs_count, 12)):  # Max 12 pairs in 3x4 grid
        row = i // 3
        col = (i % 3) * 3 + 5  # Start at x=5, 3 units per pair
        layout.append(
            dashboard.Item(
                f"pair_{i}", col, row * 2, 3, 2, isDraggable=True, isResizable=False
            )
        )

    # Add empty pair slots for creating new pairs
    empty_slots_start = pairs_count
    for i in range(max(0, 12 - pairs_count)):  # Fill remaining slots
        slot_idx = empty_slots_start + i
        row = slot_idx // 3
        col = (slot_idx % 3) * 3 + 5
        layout.append(
            dashboard.Item(
                f"empty_pair_{i}",
                col,
                row * 2,
                3,
                2,
                isDraggable=False,
                isResizable=False,
            )
        )

    return layout


def render_unmatched_pool_panel():
    """Render the left panel with unmatched fighters in compact cards."""
    unmatched_df = st.session_state["unmatched"]

    if unmatched_df.empty:
        # Show empty state
        with mui.Paper(
            mui.Box(
                mui.Typography(
                    t("unmatched_pool", "Unmatched Fighters Pool"),
                    sx={"fontWeight": "bold", "mb": 1},
                ),
                mui.Typography(
                    "No unmatched fighters",
                    sx={"color": "#666", "fontStyle": "italic", "textAlign": "center"},
                ),
                sx={"p": 2, "textAlign": "center"},
            ),
            key="unmatched_pool_header",
            sx={"gridColumn": "1 / 5", "gridRow": "1", "mb": 1},
        ):
            pass
        return

    # Header for unmatched pool
    with mui.Paper(
        mui.Typography(
            f"{t('unmatched_pool', 'Unmatched Fighters Pool')} ({len(unmatched_df)})",
            sx={"fontWeight": "bold"},
        ),
        key="unmatched_pool_header",
        sx={"gridColumn": "1 / 5", "gridRow": "1", "p": 1, "mb": 1},
    ):
        pass

    # Render unmatched fighters as compact cards
    for idx, (_, fighter) in enumerate(unmatched_df.iterrows()):
        if idx >= 20:  # Performance limit
            break

        fighter_obj = create_fighter_object(fighter)
        compact_card = create_compact_fighter_card(fighter_obj, idx)

        with mui.Paper(
            compact_card,
            key=f"unmatched_{idx}",
            sx={
                "p": 1,
                "cursor": "grab",
                "border": "2px solid #e0e0e0",
                "borderRadius": 2,
                "backgroundColor": "#f8f9fa",
                "&:hover": {
                    "borderColor": "#007bff",
                    "boxShadow": "0 2px 8px rgba(0,123,255,0.2)",
                    "backgroundColor": "#fff",
                },
            },
        ):
            pass


def render_existing_pairs_grid():
    """Render the right panel with existing pairs in a visual grid."""
    matches_df = st.session_state["matches"]

    # Header for pairs grid
    with mui.Paper(
        mui.Typography(
            f"{t('existing_pairs_grid', 'Existing Pairs')} ({len(matches_df)})",
            sx={"fontWeight": "bold"},
        ),
        key="pairs_grid_header",
        sx={"gridColumn": "5 / 12", "gridRow": "1", "p": 1, "mb": 1},
    ):
        pass

    # Render existing pairs
    for idx, (_, match) in enumerate(matches_df.iterrows()):
        if idx >= 12:  # Layout limit
            break

        pair_card = create_pair_card(match, idx)

        with mui.Paper(
            pair_card,
            key=f"pair_{idx}",
            sx={
                "p": 1,
                "border": "2px solid #28a745",
                "borderRadius": 2,
                "cursor": "grab",
                "&:hover": {
                    "borderColor": "#007bff",
                    "boxShadow": "0 2px 8px rgba(0,123,255,0.2)",
                },
            },
        ):
            pass

    # Render empty pair slots
    empty_slots = max(0, 12 - len(matches_df))
    for i in range(empty_slots):
        slot_idx = len(matches_df) + i

        with mui.Paper(
            mui.Box(
                mui.Typography(
                    t("drop_here", "Drop fighter here"),
                    sx={"textAlign": "center", "color": "#666", "fontStyle": "italic"},
                ),
                sx={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "minHeight": "80px",
                },
            ),
            key=f"empty_pair_{i}",
            sx={
                "p": 1,
                "border": "2px dashed #dee2e6",
                "borderRadius": 2,
                "backgroundColor": "#f8f9fa",
                "minHeight": "100px",
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


def create_compact_fighter_card(fighter_obj, card_id):
    """Create a compact fighter card for the unmatched pool."""
    gender_color = (
        "#007bff" if fighter_obj.gender.lower() in ["м", "m", "male"] else "#e83e8c"
    )

    # Format weight range
    if fighter_obj.weight_min == fighter_obj.weight_max:
        weight_display = f"{fighter_obj.weight_min}kg"
    else:
        weight_display = f"{fighter_obj.weight_min}-{fighter_obj.weight_max}kg"

    return mui.Box(
        # Header with name and drag indicator
        mui.Box(
            mui.Typography(
                "⋮⋮",  # Drag handle indicator
                sx={"fontSize": "0.7rem", "color": "#ccc", "mr": 0.5},
            ),
            mui.Typography(
                fighter_obj.name,
                sx={"fontWeight": "bold", "fontSize": "0.85rem", "flex": 1},
            ),
            sx={"display": "flex", "alignItems": "center", "mb": 0.25},
        ),
        # Details row
        mui.Box(
            mui.Typography(
                f"{fighter_obj.age}y",
                sx={"fontSize": "0.75rem", "color": "#666", "mr": 1},
            ),
            mui.Typography(
                weight_display,
                sx={"fontSize": "0.75rem", "color": "#666", "fontWeight": "500"},
            ),
            sx={"display": "flex", "mb": 0.25},
        ),
        # Club (truncated)
        mui.Typography(
            fighter_obj.club[:18] + "..."
            if len(fighter_obj.club) > 18
            else fighter_obj.club,
            sx={"fontSize": "0.65rem", "color": "#888", "lineHeight": 1.2},
        ),
        sx={
            "backgroundColor": gender_color + "08",  # Very light background
            "borderLeft": f"3px solid {gender_color}",
            "borderRadius": "4px",
            "padding": "8px",
            "minHeight": "70px",
            "cursor": "grab",
            "transition": "all 0.2s ease",
            "&:hover": {
                "backgroundColor": gender_color + "12",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
        },
    )

    return mui.Box(
        mui.Typography(
            fighter_obj.name,
            sx={"fontWeight": "bold", "fontSize": "0.85rem", "mb": 0.5},
        ),
        mui.Typography(
            f"{fighter_obj.age}y, {fighter_obj.weight_min}-{fighter_obj.weight_max}kg",
            sx={"fontSize": "0.75rem", "color": "#666"},
        ),
        mui.Typography(
            fighter_obj.club[:15] + "..."
            if len(fighter_obj.club) > 15
            else fighter_obj.club,
            sx={"fontSize": "0.7rem", "color": "#888"},
        ),
        sx={
            "backgroundColor": gender_color + "10",
            "borderLeft": f"3px solid {gender_color}",
            "minHeight": "60px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
        },
    )


def create_pair_card(match_row, pair_idx):
    """Create a visual card showing a pair of fighters."""
    fighter1_name = match_row.get("Fighter_1", "")
    fighter2_name = match_row.get("Fighter_2", "")
    weight1 = match_row.get("Weight_1", 0)
    weight2 = match_row.get("Weight_2", 0)
    weight_diff = abs(weight1 - weight2)

    # Enhanced validation - check multiple criteria
    age1 = match_row.get("Age_1", 0)
    age2 = match_row.get("Age_2", 0)
    gender = match_row.get("Gender", "")

    # Basic validation checks
    weight_valid = weight_diff <= 3
    age_diff = abs(age1 - age2)
    age_valid = age_diff <= 3  # Max 3 year age difference

    is_valid = weight_valid and age_valid

    status_color = "#28a745" if is_valid else "#dc3545"
    status_icon = "✓" if is_valid else "✗"

    # Determine gender color
    gender_color = "#007bff" if gender.lower() in ["м", "m", "male"] else "#e83e8c"

    return mui.Box(
        # Header with pair number and status
        mui.Box(
            mui.Typography(
                f"Pair {pair_idx + 1}", sx={"fontWeight": "bold", "fontSize": "0.8rem"}
            ),
            mui.Typography(
                status_icon,
                sx={
                    "fontSize": "1rem",
                    "color": status_color,
                    "fontWeight": "bold",
                    "ml": "auto",
                },
            ),
            sx={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "mb": 0.5,
            },
        ),
        # Fighters display
        mui.Box(
            # Fighter 1
            mui.Box(
                mui.Typography(
                    fighter1_name[:12] + "..."
                    if len(fighter1_name) > 12
                    else fighter1_name,
                    sx={"fontSize": "0.7rem", "fontWeight": "500", "mb": 0.25},
                ),
                mui.Typography(
                    f"{age1}y • {weight1}kg",
                    sx={"fontSize": "0.65rem", "color": "#666"},
                ),
                sx={
                    "flex": 1,
                    "p": 0.5,
                    "bgcolor": gender_color + "08",
                    "borderRadius": 1,
                    "border": f"1px solid {gender_color}20",
                },
            ),
            # Fighter 2
            mui.Box(
                mui.Typography(
                    fighter2_name[:12] + "..."
                    if len(fighter2_name) > 12
                    else fighter2_name,
                    sx={"fontSize": "0.7rem", "fontWeight": "500", "mb": 0.25},
                ),
                mui.Typography(
                    f"{age2}y • {weight2}kg",
                    sx={"fontSize": "0.65rem", "color": "#666"},
                ),
                sx={
                    "flex": 1,
                    "p": 0.5,
                    "bgcolor": gender_color + "08",
                    "borderRadius": 1,
                    "border": f"1px solid {gender_color}20",
                },
            ),
            sx={"display": "flex", "gap": 0.5, "mb": 0.5},
        ),
        # Stats footer
        mui.Box(
            mui.Typography(
                f"Δ{weight_diff}kg", sx={"fontSize": "0.65rem", "color": "#666"}
            ),
            mui.Typography(
                f"Age diff: {age_diff}y",
                sx={"fontSize": "0.65rem", "color": "#666", "ml": "auto"},
            ),
            sx={"display": "flex", "justifyContent": "space-between"},
        ),
        sx={
            "minHeight": "110px",
            "padding": "8px",
            "borderRadius": "6px",
            "border": f"2px solid {status_color}40",
            "backgroundColor": "#ffffff",
            "cursor": "grab",
            "transition": "all 0.2s ease",
            "&:hover": {
                "borderColor": status_color,
                "boxShadow": f"0 2px 8px {status_color}20",
            },
        },
    )


def create_fighter_card_content(fighter, card_id):
    """Create the content for a fighter card (legacy function for compatibility)."""
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


def process_enhanced_layout_change(updated_layout):
    """Process enhanced layout changes supporting pair modifications with state management."""
    if st.session_state.operation_lock:
        return  # Skip if operations are locked

    lock_operations()

    try:
        # Track which items have moved and their sources
        moved_items = {}

        for item in updated_layout:
            item_id = item["i"]
            new_x, new_y = item["x"], item["y"]

            # Determine item type and handle accordingly
            if item_id.startswith("unmatched_"):
                # Unmatched fighter being moved
                fighter_idx = int(item_id.split("_")[1])
                handle_unmatched_fighter_drop(fighter_idx, new_x, new_y)

            elif item_id.startswith("pair_"):
                # Existing pair being moved or modified
                pair_idx = int(item_id.split("_")[1])
                handle_pair_drop(pair_idx, new_x, new_y)

            # Store for potential undo functionality
            moved_items[item_id] = {"x": new_x, "y": new_y}

        # Update fighter locations after all operations
        update_fighter_locations()

    finally:
        unlock_operations()


def handle_unmatched_fighter_drop(fighter_idx, target_x, target_y):
    """Handle dropping an unmatched fighter onto the pairs grid."""
    unmatched_df = st.session_state["unmatched"]

    if fighter_idx >= len(unmatched_df):
        return

    fighter_row = unmatched_df.iloc[fighter_idx]
    fighter_obj = create_fighter_object(fighter_row)

    # Determine drop target
    if target_x >= 5:  # Dropped in pairs area (x >= 5)
        # Calculate which pair slot this was dropped into
        pair_col = (target_x - 5) // 3  # Each pair takes 3 units
        pair_row = target_y // 2
        pair_idx = pair_row * 3 + pair_col

        if pair_idx < len(st.session_state["matches"]):
            # Dropped onto existing pair - attempt to modify
            handle_fighter_to_existing_pair(fighter_obj, fighter_row, pair_idx)
        else:
            # Dropped onto empty slot - create new pair
            handle_fighter_to_empty_slot(fighter_obj, fighter_row, pair_idx)


def handle_pair_drop(pair_idx, target_x, target_y):
    """Handle dropping an existing pair (for rearrangement or breaking)."""
    matches_df = st.session_state["matches"]

    if pair_idx >= len(matches_df):
        return

    # Check if dropped in unmatched area (left panel)
    if target_x < 5:  # Left panel x < 5
        # Break the pair - move fighters back to unmatched
        break_pair(pair_idx)
    else:
        # Rearrange within pairs grid - could implement pair swapping
        st.info(f"Pair {pair_idx + 1} rearranged in grid")


def break_pair(pair_idx):
    """Break an existing pair and move fighters back to unmatched pool."""
    matches_df = st.session_state["matches"]

    if pair_idx >= len(matches_df):
        return

    pair = matches_df.iloc[pair_idx]

    # Record operation for potential undo
    operation_details = {
        "action": "break_pair",
        "pair_idx": pair_idx,
        "pair_data": pair.to_dict(),
        "fighter1": pair.get("Fighter_1", ""),
        "fighter2": pair.get("Fighter_2", ""),
    }
    record_operation("break_pair", operation_details)

    # Create fighter data for unmatched pool
    fighter1_data = {
        "Name": pair.get("Fighter_1", ""),
        "Gender": pair.get("Gender", ""),
        "Age": pair.get("Age_1", 0),
        "Weight": f"{pair.get('Weight_1', 0)}-{pair.get('Weight_1', 0)}",
        "Club": pair.get("Club_1", ""),
        "Trainer": "",  # Not stored in matches
        "Record": 0,
    }

    fighter2_data = {
        "Name": pair.get("Fighter_2", ""),
        "Gender": pair.get("Gender", ""),
        "Age": pair.get("Age_2", 0),
        "Weight": f"{pair.get('Weight_2', 0)}-{pair.get('Weight_2', 0)}",
        "Club": pair.get("Club_2", ""),
        "Trainer": "",  # Not stored in matches
        "Record": 0,
    }

    # Add fighters back to unmatched pool
    unmatched_df = st.session_state["unmatched"]
    new_unmatched = pd.DataFrame([fighter1_data, fighter2_data])
    st.session_state["unmatched"] = pd.concat(
        [unmatched_df, new_unmatched], ignore_index=True
    )

    # Remove pair from matches
    matches_df = matches_df.drop(pair_idx).reset_index(drop=True)
    st.session_state["matches"] = matches_df

    st.success(f"Pair {pair_idx + 1} broken - fighters moved back to unmatched pool")


def handle_fighter_to_existing_pair(fighter_obj, fighter_row, pair_idx):
    """Handle adding a fighter to an existing pair (replacement or enhancement)."""
    matches_df = st.session_state["matches"]

    if pair_idx >= len(matches_df):
        return

    existing_pair = matches_df.iloc[pair_idx]

    # Create Fighter objects for validation
    existing_fighter1 = create_fighter_from_match(existing_pair, "Fighter_1")
    existing_fighter2 = create_fighter_from_match(existing_pair, "Fighter_2")

    # Strategy 1: Try to replace each fighter in the pair
    for target_pos in [1, 2]:
        if target_pos == 1:
            valid, message = is_valid_pair(fighter_obj, existing_fighter2)
            replacement_target = existing_fighter1
            fighter_key = "Fighter_1"
        else:
            valid, message = is_valid_pair(existing_fighter1, fighter_obj)
            replacement_target = existing_fighter2
            fighter_key = "Fighter_2"

        if valid:
            # Replace the fighter
            update_pair_with_fighter(
                pair_idx, fighter_obj, fighter_row, replacement_target, fighter_key
            )
            st.success(
                f"Replaced {replacement_target.name} with {fighter_obj.name} in Pair {pair_idx + 1}"
            )
            return

    # Strategy 2: If no direct replacement works, check if we can create a "better" pair
    # This could involve more complex logic for optimizing pairings

    # For now, show the validation error
    error_msg = (
        get_validation_error_message(message)
        if "message" in locals()
        else "Invalid pairing"
    )
    st.error(f"Cannot add {fighter_obj.name} to Pair {pair_idx + 1}: {error_msg}")


def handle_fighter_to_empty_slot(fighter_obj, fighter_row, slot_idx):
    """Handle dropping a fighter onto an empty pair slot."""
    # For now, just create a single-fighter "pair" - could be enhanced to wait for second fighter
    st.info(
        f"{fighter_obj.name} placed in slot {slot_idx + 1}. Drop another fighter to complete the pair."
    )


def create_fighter_from_match(match_row, fighter_key):
    """Create a Fighter object from match data."""
    name = match_row.get(fighter_key, "")
    gender = match_row.get("Gender", "")
    age = match_row.get(f"Age_{fighter_key[-1]}", 0)  # Age_1 or Age_2
    weight = match_row.get(f"Weight_{fighter_key[-1]}", 0)  # Weight_1 or Weight_2

    return Fighter(
        index=0,
        name=name,
        gender=gender,
        age=int(age),
        weight_min=float(weight),
        weight_max=float(weight),
        club="",  # Not stored in matches
        trainer="",
        record=0,
        total_fights=0,
        weight_class="",
    )


def update_pair_with_fighter(
    pair_idx, new_fighter, new_fighter_row, old_fighter, fighter_key
):
    """Update a pair by replacing one fighter with another."""
    matches_df = st.session_state["matches"]

    # Record operation for potential undo
    operation_details = {
        "action": "replace_fighter",
        "pair_idx": pair_idx,
        "fighter_key": fighter_key,
        "old_fighter": {
            "name": old_fighter.name,
            "weight": old_fighter.weight_min,
            "age": old_fighter.age,
        },
        "new_fighter": {
            "name": new_fighter.name,
            "weight": new_fighter.weight_min,
            "age": new_fighter.age,
        },
    }
    record_operation("replace_fighter", operation_details)

    # Update the match record
    matches_df.at[pair_idx, fighter_key] = new_fighter.name
    matches_df.at[pair_idx, f"Weight_{fighter_key[-1]}"] = new_fighter.weight_min
    matches_df.at[pair_idx, f"Age_{fighter_key[-1]}"] = new_fighter.age

    # Recalculate weight difference
    weight1 = matches_df.at[pair_idx, "Weight_1"]
    weight2 = matches_df.at[pair_idx, "Weight_2"]
    matches_df.at[pair_idx, "Weight_Diff"] = abs(weight1 - weight2)

    # Move old fighter back to unmatched
    old_fighter_data = {
        "Name": old_fighter.name,
        "Gender": old_fighter.gender,
        "Age": old_fighter.age,
        "Weight": f"{old_fighter.weight_min}-{old_fighter.weight_max}",
        "Club": old_fighter.club,
        "Trainer": old_fighter.trainer,
        "Record": old_fighter.record,
    }

    # Remove new fighter from unmatched
    unmatched_df = st.session_state["unmatched"]
    fighter_mask = (unmatched_df["Name"] == new_fighter.name) & (
        unmatched_df["Club"] == new_fighter.club
    )
    unmatched_df = unmatched_df[~fighter_mask]

    # Add old fighter to unmatched
    unmatched_df = pd.concat(
        [unmatched_df, pd.DataFrame([old_fighter_data])], ignore_index=True
    )

    st.session_state["unmatched"] = unmatched_df
    st.session_state["matches"] = matches_df


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
