import pandas as pd
import re
import pytest

# Validation function
def is_valid_mfr_part_no(value):
    pattern = r'^[a-zA-Z0-9]{4,6}(-B21|-H21|-K21|-S01|-L22|-S21|-L21|-001|-B22)?$'
    return bool(re.match(pattern, str(value)))

@pytest.fixture
def load_csv():
    """Fixture to load the CSV file into a DataFrame."""
    file_path = "hpe_db_import (1).csv"  # Path to your test CSV file
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Ensure no extra spaces in column names
    return df

def test_mfr_part_no_results(load_csv):
    """Test and log results for 'mfr_part_no' column."""
    df = load_csv

    # Check if the column exists
    assert 'mfr_part_no' in df.columns, "Column 'mfr_part_no' not found in the CSV file."

    # Create Valid and Invalid columns
    df['Valid_mfr_part_no'] = df['mfr_part_no'].apply(lambda x: x if is_valid_mfr_part_no(x) else None)
    df['Invalid_mfr_part_no'] = df['mfr_part_no'].apply(lambda x: x if not is_valid_mfr_part_no(x) else None)

    # Save the updated DataFrame to a new CSV file
    output_file = "mfr_part_no_validation_results.csv"
    df.to_csv(output_file, index=False)
    print(f"Validation results saved to '{output_file}'.")

    # Always fail the test if invalid rows exist
    if df['Invalid_mfr_part_no'].notna().any():
        raise AssertionError("Invalid mfr_part_no values found. Details saved to the output CSV file.")













