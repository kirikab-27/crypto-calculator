"""Date utility functions for consistent date handling."""

from datetime import datetime
from typing import Optional, Union
import re


def normalize_date_to_string(date_input: Union[str, datetime, int, float]) -> str:
    """Normalize various date formats to YYYY-MM-DD string format.
    
    Parameters
    ----------
    date_input : Union[str, datetime, int, float]
        Date in various formats:
        - String in various date formats
        - datetime object
        - Unix timestamp (int or float)
        
    Returns
    -------
    str
        Date in YYYY-MM-DD format
        
    Raises
    ------
    ValueError
        If date cannot be parsed
    """
    if isinstance(date_input, datetime):
        return date_input.strftime("%Y-%m-%d")
    
    if isinstance(date_input, (int, float)):
        # Handle Unix timestamps
        # If timestamp is in milliseconds (> 10 digits), convert to seconds
        if date_input > 10000000000:
            date_input = date_input / 1000
        return datetime.fromtimestamp(date_input).strftime("%Y-%m-%d")
    
    if isinstance(date_input, str):
        # Remove extra whitespace
        date_str = date_input.strip()
        
        # If already in correct format, return as is
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            # Validate it's a real date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                pass
        
        # Try various date formats
        date_formats = [
            "%Y-%m-%d",           # ISO format
            "%Y/%m/%d",           # Alternative with slashes
            "%Y-%m-%d %H:%M:%S", # Datetime with time
            "%Y/%m/%d %H:%M:%S", # Datetime with slashes
            "%d-%m-%Y",           # European format
            "%d/%m/%Y",           # European with slashes
            "%m-%d-%Y",           # US format
            "%m/%d/%Y",           # US with slashes
            "%Y%m%d",             # Compact format
            "%d.%m.%Y",           # German format
            "%Y.%m.%d",           # Alternative dot format
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Try parsing as timestamp if it's numeric
        if date_str.isdigit():
            return normalize_date_to_string(int(date_str))
        
        # Try using fromisoformat for ISO 8601 formats
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        except:
            pass
    
    raise ValueError(f"Unable to parse date: {date_input}")


def validate_date_format(date_str: str) -> bool:
    """Validate that a date string is in YYYY-MM-DD format.
    
    Parameters
    ----------
    date_str : str
        Date string to validate
        
    Returns
    -------
    bool
        True if valid YYYY-MM-DD format, False otherwise
    """
    if not isinstance(date_str, str):
        return False
    
    # Check format with regex
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    
    # Validate it's a real date
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def ensure_date_normalized(date_input: Union[str, datetime]) -> str:
    """Ensure date is normalized to YYYY-MM-DD format.
    
    This is a convenience function that handles the most common case
    where the input is already normalized.
    
    Parameters
    ----------
    date_input : Union[str, datetime]
        Date as string or datetime object
        
    Returns
    -------
    str
        Date in YYYY-MM-DD format
    """
    if isinstance(date_input, str) and validate_date_format(date_input):
        return date_input
    
    return normalize_date_to_string(date_input)