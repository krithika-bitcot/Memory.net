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

# Define the valid DIMM rank values based on the checkboxes, excluding "(Blanks)"
VALID_DIMM_RANKS = {"1Rx2", "1Rx4", "1Rx8", "2Rx4", "2Rx8", "4Rx4", "8Rx4"}

# Update the helper function to exclude "(Blanks)" during validation
def _validate_dimm_ranks(ranks: set) -> bool:
    """
    Validate that all DIMM ranks are in the predefined list of valid ranks, 
    excluding "(Blanks)".
    """
    # Filter out "(Blanks)" and check if remaining values are valid
    ranks = {rank for rank in ranks if rank != "(Blanks)"}
    return all(rank in VALID_DIMM_RANKS for rank in ranks)

def test_dimm_ranks_row_level(df):
    """
    Row-by-row: Build exactly one expected "<rank>Rx<width>" per row,
    parse that row’s dimm_ranks, and assert the expected pattern matches.
    Writes dimm_ranks_row_report.csv.
    """
    # Ensure columns exist
    for col in ("option_part_no", "ranks", "rank_width", "dimm_ranks"):
        assert col in df.columns, f"Missing required column '{col}'"
    
    report = []
    for idx, row in df.iterrows():
        part_no = str(row["option_part_no"]).strip()
        
        # Build expected pattern like "<rank>Rx<width>"
        try:
            r = int(float(row["ranks"]))
            w = int(float(row["rank_width"]))
            expected = f"{r}Rx{w}"
        except Exception:
            report.append({
                "row": idx,
                "option_part_no": part_no,
                "expected": "",
                "actual": "",
                "mismatch": "",
                "status": "SKIP"
            })
            continue

        # Parse dimm_ranks as a list and check for expected pattern match
        actual_set = set(_parse_list(row["dimm_ranks"]))
        
        # Validate that the parsed dimm_ranks are in the valid set, excluding "(Blanks)"
        if not _validate_dimm_ranks(actual_set):
            status = "FAIL"
            mismatch = f"Invalid dimm_ranks: {', '.join(actual_set)}"
        elif any(re.fullmatch(rf"{r}Rx{w}", item) for item in actual_set):
            status = "PASS"
            mismatch = ""
        else:
            status = "FAIL"
            mismatch = expected
        
        report.append({
            "row": idx,
            "option_part_no": part_no,
            "expected": expected,
            "actual": ",".join(sorted(actual_set)),
            "mismatch": mismatch,
            "status": status
        })

    # Write the row-level report
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_row_report.csv")
    with open(out_path, "w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row", "option_part_no", "expected", "actual", "mismatch", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any row has a FAIL status
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['option_part_no']}(row {r['row']})" for r in fails]
        pytest.fail(
            f"DIMM-ranks mismatch or invalid entries in rows: {parts}\n"
            f"See 'dimm_ranks_row_report.csv' for details."
        )


def test_dimm_ranks_presence_in_server(df):
    """
    Row-by-row: parse single‐value dimm_ranks and list‐value server_dimm_ranks,
    assert every dimm_rank appears in the server list.
    Checks for duplicates in server_dimm_ranks and writes dimm_ranks_server_report.csv.
    """
    # Ensure columns exist
    for col in ("server_description", "dimm_ranks", "server_dimm_ranks"):
        assert col in df.columns, f"Missing required column '{col}'"

    # Initialize the report
    report = []

    # Group the data by server description and process each group
    for server_desc, group in df.groupby("server_description"):
        # For each server, extract all DIMM ranks for this server
        server_dimm_ranks_set = set(_parse_list(group["server_dimm_ranks"].iloc[0]))  # Assuming same server_dimm_ranks across rows
        mismatch_ranks = set()
        duplicate_ranks = set()

        # Check for mismatch DIMM ranks in each row for the given server description
        for idx, row in group.iterrows():
            dimm_set = set(_parse_list(row["dimm_ranks"]))  # Set of all DIMM ranks for this row
            server_dimm_ranks = _parse_list(row["server_dimm_ranks"])

            # Validate that the dimm_ranks are in the valid set, excluding "(Blanks)"
            if not _validate_dimm_ranks(dimm_set):
                mismatch_ranks.update(dimm_set)
            
            # Check for duplicates in the server_dimm_ranks
            duplicates = [item for item in server_dimm_ranks if server_dimm_ranks.count(item) > 1]
            if duplicates:
                duplicate_ranks.update(duplicates)  # Collect duplicate ranks

            # Check for mismatch DIMM ranks in the server_dimm_ranks
            mismatch = dimm_set - server_dimm_ranks_set  # Check if any dimm_ranks are mismatch in server_dimm_ranks
            if mismatch:
                mismatch_ranks.update(mismatch)  # Collect all mismatch ranks

        # Log results for the current server
        if mismatch_ranks or duplicate_ranks:
            status = "FAIL"
        else:
            status = "PASS"

        report.append({
            "server_description": server_desc,
            "mismatch": ",".join(sorted(mismatch_ranks)) if mismatch_ranks else "",
            "duplicates": ",".join(sorted(duplicate_ranks)) if duplicate_ranks else "",
            "status": status,
            "actual_data": ",".join(sorted(_parse_list(group["server_dimm_ranks"].iloc[0])))  # Include actual server dimm_ranks data
        })

    # Write the result report to CSV
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_server_report.csv")
    with open(out_path, "w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["server_description", "mismatch", "duplicates", "status", "actual_data"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any server description has mismatch DIMM ranks or duplicates
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['server_description']}" for r in fails]
        pytest.fail(
            f"DIMM ranks mismatch or duplicates in the following server descriptions: {parts}\n"
            f"See 'dimm_ranks_server_report.csv' for details."
        )
