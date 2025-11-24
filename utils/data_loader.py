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
                "Weight",
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

        # Parse weight categories for standard order
        if "Weight" in df.columns:
            df["Weight_Min"] = df["Weight"].apply(lambda x: parse_weight_category(x)[0])
            df["Weight_Max"] = df["Weight"].apply(lambda x: parse_weight_category(x)[1])

        # Fill missing optional columns with empty strings
        required_columns = ["Name", "Gender", "Age", "Weight"]
        optional_columns = ["Club", "Trainer", "Record", "Class"]
        for col in required_columns + optional_columns:
            if col not in df.columns:
                df[col] = "" if col in optional_columns else None

        return validate_fighter_dataframe(df)

    except Exception as e:
        return None, f"Error reading spreadsheet file: {str(e)}"


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
        # First, map Russian column names to English
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()

        # Apply Russian column mapping
        column_mapping = {}
        for rus_col, eng_col in RUSSIAN_COLUMN_MAPPING.items():
            if rus_col.lower() in df.columns:
                column_mapping[rus_col.lower()] = eng_col

        df = df.rename(columns=column_mapping)

        # Check for required columns (at least Name, Gender, Weight)
        required_cols = ["Name", "Gender", "Weight"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return None, f"Missing required columns: {', '.join(missing_cols)}"

        # Convert and validate data types
        df = df.copy()  # Avoid modifying original

        # Gender standardization
        df["Gender"] = df["Gender"].astype(str).str.upper().str.strip()
        valid_genders = ["M", "F", "MALE", "FEMALE", "М", "Ж", "МУЖ", "ЖЕН"]
        invalid_genders = df[~df["Gender"].isin(valid_genders)]
        if not invalid_genders.empty:
            return (
                None,
                f"Invalid gender values found. Use M/F or Male/Female. Invalid rows: {invalid_genders.index.tolist()}",
            )

        # Map to standard M/F
        gender_map = {
            "MALE": "M",
            "FEMALE": "F",
            "МУЖ": "M",
            "ЖЕН": "F",
            "М": "M",
            "Ж": "F",
        }
        df["Gender"] = df["Gender"].replace(gender_map)

        # DOB processing (optional)
        if "DOB" in df.columns:
            df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")

        # Age validation/calculation
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
            # If DOB exists and Age is missing, calculate age
            if "DOB" in df.columns:
                mask = df["Age"].isna() & df["DOB"].notna()
                df.loc[mask, "Age"] = (
                    pd.Timestamp.now() - df.loc[mask, "DOB"]
                ).dt.days // 365
        else:
            # Calculate age from DOB if available
            if "DOB" in df.columns:
                df["Age"] = (pd.Timestamp.now() - df["DOB"]).dt.days // 365
            else:
                df["Age"] = 25  # Default age

        if df["Age"].isna().any():
            df["Age"] = df["Age"].fillna(25)  # Default age

        df["Age"] = df["Age"].astype(int)

        # Weight category parsing
        if "Weight" in df.columns:
            # Parse weight categories into min/max
            weight_ranges = df["Weight"].apply(parse_weight_category)
            df["Weight_Min"] = weight_ranges.apply(lambda x: x[0])
            df["Weight_Max"] = weight_ranges.apply(lambda x: x[1])
            # Keep original weight text for display
            df["Weight_Display"] = df["Weight"]
        else:
            df["Weight_Min"] = 0
            df["Weight_Max"] = 999
            df["Weight_Display"] = ""

        # Record (experience) - optional, convert to numeric if possible
        if "Record" in df.columns:
            df["Record"] = (
                pd.to_numeric(df["Record"], errors="coerce").fillna(0).astype(int)
            )

        # Wins - optional
        if "Wins" in df.columns:
            df["Wins"] = (
                pd.to_numeric(df["Wins"], errors="coerce").fillna(0).astype(int)
            )

        # Class validation - optional, must be A, B, C, or empty
        if "Class" in df.columns:
            df["Class"] = df["Class"].astype(str).str.upper().str.strip()
            valid_classes = ["A", "B", "C", ""]
            invalid_classes = df[~df["Class"].isin(valid_classes)]
            if not invalid_classes.empty:
                return (
                    None,
                    f"Invalid class values found. Use A, B, C, or leave empty. Invalid rows: {invalid_classes.index.tolist()}",
                )

        # Fill missing optional fields with empty string
        optional_fields = ["Club", "Trainer", "Class", "Age_Category"]
        for field in optional_fields:
            if field in df.columns:
                df[field] = df[field].fillna("").astype(str)
            else:
                df[field] = ""

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
