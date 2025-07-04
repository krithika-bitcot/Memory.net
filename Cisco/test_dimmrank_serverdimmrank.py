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
    Skip all tests if missing or empty.
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
                "missing": "",
                "status": "SKIP"
            })
            continue

        # Parse dimm_ranks as a list and check for expected pattern match
        actual_set = set(_parse_list(row["dimm_ranks"]))
        
        # Check if the expected pattern is within the parsed dimm_ranks
        if any(re.fullmatch(rf"{r}Rx{w}", item) for item in actual_set):
            status = "PASS"
            missing = ""
        else:
            status = "FAIL"
            missing = expected
        
        report.append({
            "row": idx,
            "option_part_no": part_no,
            "expected": expected,
            "actual": ",".join(sorted(actual_set)),
            "missing": missing,
            "status": status
        })

    # Write the row-level report
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_row_report.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row", "option_part_no", "expected", "actual", "missing", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any row has a FAIL status
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['option_part_no']}(row {r['row']})" for r in fails]
        pytest.fail(
            f"DIMM-ranks missing in rows: {parts}\n"
            f"See 'dimm_ranks_row_report.csv' for details."
        )


def test_dimm_ranks_presence_in_server(df):
    """
    Row-by-row: parse single‐value dimm_ranks and list‐value server_dimm_ranks,
    assert every dimm_rank appears in the server list.
    Writes dimm_ranks_server_report.csv.
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
        missing_ranks = set()

        # Check for missing DIMM ranks in each row for the given server description
        for idx, row in group.iterrows():
            dimm_set = set(_parse_list(row["dimm_ranks"]))  # Set of all DIMM ranks for this row
            
            missing = dimm_set - server_dimm_ranks_set  # Check if any dimm_ranks are missing in server_dimm_ranks
            if missing:
                missing_ranks.update(missing)  # Collect all missing ranks

        # Log results for the current server
        if missing_ranks:
            status = "FAIL"
        else:
            status = "PASS"
        
        report.append({
            "server_description": server_desc,
            "missing": ",".join(sorted(missing_ranks)) if missing_ranks else "",
            "status": status
        })

    # Write the result report to CSV
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_server_report.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["server_description", "missing", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any server description has missing DIMM ranks
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['server_description']}" for r in fails]
        pytest.fail(
            f"DIMM ranks missing in the following server descriptions: {parts}\n"
            f"See 'dimm_ranks_server_report.csv' for details."
        )
# Note: The original code snippet provided was not complete and did not include the full context of the test.
# The above code is a complete test function that checks DIMM ranks in a server context.