import os
import pandas as pd
import pytest

# ─── CONFIG ───
# Path to your master brands‐vs‐categories Excel file
BRANDS_CSV = 'Brands and their list - Sheet1.xlsx'  # actually an .xlsx zippable file
# Path to your test data (only store)
TEST_FILE = 'testdata.xlsx'
# Where to write the one‐row report
OUTPUT_CSV = 'missing_categories_report.csv'

# ─── HELPERS ───

def get_expected_categories(brands_excel_path: str, store: str) -> set[str]:
    """
    Invert the brands Excel (columns are category names; cells list brand names)
    and return the set of categories for the given store.
    """
    df = pd.read_excel(brands_excel_path, dtype=str, engine='openpyxl')
    store = store.strip().lower()
    expected = set()
    for col in df.columns:
        brands_in_col = (
            df[col]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
            .tolist()
        )
        if store in brands_in_col:
            expected.add(col.strip().lower())
    return expected


def get_actual_categories(test_file_path: str) -> tuple[str, set[str]]:
    """
    Load the test file, take the 1st column as 'store' and the 6th as 'category',
    normalize to lowercase, and return (store_name, set_of_unique_categories).
    """
    ext = os.path.splitext(test_file_path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(test_file_path, dtype=str, engine='openpyxl')
    else:
        df = pd.read_csv(test_file_path, dtype=str)

    df = df.iloc[:, [0, 5]].copy()
    df.columns = ['store', 'category']
    df['store'] = df['store'].astype(str).str.strip().str.lower()
    df['category'] = df['category'].fillna('').astype(str).str.strip().str.lower()

    store = df['store'].iloc[0]
    actual = set(df['category'])
    actual.discard('')  # remove empty strings
    return store, actual


def write_report(store: str, result: str):
    """Write a single‐row CSV with store and result."""
    pd.DataFrame([{'store': store, 'result': result}]) \
        .to_csv(OUTPUT_CSV, index=False)

# ─── THE TEST ───

def test_categories():
    store, actual = get_actual_categories(TEST_FILE)
    expected = get_expected_categories(BRANDS_CSV, store)

    # decide pass/fail + message
    if actual == expected:
        result = 'all pass'
    elif len(actual) < len(expected):
        missing = sorted(expected - actual)
        result = 'missing: ' + ', '.join(missing)
    elif len(actual) > len(expected):
        extra = sorted(actual - expected)
        result = 'extra: ' + ', '.join(extra)
    else:  # same length but elements differ
        result = 'category mismatch'

    # write CSV and assert
    write_report(store, result)
    assert actual == expected, result
