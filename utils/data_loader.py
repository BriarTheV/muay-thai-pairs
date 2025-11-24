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
        df = pd.read_excel(uploaded_file, engine=engine, header=None)

        # Assign column names based on expected structure
        expected_columns = [
            "Timestamp",
            "Gender",
            "Name",
            "DOB",
            "Unknown1",
            "Weight_Range",
            "Weight_Class",
            "Class",
            "Club",
            "Trainer",
            "Total_Fights",
            "Wins",
        ]
        if len(df.columns) == len(expected_columns):
            df.columns = expected_columns
        else:
            df.columns = [f"Col{i + 1}" for i in range(len(df.columns))]

        # Calculate losses if columns exist
        if "Total_Fights" in df.columns and "Wins" in df.columns:
            df["Losses"] = df["Total_Fights"] - df["Wins"]
        else:
            df["Losses"] = 0

        if column_mapping:
            # Use provided mapping
            df = df.rename(columns=column_mapping)
        else:
            # Map standard columns for this data format
            standard_mapping = {
                "Name": "Name",
                "Gender": "Gender",
                "DOB": "DOB",
                "Weight_Class": "Weight Class",
                "Club": "Club",
                "Trainer": "Trainer",
                "Total_Fights": "Record",
                "Wins": "Wins",
                "Losses": "Losses",
                "Class": "Class",
            }
            df = df.rename(columns=standard_mapping)

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


def validate_fighter_dataframe(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Validate and clean fighter data in DataFrame format.

    Performs data type validation, fills missing values, and ensures data integrity.

    Args:
        df: DataFrame with fighter data after column processing

    Returns:
        Tuple of (validated DataFrame or None, error message string)
    """
    # Check for empty data
    if df is None or df.empty:
        return None, "No data provided"

    try:
        # Validate and convert Age column
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
            # Fill missing ages with default
            if df["Age"].isna().any():
                df["Age"] = df["Age"].fillna(25)
        else:
            df["Age"] = 25  # Default age if column missing

        df["Age"] = df["Age"].astype(int)

        # Validate and convert Record column (total fights)
        if "Record" in df.columns:
            df["Record"] = (
                pd.to_numeric(df["Record"], errors="coerce").fillna(0).astype(int)
            )
        else:
            df["Record"] = 0

        # Validate Class column
        if "Class" in df.columns:
            df["Class"] = df["Class"].astype(str).str.upper().str.strip()
            valid_classes = ["A", "B", "C", ""]
            invalid_mask = ~df["Class"].isin(valid_classes)
            if invalid_mask.any():
                invalid_rows = df[invalid_mask].index.tolist()
                return (
                    None,
                    f"Invalid class values found. Use A, B, C, or leave empty. Invalid rows: {invalid_rows}",
                )
        else:
            df["Class"] = ""

        # Handle optional fields
        optional_fields = ["Club", "Trainer", "Age_Category"]
        for field in optional_fields:
            if field in df.columns:
                df[field] = df[field].fillna("").astype(str)
            else:
                df[field] = ""

        # Validate required Name field
        if "Name" not in df.columns:
            return None, "Required 'Name' column is missing"

        # Remove rows with missing or empty names
        df = df.dropna(subset=["Name"])
        df["Name"] = df["Name"].astype(str).str.strip()
        df = df[df["Name"] != ""]

        if df.empty:
            return None, "No valid fighter data found after cleaning"

        # Ensure all required columns exist
        required_columns = ["Name", "Gender", "Age"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"Missing required columns: {', '.join(missing_columns)}"

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
