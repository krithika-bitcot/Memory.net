import os
import csv
import ast
import pandas as pd
import pytest
import re
from pandas.errors import EmptyDataError

# 1) Point to the CSV once
CSV_PATH = os.path.join(os.path.dirname(__file__), "03062025_cisco_db_import.csv")

@pytest.fixture(scope="session")
def df():
    """
    Load the CSV into a DataFrame once per session.
    Skip all tests if mismatch or empty.
    """
    if not os.path.exists(CSV_PATH):
        pytest.skip(f"CSV not found at {CSV_PATH}")
    try:
        data = pd.read_csv(CSV_PATH)
    except EmptyDataError:
        pytest.skip(f"No data found in CSV at {CSV_PATH}")
    data.columns = data.columns.str.strip()
    return data

# 2) Helper: parse a Python‐literal or comma‐sep list into flat list of combos
def _parse_list(cell: str) -> list[str]:
    text = str(cell).strip()
    if not text or text.lower() in ("nan", "[]"):
        return []
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        # fallback: split on commas
        return [s.strip().strip("'\"") for s in text.split(",") if s.strip()]
    def _flatten(x):
        for item in x:
            if isinstance(item, (list, tuple)):
                yield from _flatten(item)
            else:
                yield str(item).strip().strip("'\"")
    return list(_flatten(parsed))

# Define the valid DIMM rank values based on the checkboxes
VALID_DIMM_RANKS = {"1Rx2", "1Rx4", "1Rx8", "2Rx4", "2Rx8", "4Rx4", "8Rx4"}

# Regular expression to strictly validate DIMM rank pattern like '1Rx2', '2Rx4', etc.
DIMM_RANK_PATTERN = re.compile(r'^\dRx\d$')  # Only allows one digit for rank and width

def _validate_dimm_ranks(dimm_ranks_list: list[str]) -> tuple[list[str], list[str]]:
    """
    Validate DIMM ranks against the valid set.
    Returns (valid_ranks, invalid_ranks)
    """
    valid_ranks = []
    invalid_ranks = []
    
    for rank in dimm_ranks_list:
        if rank in VALID_DIMM_RANKS:
            valid_ranks.append(rank)
        else:
            invalid_ranks.append(rank)
    
    return valid_ranks, invalid_ranks

def test_dimm_ranks_row_level(df: pd.DataFrame):
    """
    Row-by-row: Build exactly one expected "<rank>Rx<width>" per row,
    parse that row's dimm_ranks, and assert the expected pattern matches.
    Also validates all dimm_ranks against the valid set.
    Writes a combined output file with actual and expected columns.
    """
    # Ensure columns exist
    for col in ("server_description", "option_part_no", "ranks", "rank_width", "dimm_ranks"):
        assert col in df.columns, f"Missing required column '{col}'"
    
    report = []
    for idx, row in df.iterrows():
        part_no = str(row["option_part_no"]).strip()
        server_desc = str(row["server_description"]).strip()  # Capture the server description
        
        # Build expected pattern like "<rank>Rx<width>"
        try:
            r = int(float(row["ranks"]))
            w = int(float(row["rank_width"]))
            expected = f"{r}Rx{w}"
        except Exception:
            report.append({
                "row": idx,
                "server_description": server_desc,
                "option_part_no": part_no,
                "expected": "",
                "actual": "",
                "mismatch": "",
                "status": "SKIP"
            })
            continue

        # Parse dimm_ranks as a list and validate against valid set
        actual_list = _parse_list(row["dimm_ranks"])
        valid_ranks, invalid_ranks = _validate_dimm_ranks(actual_list)
        
        actual_set = set(actual_list)
        status = "PASS"
        mismatch = ""
        
        # Check for invalid ranks
        if invalid_ranks:
            status = "FAIL"
            mismatch = f"Invalid dimm_ranks found: {', '.join(invalid_ranks)}"
        
        # Check if expected pattern is present (only if no invalid ranks)
        if not invalid_ranks and expected not in actual_set:
            status = "FAIL"
            if mismatch:
                mismatch += f"; Expected '{expected}' not found in dimm_ranks"
            else:
                mismatch = f"Expected '{expected}' not found in dimm_ranks"
        
        report.append({
            "row": idx,
            "server_description": server_desc,
            "option_part_no": part_no,
            "expected": expected,
            "actual": ",".join(sorted(actual_set)),
            "mismatch": mismatch,
            "status": status
        })

    # Write the combined report to CSV
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_combined_report.csv")
    with open(out_path, "w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row", "server_description", "option_part_no", "expected", "actual", "mismatch", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any row has a FAIL status
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['option_part_no']}(row {r['row']})" for r in fails]
        pytest.fail(
            f"DIMM-ranks validation failed in rows: {parts}\n"
            f"See 'dimm_ranks_combined_report.csv' for details."
        )

def test_dimm_ranks_presence_in_server(df: pd.DataFrame):
    """
    Row-by-row: parse single‐value dimm_ranks and list‐value server_dimm_ranks,
    assert every dimm_rank appears in the server list.
    Validates both dimm_ranks and server_dimm_ranks against the valid set.
    Checks for duplicates in server_dimm_ranks and writes a combined output file.
    """
    # Ensure columns exist
    for col in ("dimm_ranks", "server_dimm_ranks", "server_description"):
        assert col in df.columns, f"Missing required column '{col}'"

    # Initialize the report
    report = []

    # Iterate through each row
    for idx, row in df.iterrows():
        dimm_list = _parse_list(row["dimm_ranks"])
        server_dimm_ranks = _parse_list(row["server_dimm_ranks"])
        server_desc = str(row["server_description"]).strip()  # Capture the server description

        # Validate dimm_ranks against valid set
        valid_dimm_ranks, invalid_dimm_ranks = _validate_dimm_ranks(dimm_list)
        
        # Validate server_dimm_ranks against valid set
        valid_server_ranks, invalid_server_ranks = _validate_dimm_ranks(server_dimm_ranks)
        
        dimm_set = set(valid_dimm_ranks)  # Only use valid dimm_ranks for comparison
        server_set = set(valid_server_ranks)  # Only use valid server_dimm_ranks for comparison

        status = "PASS"
        issues = []

        # Check for invalid entries in dimm_ranks
        if invalid_dimm_ranks:
            status = "FAIL"
            issues.append(f"Invalid dimm_ranks: {', '.join(invalid_dimm_ranks)}")

        # Check for invalid entries in server_dimm_ranks
        if invalid_server_ranks:
            status = "FAIL"
            issues.append(f"Invalid server_dimm_ranks: {', '.join(invalid_server_ranks)}")

        # Check if all valid dimm_ranks are contained in valid server_dimm_ranks
        mismatch = dimm_set - server_set
        if mismatch:
            status = "FAIL"
            issues.append(f"dimm_ranks not in server_dimm_ranks: {', '.join(mismatch)}")

        # Check for duplicates in the server_dimm_ranks
        duplicate_ranks = [item for item in server_dimm_ranks if server_dimm_ranks.count(item) > 1]
        if duplicate_ranks:
            status = "FAIL"
            issues.append(f"Duplicates in server_dimm_ranks: {', '.join(set(duplicate_ranks))}")

        report.append({
            "row": idx,
            "server_description": server_desc,
            "dimm_ranks": ",".join(sorted(dimm_list)),
            "server_dimm_ranks": ",".join(sorted(server_dimm_ranks)),
            "invalid_dimm_ranks": ",".join(sorted(invalid_dimm_ranks)) if invalid_dimm_ranks else "",
            "invalid_server_ranks": ",".join(sorted(invalid_server_ranks)) if invalid_server_ranks else "",
            "issues": "; ".join(issues) if issues else "",
            "status": status
        })

    # Write the combined report to CSV
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_combined_report.csv")
    with open(out_path, "w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row", "server_description", "dimm_ranks", "server_dimm_ranks", 
                       "invalid_dimm_ranks", "invalid_server_ranks", "issues", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any row has a FAIL status
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        pytest.fail(
            f"DIMM ranks validation failed in the following rows: {', '.join(str(r['row']) for r in fails)}\n"
            f"See 'dimm_ranks_combined_report.csv' for details."
        )
