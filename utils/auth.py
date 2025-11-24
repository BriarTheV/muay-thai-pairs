# utils/auth.py - Authentication layer using Supabase

import streamlit as st
from supabase import create_client, Client


def init_supabase() -> Client:
    """Initialize Supabase client from secrets."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {e}")
        st.stop()


def show_login_page():
    """Display login form."""
    st.title("🔐 Login to Muay Thai Matchmaker")

    # Initialize Supabase
    supabase = init_supabase()

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state.user = response.user
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")


def logout():
    """Logout user."""
    supabase = init_supabase()
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.rerun()


def require_auth():
    """Check if user is authenticated, show login if not."""
    if "user" not in st.session_state or st.session_state.user is None:
        show_login_page()
        st.stop()


def get_current_user():
    """Get current authenticated user."""
    return st.session_state.get("user")
