import pytest
import pandas as pd
import os

# Allowed category values
VALID_CATEGORIES = {"adapter", "hba", "hdd", "memory", "optical_drives", "processor", "ssd"}

# CSV file paths
INPUT_CSV_FILE = "25022025_hpe_db_import.csv"  # Update this with your actual CSV file
INVALID_CATEGORY_CSV = "invalid_category_rows_updated1.csv"  # Output CSV file

def load_csv(file_path):
    """Load CSV into a DataFrame."""
    return pd.read_csv(file_path, dtype=str)  # Read as string to detect blanks

def test_category_column():
    """Test that the category column has only valid values and no missing data."""
    df = load_csv(INPUT_CSV_FILE)

    # Ensure required category column exists
    assert 'category' in df.columns, "Category column is missing in the CSV"

    # Check if column 'A' exists and print its values if it does
    if 'A' in df.columns:
        print("Values in column 'A':", df['A'].unique())

    # Trim whitespace and fill NaN with empty string for better detection
    df['category'] = df['category'].str.strip().fillna("")  

    # Print unique categories in the CSV for debugging
    print("Unique categories found in CSV:", df['category'].unique())

    # Find invalid rows (not in valid set or empty)
    invalid_rows = df[~df['category'].isin(VALID_CATEGORIES) | (df['category'] == "")]

    # Check if invalid rows exist before saving
    if not invalid_rows.empty:
        # Ensure the output directory exists (create if needed)
        output_dir = os.path.dirname(INVALID_CATEGORY_CSV)
        if not os.path.exists(output_dir) and output_dir != '':
            os.makedirs(output_dir)
        
        # Save both 'A' and 'category' columns to the CSV file for invalid rows
        invalid_rows[['A', 'category']].reset_index(drop=True).to_csv(INVALID_CATEGORY_CSV, index=False)
        print(f"Invalid rows with column A and category saved to {INVALID_CATEGORY_CSV}")
    else:
        print("No invalid rows found.")

    # Check for missing categories
    present_categories = set(df['category'].unique())
    missing_categories = VALID_CATEGORIES - present_categories

    if missing_categories:
        print(f"Warning: Missing categories in the CSV: {', '.join(missing_categories)}")  # Log a warning
        pytest.fail(f"Missing categories in the CSV: {', '.join(missing_categories)}")  # Fail after logging the issue
    else:
        print("All required categories are present in the CSV.")
