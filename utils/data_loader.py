# utils/data_loader.py - Excel validation and cleaning

import pandas as pd
from typing import Optional, Tuple, Dict
import re


def parse_weight_category(text: str) -> Tuple[float, float]:
    """Parse weight category from text, supporting 'до X' and single numbers."""
    if pd.isna(text) or text == "":
        return (0, 999)  # Default wide range

    text = str(text).lower().strip()

    # Russian "до" (under/up to)
    if "до" in text:
        try:
            max_weight = float(re.search(r"до\s*(\d+(?:\.\d+)?)", text).group(1))
            return (0, max_weight)
        except Exception:
            pass

    # Single weight
    try:
        weight = float(text)
        return (weight, weight)
    except Exception:
        return (0, 999)  # Fallback


EXPECTED_COLUMNS = [
    "Name",
    "Gender",
    "Age",
    "Weight",
    "Club",
    "Trainer",
    "Record",
    "DOB",
]

# Russian column name mappings
RUSSIAN_COLUMN_MAPPING = {
    "дата": "Date",  # Event date
    "пол": "Gender",
    "фамилия и имя спортсмена": "Name",
    "дата рождения": "DOB",
    "полных лет": "Age",
    "возрастная категория": "Age_Category",
    "весовая категория": "Weight_Class",
    "класс": "Class",  # Experience class
    "город/клуб": "Club",
    "тренер": "Trainer",
    "количество боев": "Record",
    "количество побед": "Wins",
}


def validate_excel_file(
    uploaded_file, column_mapping: Optional[Dict[str, str]] = None
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Validate and load spreadsheet file with fighter data.
    If column_mapping provided, uses it; otherwise assumes standard order.

    Args:
        uploaded_file: Streamlit uploaded file object
        column_mapping: Optional dict mapping file columns to standard names

    Returns:
        Tuple of (DataFrame or None, error message)
    """
    if uploaded_file is None:
        return None, "No file uploaded"

    try:
        # Determine file type and appropriate engine
        file_name = uploaded_file.name.lower()
        if file_name.endswith(".xlsx"):
            engine = "openpyxl"
        elif file_name.endswith(".ods"):
            engine = "odf"
        else:
            return None, "Unsupported file format. Please use .xlsx or .ods files."

        # Read spreadsheet file
        df = pd.read_excel(uploaded_file, engine=engine, header=0)

        if column_mapping:
            # Use provided mapping
            df = df.rename(columns=column_mapping)
        else:
            # Assume fixed column order and rename
            expected_columns = [
                "Name",
                "Gender",
                "Age",
                "Weight Class",
                "Club",
                "Trainer",
                "Record",
            ]
            if len(df.columns) < 4:  # At least Name, Gender, Age, Weight
                return (
                    None,
                    f"File must have at least 4 columns. Found {len(df.columns)}.",
                )

            # Rename columns by position
            position_mapping = {}
            for i, col in enumerate(expected_columns):
                if i < len(df.columns):
                    position_mapping[df.columns[i]] = col

            df = df.rename(columns=position_mapping)

            # Parse weight categories
            weight_column = "Weight Class" if "Weight Class" in df.columns else "Weight"
            if weight_column in df.columns:
                # Parse weight categories into min/max
                weight_ranges = df[weight_column].apply(parse_weight_category)
                df["Weight_Min"] = weight_ranges.apply(lambda x: x[0])
                df["Weight_Max"] = weight_ranges.apply(lambda x: x[1])
                # Keep original weight text for display
                df["Weight_Display"] = df[weight_column]

            # Fill missing optional columns with empty strings
            required_columns = ["Name", "Gender", "Age", "Weight"]
            optional_columns = ["Club", "Trainer", "Record", "Class"]
            for col in required_columns + optional_columns:
                if col not in df.columns:
                    df[col] = "" if col in optional_columns else None

            return validate_fighter_dataframe(df)

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
