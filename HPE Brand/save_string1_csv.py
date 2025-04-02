import pandas as pd
import pytest
       
# Validation function
def is_valid_alphabet(value):
    """
    Function to validate that a value contains only alphabets.
    """
    return isinstance(value, str) and value.isalpha()

@pytest.fixture
def load_csv():
    """Fixture to load the CSV file into a DataFrame."""
    file_path = "Memory.net\chunk_1.csv"  # Path to your test CSV file
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Ensure no extra spaces in column names
    return df

def test_alphabet_columns(load_csv):
    """Test and log results for specific columns containing only alphabetic values."""
    df = load_csv

    # Columns to validate
    columns_to_test = ['store', 'A', 'B']

    # Prepare a list to hold results
    results = []

    for column in columns_to_test:
        # Check if the column exists
        assert column in df.columns, f"Column '{column}' not found in the CSV file."

        # Separate valid and invalid rows
        valid_rows = df[df[column].apply(is_valid_alphabet)]
        invalid_rows = df[~df[column].apply(is_valid_alphabet)]

        # Collect results for the column
        for value in valid_rows[column]:
            results.append({"column_name": column, "value_type": "valid", "value": value})

        for index, row in invalid_rows.iterrows():
            results.append({"column_name": column, "value_type": "invalid", "value": row[column]})

    # Convert results into a DataFrame
    result_df = pd.DataFrame(results)

    # Write results to CSV
    result_df.to_csv("test_results_1.csv", index=False)

    # Always fail the test if invalid rows exist in any column
    if any(~df[column].apply(is_valid_alphabet).all() for column in columns_to_test):
        raise AssertionError("Invalid rows found. Details are logged in 'test_results_1.csv'.")
