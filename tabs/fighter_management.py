import streamlit as st
import pandas as pd
from utils.data_loader import get_weight_class
from utils.translations import translations


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def render_fighter_management_tab():
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

        # Get data
        clubs = get_clubs()
        club_options = [""] + [club["name"] for club in clubs]

        # Tabs for different management functions
        manage_tab1, manage_tab2, manage_tab3 = st.tabs(
            [t("manage_add_fighter"), t("manage_edit_fighters"), t("manage_clubs")]
        )

        with manage_tab1:
            st.subheader(t("add_fighter"))

            with st.form("add_fighter_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(t("fighter_name"), key="add_name")
                    gender = st.selectbox(
                        t("fighter_gender"), ["M", "F"], key="add_gender"
                    )
                    weight = st.number_input(
                        t("fighter_weight"),
                        min_value=40.0,
                        max_value=150.0,
                        value=70.0,
                        step=0.1,
                        key="add_weight",
                    )
                    age = st.number_input(
                        t("fighter_age"),
                        min_value=10,
                        max_value=100,
                        value=25,
                        key="add_age",
                    )
                    club = st.selectbox(t("fighter_club"), club_options, key="add_club")
                    record = st.number_input(
                        t("fighter_record"),
                        min_value=0,
                        value=0,
                        key="add_record",
                    )
                trainer = st.text_input(
                    t("fighter_trainer_optional"), key="add_trainer"
                )
                wins = st.number_input(
                    t("fighter_wins"),
                    min_value=0,
                    value=0,
                    key="add_wins",
                )

                with col2:
                    dob = st.date_input(t("dob_optional"), key="add_dob")
                    age = st.number_input(
                        t("fighter_age"),
                        min_value=16,
                        max_value=100,
                        value=25,
                        key="add_age",
                    )
                    club_options = [""] + [club["name"] for club in get_clubs()]
                    club = st.selectbox(t("fighter_club"), club_options, key="add_club")
                    total_fights = st.number_input(
                        "Total Fights",
                        min_value=0,
                        max_value=100,
                        value=0,
                        key="add_record",
                    )

                trainer = st.text_input(t("trainer_optional"), key="add_trainer")
                wins = st.number_input(
                    t("wins_optional"),
                    min_value=0,
                    max_value=100,
                    value=0,
                    key="add_wins",
                )
                fighter_class = st.selectbox(
                    t("fighter_class"),
                    ["", "A", "B", "C"],
                    index=0,
                    key="add_class",
                )

                submitted = st.form_submit_button(t("add_fighter_button"))

                if submitted:
                    if not name or not gender or not weight:
                        st.error(t("required_fields"))
                    else:
                        fighter_data = {
                            "name": name,
                            "gender": gender,
                            "dob": str(dob) if dob else None,
                            "age": age,
                            "weight_min": weight,
                            "weight_max": weight,
                            "weight_class": get_weight_class(weight),
                            "club_id": next(
                                (c["id"] for c in get_clubs() if c["name"] == club),
                                None,
                            )
                            if club
                            else None,
                            "trainer": trainer or "",
                            "record_w": wins,
                            "record_l": total_fights - wins,
                            "class": fighter_class or None,
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
                        "ID": st.column_config.NumberColumn(
                            t("column_id"), disabled=True
                        ),
                        "Name": st.column_config.TextColumn(
                            t("column_name"), required=True
                        ),
                        "Gender": st.column_config.SelectboxColumn(
                            t("column_gender"), options=["M", "F"], required=True
                        ),
                        "Age": st.column_config.NumberColumn(
                            t("column_age"), min_value=10, max_value=100, required=True
                        ),
                        "Weight": st.column_config.NumberColumn(
                            t("column_weight"),
                            min_value=40.0,
                            max_value=150.0,
                            required=True,
                        ),
                        "Club": st.column_config.TextColumn(t("column_club")),
                        "Trainer": st.column_config.TextColumn(t("column_trainer")),
                        "Record_W": st.column_config.NumberColumn(
                            t("column_wins"), min_value=0
                        ),
                        "Record_L": st.column_config.NumberColumn(
                            t("column_losses"), min_value=0
                        ),
                        "Active": st.column_config.CheckboxColumn(t("column_active")),
                    },
                )

                if st.button(t("save_changes"), type="primary"):
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

                    if st.button(t("deactivate_selected"), type="secondary"):
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
                                    st.error(
                                        f"{t('error_deactivating')} {name}: {str(e)}"
                                    )

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
                club_name = st.text_input(t("club_name"), key="club_name")
                contact_info = st.text_area(
                    t("contact_info_json"),
                    placeholder='{"phone": "+1234567890", "email": "club@example.com"}',
                    key="club_contact",
                )

                submitted = st.form_submit_button(t("add_club_button"))

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
