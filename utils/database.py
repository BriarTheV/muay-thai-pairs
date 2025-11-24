# utils/database.py - Database operations with Supabase

import streamlit as st
from supabase import create_client, Client
from typing import List, Dict, Optional
import pandas as pd


def get_supabase_client() -> Client:
    """Get initialized Supabase client."""
    try:
        supabase: Client = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"]
        )
        return supabase
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {e}")
        st.stop()


# Clubs operations
def get_clubs() -> List[Dict]:
    """Get all clubs."""
    supabase = get_supabase_client()
    response = supabase.table("clubs").select("*").execute()
    return response.data


def add_club(name: str, contact_info: Optional[Dict] = None) -> Dict:
    """Add new club."""
    supabase = get_supabase_client()
    data = {"name": name}
    if contact_info:
        data["contact_info"] = contact_info
    response = supabase.table("clubs").insert(data).execute()
    return response.data[0]


# Fighters operations
def get_fighters(active_only: bool = True) -> List[Dict]:
    """Get all fighters."""
    supabase = get_supabase_client()
    query = supabase.table("fighters").select("*, clubs(name)")
    if active_only:
        query = query.eq("active_status", True)
    response = query.execute()
    return response.data


def add_fighter(fighter_data: Dict) -> Dict:
    """Add new fighter."""
    supabase = get_supabase_client()
    response = supabase.table("fighters").insert(fighter_data).execute()
    return response.data[0]


def update_fighter(fighter_id: int, updates: Dict) -> Dict:
    """Update fighter."""
    supabase = get_supabase_client()
    response = supabase.table("fighters").update(updates).eq("id", fighter_id).execute()
    return response.data[0]


def deactivate_fighter(fighter_id: int):
    """Deactivate fighter."""
    update_fighter(fighter_id, {"active_status": False})


# Events operations
def get_events() -> List[Dict]:
    """Get all events."""
    supabase = get_supabase_client()
    response = supabase.table("events").select("*").order("date", desc=True).execute()
    return response.data


def add_event(name: str, date: str, location: str = "") -> Dict:
    """Add new event."""
    supabase = get_supabase_client()
    response = (
        supabase.table("events")
        .insert({"name": name, "date": date, "location": location})
        .execute()
    )
    return response.data[0]


# Matches operations
def save_matches(event_id: int, matches_df: pd.DataFrame):
    """Save matches for an event."""
    supabase = get_supabase_client()

    # Convert DataFrame to match records
    matches_data = []
    for _, match in matches_df.iterrows():
        matches_data.append(
            {
                "event_id": event_id,
                "fighter_red_id": int(match["Red_ID"]),  # Assuming we have IDs
                "fighter_blue_id": int(match["Blue_ID"]),
                "result": None,  # To be filled after event
            }
        )

    response = supabase.table("matches").insert(matches_data).execute()
    return response.data


def get_event_matches(event_id: int) -> List[Dict]:
    """Get matches for an event."""
    supabase = get_supabase_client()
    response = (
        supabase.table("matches")
        .select("""
        *,
        fighter_red:fighter_red_id(name, club),
        fighter_blue:fighter_blue_id(name, club)
    """)
        .eq("event_id", event_id)
        .execute()
    )
    return response.data
