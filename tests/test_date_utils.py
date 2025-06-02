"""Unit tests for date_utils module."""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.date_utils import normalize_date_to_string, validate_date_format, ensure_date_normalized


class TestNormalizeDateToString:
    """Test normalize_date_to_string function."""
    
    def test_string_formats(self):
        """Test various string date formats."""
        # ISO format
        assert normalize_date_to_string("2023-12-25") == "2023-12-25"
        
        # With time
        assert normalize_date_to_string("2023-12-25 14:30:00") == "2023-12-25"
        assert normalize_date_to_string("2023/12/25 14:30:00") == "2023-12-25"
        
        # Different separators
        assert normalize_date_to_string("2023/12/25") == "2023-12-25"
        assert normalize_date_to_string("2023.12.25") == "2023-12-25"
        
        # Different order formats
        assert normalize_date_to_string("25-12-2023") == "2023-12-25"
        assert normalize_date_to_string("25/12/2023") == "2023-12-25"
        assert normalize_date_to_string("12-25-2023") == "2023-12-25"
        assert normalize_date_to_string("12/25/2023") == "2023-12-25"
        
        # Compact format
        assert normalize_date_to_string("20231225") == "2023-12-25"
        
        # ISO 8601 with timezone
        assert normalize_date_to_string("2023-12-25T14:30:00Z") == "2023-12-25"
        assert normalize_date_to_string("2023-12-25T14:30:00+00:00") == "2023-12-25"
    
    def test_numeric_timestamps(self):
        """Test Unix timestamp formats."""
        # Unix timestamp in seconds (2023-12-25 00:00:00 UTC)
        assert normalize_date_to_string(1703462400) == "2023-12-25"
        
        # Unix timestamp in milliseconds
        assert normalize_date_to_string(1703462400000) == "2023-12-25"
        
        # Float timestamps
        assert normalize_date_to_string(1703462400.0) == "2023-12-25"
        assert normalize_date_to_string(1703462400000.0) == "2023-12-25"
        
        # String timestamps
        assert normalize_date_to_string("1703462400") == "2023-12-25"
        assert normalize_date_to_string("1703462400000") == "2023-12-25"
    
    def test_datetime_objects(self):
        """Test datetime object input."""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        assert normalize_date_to_string(dt) == "2023-12-25"
    
    def test_invalid_dates(self):
        """Test invalid date inputs."""
        with pytest.raises(ValueError):
            normalize_date_to_string("not a date")
        
        with pytest.raises(ValueError):
            normalize_date_to_string("")
        
        with pytest.raises(ValueError):
            normalize_date_to_string("2023-13-01")  # Invalid month
        
        with pytest.raises(ValueError):
            normalize_date_to_string("2023-12-32")  # Invalid day


class TestValidateDateFormat:
    """Test validate_date_format function."""
    
    def test_valid_formats(self):
        """Test valid date formats."""
        assert validate_date_format("2023-12-25") is True
        assert validate_date_format("2023-01-01") is True
        assert validate_date_format("1999-12-31") is True
        assert validate_date_format("2024-02-29") is True  # Leap year
    
    def test_invalid_formats(self):
        """Test invalid date formats."""
        # Wrong separators
        assert validate_date_format("2023/12/25") is False
        assert validate_date_format("2023.12.25") is False
        
        # Wrong order
        assert validate_date_format("25-12-2023") is False
        assert validate_date_format("12-25-2023") is False
        
        # Invalid dates
        assert validate_date_format("2023-13-01") is False  # Invalid month
        assert validate_date_format("2023-12-32") is False  # Invalid day
        assert validate_date_format("2023-02-29") is False  # Not a leap year
        
        # Not strings
        assert validate_date_format(None) is False
        assert validate_date_format(123) is False
        assert validate_date_format(datetime.now()) is False
        
        # Empty or invalid strings
        assert validate_date_format("") is False
        assert validate_date_format("not a date") is False
        assert validate_date_format("2023-12-25 10:30:00") is False  # Has time


class TestEnsureDateNormalized:
    """Test ensure_date_normalized function."""
    
    def test_already_normalized(self):
        """Test dates that are already normalized."""
        assert ensure_date_normalized("2023-12-25") == "2023-12-25"
        assert ensure_date_normalized("1999-01-01") == "1999-01-01"
    
    def test_needs_normalization(self):
        """Test dates that need normalization."""
        assert ensure_date_normalized("2023/12/25") == "2023-12-25"
        assert ensure_date_normalized("25-12-2023") == "2023-12-25"
        assert ensure_date_normalized(datetime(2023, 12, 25)) == "2023-12-25"
        assert ensure_date_normalized("2023-12-25 10:30:00") == "2023-12-25"
    
    def test_error_cases(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            ensure_date_normalized("invalid date")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])