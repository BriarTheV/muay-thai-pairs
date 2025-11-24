# utils/auth.py - Authentication layer using Supabase

import streamlit as st
from supabase import create_client, Client


def init_supabase() -> Client:
    """Initialize Supabase client from secrets."""
    try:
        supabase: Client = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"]
        )
        return supabase
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {e}")
        st.stop()


def show_login_page():
    """Display login form."""
    st.title("🔐 Login Required")

    st.write("Please log in to access the Muay Thai Matchmaker.")

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            login_user(email, password)


def login_user(email: str, password: str):
    """Authenticate user with Supabase."""
    try:
        supabase = init_supabase()
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        # Store user in session state
        st.session_state.user = response.user
        st.session_state.user_email = response.user.email

        st.success("Login successful!")
        st.rerun()

    except Exception as e:
        st.error(f"Login failed: {str(e)}")


def get_current_user():
    """Get current authenticated user."""
    return st.session_state.get("user")


def logout():
    """Log out current user (alias for logout_user)."""
    logout_user()


def logout_user():
    """Log out current user."""
    try:
        supabase = init_supabase()
        supabase.auth.sign_out()
    except Exception as e:
        st.warning(f"Logout warning: {str(e)}")

    # Clear session state
    if "user" in st.session_state:
        del st.session_state.user
    if "user_email" in st.session_state:
        del st.session_state.user_email

    st.rerun()


def require_auth():
    """Check if user is authenticated, show login if not."""
    if "user" not in st.session_state:
        show_login_page()
        st.stop()  # Stop execution until logged in
