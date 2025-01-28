import re
import pandas as pd
import pytest

# Regex pattern to allow:
#  - letters (A–Z, a–z)
#  - digits (0–9)
#  - spaces (\s)
#  - hyphens (-)
VALID_PATTERN = re.compile(r'^[A-Za-z0-9\s-]+$')

def is_valid_value(value: str) -> bool:
    """Check if the value has only letters, digits, spaces, and hyphens."""
    return bool(VALID_PATTERN.match(value))

def has_comma(value: str) -> bool:
    """Check if the string contains a comma."""
    return ',' in value

@pytest.fixture
def load_csv():          
    """Fixture to load the CSV file into a DataFrame."""
    file_path = "hpe_db_import (1).csv"  # <-- Update with your CSV path
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # remove extra spaces in column names
    return df

def test_column_c_data(load_csv):
    """
    Validate that column C:
    - Does not contain commas.
    - Includes only letters, digits, spaces, and (optionally) hyphens.
    """
    df = load_csv
    assert 'C' in df.columns, "Column 'C' not found in the CSV file."

    errors = []

    for index, row in df.iterrows():
        raw_value = row['C']
        # Convert to string and strip leading/trailing whitespace
        value = str(raw_value).strip()

        # 1) Check for commas
        if has_comma(value):
            errors.append({
                "row": index,
                "value": value,
                "error": "Comma detected in column C"
            })
            continue 

        # 2) Check if only letters, digits, spaces, and hyphens
        if not is_valid_value(value):
            errors.append({
                "row": index,
                "value": value,
                "error": (
                    "Contains invalid characters. Only letters, digits, spaces, "
                    "and (optionally) hyphens are allowed."
                )
            })

    if errors:
        results_df = pd.DataFrame(errors)
        results_df.to_csv("test_results_column_c3.csv", index=False)
        assert False, (
            "Validation failed. Details are logged in 'test_results_column_c3.csv'."
        )
