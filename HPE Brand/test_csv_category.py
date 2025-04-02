import pytest
import pandas as pd

# Allowed category values
VALID_CATEGORIES = {"adapter", "hba", "hdd", "memory", "optical_drives", "processor", "ssd"}

# CSV file paths
INPUT_CSV_FILE = "25022025_hpe_db_import.csv"  # Update this with your actual CSV file
INVALID_CATEGORY_CSV = "invalid_category_rows.csv"

def load_csv(file_path):
    """Load CSV into a DataFrame."""
    return pd.read_csv(file_path, dtype=str)  # Read as string to detect blanks

def test_category_column():
    """Test that the category column has only valid values and no missing data."""
    df = load_csv(INPUT_CSV_FILE)

    # Ensure required columns exist
    assert 'category' in df.columns, "Category column is missing in the CSV"
    assert 'A' in df.columns, "Column 'A' is missing in the CSV"  # Ensure column A exists

    # Trim whitespace and fill NaN with empty string for better detection
    df['category'] = df['category'].str.strip().fillna("")

    # Find invalid rows (not in valid set or empty)
    invalid_rows = df[~df['category'].isin(VALID_CATEGORIES) | (df['category'] == "")]

    # Save only the 'index', 'A', and 'category' columns to the CSV file
    if not invalid_rows.empty:
        invalid_rows[['A', 'category']].reset_index().to_csv(INVALID_CATEGORY_CSV, index=False)
        pytest.fail(f"Invalid rows found in category column. Check '{INVALID_CATEGORY_CSV}' for details.")
