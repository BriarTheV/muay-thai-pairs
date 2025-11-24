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
        return (None, "No file uploaded")

    try:
        # Determine file type and appropriate engine
        file_name = uploaded_file.name.lower()
        if file_name.endswith(".xlsx"):
            engine = "openpyxl"
        elif file_name.endswith(".ods"):
            engine = "odf"
        else:
            return (None, "Unsupported file format. Please use .xlsx or .ods files.")

        # Detect if file has headers
        temp_df = pd.read_excel(uploaded_file, engine=engine, header=None, nrows=1)
        first_row = temp_df.iloc[0].astype(str).str.lower()
        header_keywords = [
            "name",
            "имя",
            "gender",
            "пол",
            "вес",
            "weight",
            "age",
            "возраст",
            "club",
            "клуб",
        ]

        has_headers = any(
            any(keyword in cell for keyword in header_keywords) for cell in first_row
        )

        if has_headers:
            # Read with headers
            df = pd.read_excel(uploaded_file, engine=engine, header=0)
        else:
            # Read without headers
            df = pd.read_excel(uploaded_file, engine=engine, header=None)

        if column_mapping:
            # Map columns based on whether data_value is a column name or first row value
            rename_dict = {}
            for data_value, standard_name in column_mapping.items():
                if data_value in df.columns:
                    # Header file: data_value is the column name, direct rename
                    rename_dict[data_value] = standard_name
                else:
                    # Data file: data_value is first row value, find matching column
                    for col in df.columns:
                        if str(df.iloc[0, col]) == data_value:
                            rename_dict[col] = standard_name
                            break
            df.rename(columns=rename_dict, inplace=True)
            # Ensure all column names are strings
            df.columns = [str(c) for c in df.columns]

        else:
            # Use first line from file as column names for data files without mapping
            if not has_headers:
                if len(df) > 0:
                    df.columns = df.iloc[0].astype(str)
                    df = df[1:].reset_index(drop=True)
                else:
                    df.columns = [f"Col{i + 1}" for i in range(len(df.columns))]

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
        return (None, f"Error validating data: {str(e)}")


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
        return (None, "No data provided")

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

        # Validate and convert Total_Fights and Wins columns
        if "Total_Fights" in df.columns:
            df["Total_Fights"] = (
                pd.to_numeric(df["Total_Fights"], errors="coerce").fillna(0).astype(int)
            )
        else:
            df["Total_Fights"] = 0

        if "Wins" in df.columns:
            df["Wins"] = (
                pd.to_numeric(df["Wins"], errors="coerce").fillna(0).astype(int)
            )
        else:
            df["Wins"] = 0

        # Calculate Losses if both columns exist
        if "Total_Fights" in df.columns and "Wins" in df.columns:
            df["Losses"] = df["Total_Fights"] - df["Wins"]
        else:
            df["Losses"] = 0

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
            return (None, "Required 'Name' column is missing")

        # Remove rows with missing or empty names
        df = df.dropna(subset=["Name"])
        df["Name"] = df["Name"].astype(str).str.strip()
        df = df[df["Name"] != ""]

        if df.empty:
            return (None, "No valid fighter data found after cleaning")

        return (df, "")

    except Exception as e:
        return (None, f"Error validating data: {str(e)}")


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
