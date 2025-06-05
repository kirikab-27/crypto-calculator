"""Debug module for date filtering issues."""

import logging
import os
from datetime import datetime
from typing import Optional

# Enable debug logging
os.environ['ENABLE_DEBUG_LOGS'] = '1'
logging.basicConfig(level=logging.DEBUG)

def debug_date_filter(start_date: Optional[str], end_date: Optional[str]) -> dict:
    """Debug helper for date filtering issues.
    
    Returns diagnostic information about date filtering.
    """
    from src.date_utils import ensure_date_normalized, validate_date_format
    
    result = {
        "input": {
            "start_date": start_date,
            "end_date": end_date
        },
        "normalized": {},
        "validation": {},
        "errors": []
    }
    
    # Check start date
    if start_date:
        try:
            normalized_start = ensure_date_normalized(start_date)
            result["normalized"]["start_date"] = normalized_start
            result["validation"]["start_date"] = validate_date_format(normalized_start)
        except Exception as e:
            result["errors"].append(f"Start date error: {str(e)}")
    
    # Check end date
    if end_date:
        try:
            normalized_end = ensure_date_normalized(end_date)
            result["normalized"]["end_date"] = normalized_end
            result["validation"]["end_date"] = validate_date_format(normalized_end)
        except Exception as e:
            result["errors"].append(f"End date error: {str(e)}")
    
    # Check date order
    if start_date and end_date and not result["errors"]:
        try:
            start_obj = datetime.strptime(result["normalized"]["start_date"], "%Y-%m-%d")
            end_obj = datetime.strptime(result["normalized"]["end_date"], "%Y-%m-%d")
            if start_obj > end_obj:
                result["errors"].append("Start date is after end date")
        except Exception as e:
            result["errors"].append(f"Date comparison error: {str(e)}")
    
    return result