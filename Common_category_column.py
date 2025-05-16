import os
import pandas as pd
import pytest

# ─── CONFIG ───
# In‐code master brand‐to‐category mapping
MASTER_CATEGORIES = {
    'memory':       ['asus','axiom','cisco','crucial','dell','fujitsu','giga byte','hpe','kingston',
                     'lenovo','oracle','supermicro','serversupply','memory.net'],
    'ssd':          ['axiom','cisco','crucial','dell','dell- pdf','distech','fujitsu','hpe','intel',
                     'kingston','lenovo','mrmemory','samsung','vmware'],
    'hdd':          ['axiom','cisco','dell','dell- pdf','distech','fujitsu','hpe','lenovo',
                     'supermicro','serversupply','vmware'],
    'adapter':      ['dell','distech','hpe','oracle'],
    'hba':          ['dell','distech','hpe','oracle'],
    'optical_drives':['hpe'],
    'processor':    ['amd','dell','hpe','intel'],
    'gpu':          ['amd','intel'],
    'server':       ['asacomputer']
}

# Path to your test data (CSV or Excel)
TEST_FILE   = '06052025_cisco_db_import.csv'
OUTPUT_CSV  = 'missing_categories_report.csv'


# ─── HELPERS ───

def get_expected_categories(store: str) -> set[str]:
    """Return set of expected categories for 'store' from MASTER_CATEGORIES."""
    s = store.strip().lower()
    return {cat for cat, brands in MASTER_CATEGORIES.items() if s in brands}


def get_actual_categories(test_file_path: str) -> tuple[str, set[str]]:
    """
    Load CSV/XLS(X) and *only* use header names to find:
      - the column containing 'store'
      - the column containing 'cat'
    Normalize them and return (store_name, set(categories)).
    Raises ValueError if headers missing.
    """
    # 1) Load
    ext = os.path.splitext(test_file_path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(test_file_path, dtype=str, engine='openpyxl')
    else:
        df = pd.read_csv(test_file_path, dtype=str)

    # 2) Build map lowercase_header -> actual_header
    cols_lower = [c.strip().lower() for c in df.columns]
    name_to_col = dict(zip(cols_lower, df.columns))

    # 3) Find store column by header name containing 'store'
    store_candidates = [orig for lower, orig in name_to_col.items() if 'store' in lower]
    if not store_candidates:
        raise ValueError(f"No column with 'store' in header in {test_file_path}")
    store_col = store_candidates[0]

    # 4) Find category column by header name containing 'cat'
    cat_candidates = [orig for lower, orig in name_to_col.items() if 'cat' in lower]
    if not cat_candidates:
        raise ValueError(f"No column with 'cat' in header in {test_file_path}")
    category_col = cat_candidates[0]

    # 5) Subset & normalize
    subset = df[[store_col, category_col]].copy()
    subset.columns = ['store', 'category']
    subset['store']    = subset['store'].astype(str).str.strip().str.lower()
    subset['category'] = subset['category'].fillna('').astype(str).str.strip().str.lower()

    # 6) Extract
    store_value = subset['store'].iloc[0]
    actual_cats = set(subset['category'])
    actual_cats.discard('')  # drop blanks

    return store_value, actual_cats


def write_report(store: str, result: str):
    """Write a one‐row CSV with store and result."""
    pd.DataFrame([{'store': store, 'result': result}]) \
      .to_csv(OUTPUT_CSV, index=False)


# ─── THE TEST ───

def test_categories():
    store, actual = get_actual_categories(TEST_FILE)
    expected     = get_expected_categories(store)

    if   actual == expected:
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
