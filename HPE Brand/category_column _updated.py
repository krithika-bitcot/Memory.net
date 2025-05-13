import os
import pandas as pd

# ─── CONFIG ───
# In-code master brand-to-category mapping (no external Excel file needed)
MASTER_CATEGORIES = {
    'memory': [
        'asus', 'axiom', 'cisco', 'crucial', 'dell', 'fujitsu',
        'giga byte', 'hpe', 'kingston', 'lenovo', 'oracle',
        'supermicro', 'serversupply', 'memory.net'
    ],
    'ssd': [
        'axiom', 'cisco', 'crucial', 'dell', 'dell- pdf', 'distech',
        'fujitsu', 'hpe', 'intel', 'kingston', 'lenovo',
        'mrmemory', 'samsung', 'vmware'
    ],
    'hdd': [
        'axiom', 'cisco', 'dell', 'dell- pdf', 'distech', 'fujitsu',
        'hpe', 'lenovo', 'supermicro', 'serversupply', 'vmware'
    ],
    'adapter': ['dell', 'distech', 'hpe', 'oracle'],
    'hba': ['dell', 'distech', 'hpe', 'oracle'],
    'optical_drives': ['hpe'],
    'processor': ['amd', 'dell', 'hpe', 'intel'],
    'gpu': ['amd', 'intel'],
    'server': ['asacomputer']
}

# Path to your test data (store data CSV or Excel)
TEST_FILE = '06052025_cisco_db_import.csv'
# Where to write the one-row report
OUTPUT_CSV = 'missing_categories_report.csv'

# ─── HELPERS ───

def get_expected_categories(store: str) -> set[str]:
    """
    Return the set of expected categories for the given store
    based on the in-code MASTER_CATEGORIES mapping.
    """
    store_clean = store.strip().lower()
    expected = {
        category
        for category, brands in MASTER_CATEGORIES.items()
        if store_clean in brands
    }
    return expected


def get_actual_categories(test_file_path: str) -> tuple[str, set[str]]:
    """
    Dynamically load the test file (Excel or CSV), detect 'store' and 'category'
    columns by header name, normalize to lowercase, and return
    (store_name, set_of_unique_categories).
    """
    # Load file
    ext = os.path.splitext(test_file_path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(test_file_path, dtype=str, engine='openpyxl')
    else:
        df = pd.read_csv(test_file_path, dtype=str)

    # Map lowercase header names to original columns
    cols_lower = [c.strip().lower() for c in df.columns]
    name_to_col = dict(zip(cols_lower, df.columns))

    # Determine store column
    store_col = name_to_col.get('store', df.columns[0])
    # Determine category column (any header containing 'cat')
    cat_candidates = [orig for lower, orig in name_to_col.items() if 'cat' in lower]
    category_col = cat_candidates[0] if cat_candidates else df.columns[-1]

    # Subset and normalize
    subset = df[[store_col, category_col]].copy()
    subset.columns = ['store', 'category']
    subset['store'] = subset['store'].astype(str).str.strip().str.lower()
    subset['category'] = subset['category'].fillna('').astype(str).str.strip().str.lower()

    # Extract values
    store_value = subset['store'].iloc[0]
    actual_cats = set(subset['category'])
    actual_cats.discard('')
    return store_value, actual_cats


def write_report(store: str, result: str):
    """Write a single-row CSV with store and result."""
    pd.DataFrame([{'store': store, 'result': result}])\
      .to_csv(OUTPUT_CSV, index=False)

# ─── THE TEST ───

def test_categories():
    store, actual = get_actual_categories(TEST_FILE)
    expected = get_expected_categories(store)

    if actual == expected:
        result = 'all pass'
    elif actual < expected:
        missing = sorted(expected - actual)
        result = 'missing: ' + ', '.join(missing)
    elif actual > expected:
        extra = sorted(actual - expected)
        result = 'extra: ' + ', '.join(extra)
    else:
        result = 'category mismatch'

    write_report(store, result)
    assert actual == expected, result
    # The test will fail if the actual categories do not match the expected ones