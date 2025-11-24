# utils/data_loader.py - Excel validation and cleaning

import pandas as pd
import streamlit as st
from typing import Optional, Tuple

EXPECTED_COLUMNS = ["Name", "Gender", "Age", "Weight", "Club", "Trainer", "Record"]


def validate_excel_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Validate and load Excel file with fighter data.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (DataFrame or None, error message)
    """
    if uploaded_file is None:
        return None, "No file uploaded"

    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        return validate_fighter_dataframe(df)

    except Exception as e:
        return None, f"Error reading Excel file: {str(e)}"


def validate_fighter_dataframe(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Validate fighter data in DataFrame format.

    Args:
        df: DataFrame with fighter data

    Returns:
        Tuple of (DataFrame or None, error message)
    """
    if df is None or df.empty:
        return None, "No data provided"

    try:
        # Check for required columns
        missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        if missing_cols:
            return None, f"Missing required columns: {', '.join(missing_cols)}"

        # Convert and validate data types
        df = df.copy()  # Avoid modifying original

        # Gender standardization
        df["Gender"] = df["Gender"].astype(str).str.upper().str.strip()
        valid_genders = ["M", "F", "MALE", "FEMALE"]
        invalid_genders = df[~df["Gender"].isin(valid_genders)]
        if not invalid_genders.empty:
            return (
                None,
                f"Invalid gender values found. Use M/F or Male/Female. Invalid rows: {invalid_genders.index.tolist()}",
            )

        # Map to standard M/F
        gender_map = {"MALE": "M", "FEMALE": "F"}
        df["Gender"] = df["Gender"].replace(gender_map)

        # Age validation
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
        if df["Age"].isna().any():
            return None, "Invalid age values. Must be numeric."
        df["Age"] = df["Age"].astype(int)

        # Weight validation
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
        if df["Weight"].isna().any():
            return None, "Invalid weight values. Must be numeric."
        df["Weight"] = df["Weight"].astype(float)

        # Record (experience) - optional, convert to numeric if possible
        if "Record" in df.columns:
            df["Record"] = (
                pd.to_numeric(df["Record"], errors="coerce").fillna(0).astype(int)
            )

        # Fill missing Trainer/Club with empty string
        df["Club"] = df["Club"].fillna("").astype(str)
        df["Trainer"] = df["Trainer"].fillna("").astype(str)

        # Remove rows with missing Name
        df = df.dropna(subset=["Name"])
        df["Name"] = df["Name"].astype(str).str.strip()

        if df.empty:
            return None, "No valid fighter data found after cleaning"

        return df, ""

    except Exception as e:
        return None, f"Error validating data: {str(e)}"


def get_weight_class(weight: float) -> str:
    """
    Assign IFMA weight class based on weight in kg.
    Simplified version - in reality, check official IFMA classes.
    """
    if weight <= 51.5:
        return "Light Fly"
    elif weight <= 54:
        return "Fly"
    elif weight <= 57:
        return "Bantam"
    elif weight <= 60:
        return "Feather"
    elif weight <= 63.5:
        return "Light"
    elif weight <= 67:
        return "Super Light"
    elif weight <= 71:
        return "Welter"
    elif weight <= 75:
        return "Super Welter"
    elif weight <= 81:
        return "Middle"
    elif weight <= 86:
        return "Super Middle"
    elif weight <= 91:
        return "Light Heavy"
    else:
        return "Heavy"
