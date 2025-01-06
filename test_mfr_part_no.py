import pandas as pd
import re
import pytest

# Validation function
def is_valid_mfr_part_no(value):
    
    pattern = r'^[a-zA-Z0-9]{4,8}(-B21|-H21|-K21|-S01|-L22|-S21|-L21|-001|-B22)?$'
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

    # Separate valid and invalid rows
    valid_rows = df[df['mfr_part_no'].apply(is_valid_mfr_part_no)]
    invalid_rows = df[~df['mfr_part_no'].apply(is_valid_mfr_part_no)]

    # Write results to a file
    with open("test_results.txt", "w") as result_file:
        result_file.write("===== TEST RESULTS FOR mfr_part_no =====\n\n")

        # Log valid part numbers
        result_file.write("VALID mfr_part_no VALUES:\n")
        if not valid_rows.empty:
            for part_no in valid_rows['mfr_part_no']:
                result_file.write(f"{part_no}\n")
        else:
            result_file.write("No valid values found.\n")

        result_file.write("\n")

        # Log invalid part numbers and detailed row information
        result_file.write("INVALID mfr_part_no VALUES:\n")
        if not invalid_rows.empty:
            for index, row in invalid_rows.iterrows():
                result_file.write(f"Row {index}: {row['mfr_part_no']}\n")
        else:
            result_file.write("No invalid values found.\n")

    # Always fail the test if invalid rows exist
    if not invalid_rows.empty:
        raise AssertionError(f"Invalid rows found. Details are logged in 'test_results.txt'.")
