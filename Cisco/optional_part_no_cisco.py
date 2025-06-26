import re
import pytest
import pandas as pd
import os

# ─── 1. UPDATED VALIDATOR ───────────────────────────────────────────────────────

# Allows UCS or UCSX prefix, followed by zero or more segments of alphanumeric characters
# optionally prefixed by a hyphen. Disallows spaces, commas, dots, underscores, etc.
VALID_PART_NUM_RE = re.compile(r'''
    ^                         # start of string
    (?i:UCS(?:X)?)           # "UCS" or "UCSX", case-insensitive
    (?:-?[A-Za-z0-9]+)*       # zero or more segments: optional hyphen + alphanumerics
    $                         # end of string
''', re.VERBOSE)

def is_valid_optional_part_number(s: str) -> bool:
    """
    True if s is blank (optional) or matches our updated pattern:
      • Starts with UCS or UCSX
      • Contains only letters, digits, and optional hyphens
      • No spaces, commas, dots, underscores, etc.
    """
    if not s:
        # skip blank (optional field)
        return True
    return bool(VALID_PART_NUM_RE.fullmatch(s))


# Function to identify invalid part numbers (ending with H1, H2, RE1, etc.)
# def is_invalid_product_id(product_id: str) -> bool:
#     # Regex to find part numbers ending with H1, H2, or similar patterns
#     if re.search(r"-H\d+$", product_id):
#         return True
#     # Regex to find part numbers ending with RE1, RE2, or similar patterns
#     if re.search(r"RE\d+$", product_id):
#         return True
#     return False


# ─── 2. POWER-LIKE SUFFIXES DETECTOR ──────────────────────────────────────────

def looks_like_power_suffix(product_id: str) -> bool:
    """
    Flags product IDs that appear to have power-based or revision-related suffixes.
    Examples: -H1, RE1, RE2, W1, S4K1, RW1, RW2, KAM1, KL4K1, KL4KN1.
    """
    patterns = [
        r"-H\d+$",        # e.g., -H1, -H2
        r"RE\d+$",        # e.g., RE1, RE3
        r"W\d+$",         # e.g., W1, W2
        r"S\d+K\d+$",     # e.g., S4K1, S10K2
        r"[A-Z]\d+K\d+$", # e.g., T10K3, D12K1
        r"RW\d+$",        # e.g., RW1, RW2
        r"KAM\d+$",       # e.g., KAM1
        r"KL\d+[K|N]\d+$" # e.g., KL4K1, KL4KN1
    ]
    return any(re.search(p, product_id) for p in patterns)


# ─── 3. SMOKE TESTS BASED ON YOUR DATA ──────────────────────────────────────────

@pytest.mark.parametrize("pn, expected", [
    ("UCSX-MRX96G2RF3",   True),
    ("UCS-MR-X8G1RS-H",   True),
    ("UCSXSD960GBM3XEPD", True),  # no hyphens is now valid
    ("UCSXS960G6I1XEV-D", True),  # hyphen in segment
    ("UCSX-MRX96G2RF3,",  False), # trailing comma
    ("UCS-MR.X8G1RS-H",   False), # dot instead of hyphen
    ("UCS MR X8G1RS H",   False), # spaces
    ("UCSX_MRX96G2RF3",   False), # underscore
])
def test_validator_against_samples(pn, expected):
    assert is_valid_optional_part_number(pn) is expected


# ─── 4. FULL-COLUMN ASSERTION WITH REPORT ──────────────────────────────────────

@pytest.fixture
def df_option_parts():
    """
    Adjust this `path` to point at your actual file (CSV or Excel).
    The code will choose read_csv vs. read_excel automatically.
    """
    path = "03062025_cisco_db_import.csv"  # or "06052025_cisco_db_import.xlsx"
    ext = os.path.splitext(path)[1].lower()

    if ext == ".csv":
        return pd.read_csv(path)
    else:
        return pd.read_excel(path)


def test_all_option_part_numbers_in_excel(df_option_parts):
    """
    For every non-blank value in `option_part_no`,
    assert it matches our updated UCS/UCSX-hyphen-optional pattern.
    Invalid rows (if any) are written to a CSV report.
    """
    col = df_option_parts["option_part_no"].fillna("")  # Replace NaNs with empty string

    invalid_rows = []
    for idx, pn in col.items():
        if pn and not is_valid_optional_part_number(pn):
            invalid_rows.append({"row_index": idx, "option_part_no": pn, "reason": "Invalid format"})
        # elif pn and is_invalid_product_id(pn):
        #     invalid_rows.append({"row_index": idx, "option_part_no": pn, "reason": "Power-style suffix"})
        elif pn and looks_like_power_suffix(pn):
            invalid_rows.append({"row_index": idx, "option_part_no": pn, "reason": "Power-style suffix"})

    if invalid_rows:
        # Create a DataFrame for invalid rows and write to CSV
        report_df = pd.DataFrame(invalid_rows)
        report_df.to_csv("invalid_option_part_numbers_report.csv002", index=False)

    # Assert no invalid part numbers were found
    assert not invalid_rows, (
        f"Found {len(invalid_rows)} invalid part numbers. "
        "See invalid_option_part_numbers_report.csv for details."
    )
