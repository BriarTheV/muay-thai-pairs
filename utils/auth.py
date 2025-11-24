# utils/auth.py - Authentication layer using Supabase

import streamlit as st
from supabase import create_client, Client

# Translation dictionaries (subset for auth)
auth_translations = {
    "en": {
        "login_required": "🔐 Login Required",
        "login_instruction": "Please log in to access the Muay Thai Matchmaker.",
        "email": "Email",
        "password": "Password",
        "login_button": "Login",
        "enter_email_password": "Please enter both email and password.",
        "login_success": "Login successful!",
        "login_failed": "Login failed",
        "logout_warning": "Logout warning",
        "missing_supabase_config": "Missing Supabase configuration",
    },
    "ru": {
        "login_required": "🔐 Требуется вход",
        "login_instruction": "Пожалуйста, войдите в систему для доступа к Сопоставителю бойцов Муай Тай.",
        "email": "Электронная почта",
        "password": "Пароль",
        "login_button": "Войти",
        "enter_email_password": "Пожалуйста, введите email и пароль.",
        "login_success": "Вход выполнен успешно!",
        "login_failed": "Ошибка входа",
        "logout_warning": "Предупреждение выхода",
        "missing_supabase_config": "Отсутствует конфигурация Supabase",
    },
}


def auth_t(key):
    """Translation function for auth module"""
    lang = st.session_state.get("language", "ru")
    return auth_translations[lang].get(key, key)


def init_supabase() -> Client:
    """Initialize Supabase client from secrets."""
    try:
        supabase: Client = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"]
        )
        return supabase
    except KeyError as e:
        st.error(f"{auth_t('missing_supabase_config')}: {e}")
        st.stop()


def show_login_page():
    """Display login form."""
    st.title(auth_t("login_required"))

    st.write(auth_t("login_instruction"))

    with st.form("login_form"):
        email = st.text_input(auth_t("email"), key="login_email")
        password = st.text_input(
            auth_t("password"), type="password", key="login_password"
        )

        submitted = st.form_submit_button(auth_t("login_button"))

        if submitted:
            if not email or not password:
                st.error(auth_t("enter_email_password"))
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

        st.success(auth_t("login_success"))
        st.rerun()

    except Exception as e:
        st.error(f"{auth_t('login_failed')}: {str(e)}")


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
        st.warning(f"{auth_t('logout_warning')}: {str(e)}")

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
