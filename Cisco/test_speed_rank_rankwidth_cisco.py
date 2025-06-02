#!/usr/bin/env python3
"""
validate_speed_ranks_rankwidth.py

Standalone script that:
 1. Loads "06052025_cisco_db_import.xlsx" (or CSV if renamed) from the same directory.
 2. Checks, for each row:
    - That 'speed', 'ranks', and 'rank_width' exist as columns.
    - That 'speed', 'ranks', and 'rank_width' are numeric (or NaN).
    - That no negative values appear in those three columns (NaN is allowed).
 3. Writes a per-row report to "test_report_speed_rank_rankwidth.csv" in the same folder.

Usage:
    1. Place this script and the file "06052025_cisco_db_import.xlsx" (or .csv) in the same directory.
    2. Install dependencies if necessary:
         pip install pandas numpy openpyxl
    3. Run:
         python validate_speed_ranks_rankwidth.py
    4. Inspect "test_report_speed_rank_rankwidth.csv" to see row-by-row PASS/FAIL.
"""

import os
import sys
import csv
import numpy as np
import pandas as pd

# ────────────────────────────────────────────────────────────────
# (1) Load the Excel/CSV file
# ────────────────────────────────────────────────────────────────

FILENAME = "06052025_cisco_db_import.xlsx"
REPORT_FILENAME = "test_report_speed_rank_rankwidth.csv"

def load_input_file(fn: str) -> pd.DataFrame:
    """
    Load the given file (Excel or CSV) into a pandas DataFrame.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, fn)

    if not os.path.isfile(path):
        print(f"ERROR: Could not find '{fn}' in {here}")
        sys.exit(1)

    if fn.lower().endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(path)
        except Exception as e:
            print(f"ERROR: Failed to read Excel '{fn}': {e}")
            sys.exit(1)
    else:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"ERROR: Failed to read CSV '{fn}': {e}")
            sys.exit(1)

    return df

# ────────────────────────────────────────────────────────────────
# (2) Column‐existence check (one‐time)
# ────────────────────────────────────────────────────────────────

def check_columns_exist(df: pd.DataFrame):
    """
    Verify that 'speed', 'ranks', and 'rank_width' exist as columns.
    Returns (bool, message). If missing, bool=False and message lists them.
    """
    required = ["speed", "ranks", "rank_width"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return False, f"Missing column(s): {missing}"
    return True, ""

# ────────────────────────────────────────────────────────────────
# (3) Per‐row checks
# ────────────────────────────────────────────────────────────────

def is_numeric_or_nan(df: pd.DataFrame, col: str):
    """
    Return True if df[col] has a numeric dtype (ints, floats, or pandas Nullable Int/Float),
    or if the entire column is NaN. Otherwise False.
    """
    return pd.api.types.is_numeric_dtype(df[col])

def check_no_negative_value(val):
    """
    Return True if val is NaN or val >= 0. Otherwise False.
    """
    if pd.isna(val):
        return True
    return val >= 0

# ────────────────────────────────────────────────────────────────
# (4) Main logic: run checks and write report
# ────────────────────────────────────────────────────────────────

def main():
    # Load the DataFrame
    df = load_input_file(FILENAME)
    total_rows = len(df)

    # Check that required columns exist
    col_exist_pass, col_exist_msg = check_columns_exist(df)
    if not col_exist_pass:
        # If columns are missing, write a single‐row report and exit
        here = os.path.dirname(os.path.abspath(__file__))
        rpt_path = os.path.join(here, REPORT_FILENAME)
        with open(rpt_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["check", "status", "details"]
            )
            writer.writeheader()
            writer.writerow({
                "check": "test_columns_exist",
                "status": "FAILED",
                "details": col_exist_msg
            })
        print(f"ERROR: {col_exist_msg}")
        print(f"Report written to {rpt_path}")
        sys.exit(1)

    # Prepare per-row report
    report_rows = []
    for idx, row in df.iterrows():
        # Initialize the dictionary for this row
        row_report = {
            "row_index": idx,
            "speed": row.get("speed", np.nan),
            "ranks": row.get("ranks", np.nan),
            "rank_width": row.get("rank_width", np.nan),
            # Sub-check results (PASS or FAIL):
            "speed_is_numeric": "",
            "speed_non_negative": "",
            "ranks_is_numeric": "",
            "ranks_non_negative": "",
            "rank_width_is_numeric": "",
            "rank_width_non_negative": "",
            "overall_status": ""
        }

        # 1) speed_is_numeric
        if is_numeric_or_nan(df, "speed"):
            row_report["speed_is_numeric"] = "PASS"
        else:
            row_report["speed_is_numeric"] = "FAIL"

        # 2) speed_non_negative
        if check_no_negative_value(row["speed"]):
            row_report["speed_non_negative"] = "PASS"
        else:
            row_report["speed_non_negative"] = "FAIL"

        # 3) ranks_is_numeric
        if is_numeric_or_nan(df, "ranks"):
            row_report["ranks_is_numeric"] = "PASS"
        else:
            row_report["ranks_is_numeric"] = "FAIL"

        # 4) ranks_non_negative
        if check_no_negative_value(row["ranks"]):
            row_report["ranks_non_negative"] = "PASS"
        else:
            row_report["ranks_non_negative"] = "FAIL"

        # 5) rank_width_is_numeric
        if is_numeric_or_nan(df, "rank_width"):
            row_report["rank_width_is_numeric"] = "PASS"
        else:
            row_report["rank_width_is_numeric"] = "FAIL"

        # 6) rank_width_non_negative
        if check_no_negative_value(row["rank_width"]):
            row_report["rank_width_non_negative"] = "PASS"
        else:
            row_report["rank_width_non_negative"] = "FAIL"

        # Determine overall_status: PASS only if all six sub-checks are PASS
        sub_checks = [
            row_report["speed_is_numeric"],
            row_report["speed_non_negative"],
            row_report["ranks_is_numeric"],
            row_report["ranks_non_negative"],
            row_report["rank_width_is_numeric"],
            row_report["rank_width_non_negative"]
        ]
        row_report["overall_status"] = (
            "PASSED" if all(ch == "PASS" for ch in sub_checks) else "FAILED"
        )

        report_rows.append(row_report)

    # Write the per-row report CSV
    here = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(here, REPORT_FILENAME)

    with open(report_path, "w", newline="") as csvfile:
        fieldnames = [
            "row_index",
            "speed",
            "ranks",
            "rank_width",
            "speed_is_numeric",
            "speed_non_negative",
            "ranks_is_numeric",
            "ranks_non_negative",
            "rank_width_is_numeric",
            "rank_width_non_negative",
            "overall_status"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in report_rows:
            writer.writerow(r)

    # Print a brief summary
    passed_count = sum(1 for r in report_rows if r["overall_status"] == "PASSED")
    failed_count = total_rows - passed_count
    print(f"Completed {total_rows} rows → {passed_count} PASSED, {failed_count} FAILED.")
    print(f"Report written to: {report_path}")

if __name__ == "__main__":
    main()
