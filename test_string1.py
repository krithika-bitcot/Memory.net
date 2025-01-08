import pandas as pd
import pytest

# Validation function
def is_valid_string(value):
    """
    Function to validate that a value is a string.
    """
    return isinstance(value, str)

@pytest.fixture
def load_csv():
    """Fixture to load the CSV file into a DataFrame."""
    file_path = "hpe_db_import (1).csv"  # Path to your test CSV file
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Ensure no extra spaces in column names
    return df

def test_string_columns(load_csv):
    """Test and log results for specific columns containing only string values."""
    df = load_csv

    # Columns to validate
    columns_to_test = ['store', 'A', 'B']

    with open("test_results_1.txt", "w") as result_file:
        result_file.write("===== TEST RESULTS FOR STRING VALIDATION =====\n\n")

        for column in columns_to_test:
            # Check if the column exists
            assert column in df.columns, f"Column '{column}' not found in the CSV file."

            # Separate valid and invalid rows
            valid_rows = df[df[column].apply(is_valid_string)]
            invalid_rows = df[~df[column].apply(is_valid_string)]

            # Log results for the column
            result_file.write(f"Results for column '{column}':\n")

            # Log valid values
            result_file.write("VALID VALUES:\n")
            if not valid_rows.empty:
                for value in valid_rows[column]:
                    result_file.write(f"{value}\n")
            else:
                result_file.write("No valid values found.\n")

            result_file.write("\n")

            # Log invalid values
            result_file.write("INVALID VALUES:\n")
            if not invalid_rows.empty:
                for index, row in invalid_rows.iterrows():
                    result_file.write(f"Row {index}: {row[column]}\n")
            else:
                result_file.write("No invalid values found.\n")

            result_file.write("\n")

        # Always fail the test if invalid rows exist in any column
        if any(~df[column].apply(is_valid_string).all() for column in columns_to_test):
            raise AssertionError("Invalid rows found. Details are logged in 'test_results_1.txt'.")
