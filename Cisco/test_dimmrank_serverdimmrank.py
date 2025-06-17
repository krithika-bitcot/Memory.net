import os
import csv
import ast
import pandas as pd
import pytest
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
    Row‐by‐row: build exactly one expected "<rank>Rx<width>" per row,
    parse that row’s dimm_ranks, and assert the expected appears.
    Writes dimm_ranks_row_report.csv.
    """
    # ensure columns
    for col in ("option_part_no", "ranks", "rank_width", "dimm_ranks"):
        assert col in df.columns, f"Missing required column '{col}'"

    report = []
    for idx, row in df.iterrows():
        part_no = str(row["option_part_no"]).strip()
        # build expected combo
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

        actual_set = set(_parse_list(row["dimm_ranks"]))
        status = "PASS" if expected in actual_set else "FAIL"
        missing = "" if status == "PASS" else expected

        report.append({
            "row": idx,
            "option_part_no": part_no,
            "expected": expected,
            "actual": ",".join(sorted(actual_set)),
            "missing": missing,
            "status": status
        })

    # write the row‐level report
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_row_report.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row","option_part_no","expected","actual","missing","status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # fail on any FAIL
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['option_part_no']}(row {r['row']})" for r in fails]
        pytest.fail(
            f"DIMM-ranks missing in rows: {parts}\n"
            f"See 'dimm_ranks_row_report.csv' for details."
        )

def test_dimm_ranks_presence_in_server(df):
    """
    Row‐by‐row: parse single‐value dimm_ranks and list‐value server_dimm_ranks,
    assert every dimm_rank appears in the server list.
    Writes dimm_ranks_server_report.csv.
    """
    # Ensure columns exist
    for col in ("server_description", "dimm_ranks", "server_dimm_ranks"):
        assert col in df.columns, f"Missing required column '{col}'"

    # Initialize the report
    report = []

    # Row-by-row check
    for idx, row in df.iterrows():
        dimm_set   = set(_parse_list(row["dimm_ranks"]))
        server_set = set(_parse_list(row["server_dimm_ranks"]))

        missing = dimm_set - server_set
        status = "PASS" if not missing else "FAIL"

        report.append({
            "row": idx,
            "server_description": row["server_description"],
            "dimm_ranks": ",".join(sorted(dimm_set)),
            "server_dimm_ranks": ",".join(sorted(server_set)),
            "missing": ",".join(sorted(missing)) if missing else "",
            "status": status
        })

    # Write the result report
    out_path = os.path.join(os.path.dirname(__file__), "dimm_ranks_server_report.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["row", "server_description", "dimm_ranks", "server_dimm_ranks", "missing", "status"]
        )
        writer.writeheader()
        writer.writerows(report)

    # Fail if any row has a FAIL status
    fails = [r for r in report if r["status"] == "FAIL"]
    if fails:
        parts = [f"{r['server_description']}(row {r['row']})" for r in fails]
        pytest.fail(
            f"DIMM-ranks missing in rows: {parts}\n"
            f"See 'dimm_ranks_server_report.csv' for details."
        )