import re
import pytest
import pandas as pd

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


# ─── 2. SMOKE TESTS BASED ON YOUR DATA ──────────────────────────────────────────

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


# ─── 3. FULL-COLUMN ASSERTION WITH REPORT ──────────────────────────────────────

@pytest.fixture
def df_option_parts():
    # adjust this path to your actual XLSX file
    return pd.read_excel("06052025_cisco_db_import.xlsx")


def test_all_option_part_numbers_in_excel(df_option_parts):
    """
    For every non-blank value in `option_part_no`,
    assert it matches our updated UCS/UCSX-hyphen-optional pattern.
    Invalid rows (if any) are written to a CSV report.
    """
    col = df_option_parts["option_part_no"].fillna("")

    invalid_rows = []
    for idx, pn in col.items():
        if pn and not is_valid_optional_part_number(pn):
            invalid_rows.append({"row_index": idx, "option_part_no": pn})

    if invalid_rows:
        report_df = pd.DataFrame(invalid_rows)
        report_df.to_csv("invalid_option_part_numbers_report.csv", index=False)

    assert not invalid_rows, (
        f"Found {len(invalid_rows)} invalid part numbers. "
        "See invalid_option_part_numbers_report.csv for details."
    )
