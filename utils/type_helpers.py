"""
Type conversion utilities for robust data handling.

This module provides safe type conversion functions that handle various input formats
(strings, bytes, None values) and provide consistent behavior across the application.
"""

import re
from typing import Union

# Import pandas early to avoid issues with pd.isna() calls
try:
    import pandas as pd
except ImportError:
    # Fallback if pandas not available
    class _MockPandas:
        @staticmethod
        def isna(value):
            if value is None:
                return True
            if isinstance(value, float):
                return str(value).lower() in ("nan", "inf", "-inf")
            return False

    pd = _MockPandas()


def safe_int_conversion(value: Union[str, int, float, bytes, None]) -> int:
    """Safely convert various data types to integer, handling strings, bytes, floats, etc.

    Args:
        value: The value to convert to integer

    Returns:
        int: The converted integer value, or 0 if conversion fails

    Examples:
        >>> safe_int_conversion("10")
        10
        >>> safe_int_conversion(b"20")
        20
        >>> safe_int_conversion("wins: 25")
        25
        >>> safe_int_conversion(None)
        0
    """
    if pd.isna(value) or value == "" or value is None:
        return 0

    try:
        # Handle bytes objects (decode if needed)
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")

        # Convert to string first to handle all cases
        str_val = str(value).strip()

        # Remove any non-numeric characters except decimal point
        numeric_str = re.sub(r"[^\d.]", "", str_val)

        # If empty after cleaning, return 0
        if not numeric_str:
            return 0

        # Convert to float first, then int (handles "5.0" -> 5)
        return int(float(numeric_str))

    except (ValueError, TypeError, AttributeError):
        # If conversion fails, return 0
        return 0


def safe_float_conversion(value: Union[str, int, float, bytes, None]) -> float:
    """Safely convert various data types to float.

    Args:
        value: The value to convert to float

    Returns:
        float: The converted float value, or 0.0 if conversion fails

    Examples:
        >>> safe_float_conversion("10.5")
        10.5
        >>> safe_float_conversion("invalid")
        0.0
    """
    if pd.isna(value) or value == "" or value is None:
        return 0.0

    try:
        # Handle bytes objects
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")

        # Convert to string first
        str_val = str(value).strip()

        # Remove non-numeric characters except decimal point and minus
        numeric_str = re.sub(r"[^\d.-]", "", str_val)

        if not numeric_str or numeric_str == "-" or numeric_str == ".":
            return 0.0

        return float(numeric_str)

    except (ValueError, TypeError, AttributeError):
        return 0.0


def safe_str_conversion(value: Union[str, int, float, bytes, None]) -> str:
    """Safely convert various data types to string.

    Args:
        value: The value to convert to string

    Returns:
        str: The converted string value, or empty string if conversion fails

    Examples:
        >>> safe_str_conversion(123)
        '123'
        >>> safe_str_conversion(None)
        ''
    """
    if pd.isna(value) or value is None:
        return ""

    try:
        # Handle bytes objects
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")

        return str(value).strip()

    except (AttributeError, TypeError):
        return ""
