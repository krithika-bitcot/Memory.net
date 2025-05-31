#!/usr/bin/env python3
"""
test_and_report.py

Standalone script that:
 1. Loads "my_data.csv" (place in the same folder as this script).
 2. For each row, computes calculate_dimm_rank(row).
 3. Automatically derives the “expected” value using the same rule:
      - If both 'ranks' and 'rank_width' are non-missing, expected = f"{int(ranks)}Rx{int(rank_width)}"
      - Otherwise expected = NaN
 4. Compares computed vs. expected, marking each row as PASSED or FAILED.
 5. Writes a per-row report to "test_report.csv" in the same folder.

Usage:
    1. Put your CSV file named "my_data.csv" in this script’s directory.
       The CSV must have columns exactly named "ranks" and "rank_width".
    2. Run:
         python test_and_report.py
    3. Inspect "test_report.csv" for pass/fail per row.
"""

import os
import sys
import csv
import numpy as np
import pandas as pd

def calculate_dimm_rank(row):
    """
    From a row with 'ranks' and 'rank_width', build a string like "1Rx4".
    If either value is missing (NaN), return np.nan.
    """
    if pd.notna(row.get("ranks")) and pd.notna(row.get("rank_width")):
        return f"{int(row['ranks'])}Rx{int(row['rank_width'])}"
    return np.nan

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, "06052025_cisco_db_import.csv")

    if not os.path.isfile(csv_path):
        print(f"ERROR: Could not find '06052025_cisco_db_import.csv' in {here}")
        sys.exit(1)

    # Load the CSV into a DataFrame
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"ERROR: Failed to read 'my_data.csv': {e}")
        sys.exit(1)

    # Ensure the CSV has the required columns
    missing_cols = [col for col in ("ranks", "rank_width") if col not in df.columns]
    if missing_cols:
        print(f"ERROR: CSV is missing required column(s): {missing_cols}")
        sys.exit(1)

    # If your CSV has stray spaces in its headers, uncomment:
    # df.columns = df.columns.str.strip()

    total_rows = len(df)
    report_rows = []
    pass_count = 0
    fail_count = 0

    for idx, row in df.iterrows():
        # Compute actual using our function
        actual = calculate_dimm_rank(row)

        # Derive expected programmatically:
        if pd.notna(row["ranks"]) and pd.notna(row["rank_width"]):
            expected = f"{int(row['ranks'])}Rx{int(row['rank_width'])}"
        else:
            expected = np.nan

        # Compare
        if isinstance(expected, str):
            passed = (actual == expected)
            exp_str = expected
            actual_str = actual if isinstance(actual, str) else repr(actual)
        else:
            # expected is NaN
            passed = pd.isna(actual)
            exp_str = "NaN"
            actual_str = "NaN" if pd.isna(actual) else repr(actual)

        status = "PASSED" if passed else "FAILED"
        if passed:
            pass_count += 1
        else:
            fail_count += 1

        report_rows.append({
            "row_index": idx,
            "ranks": row["ranks"],
            "rank_width": row["rank_width"],
            "expected": exp_str,
            "actual": actual_str,
            "status": status
        })

    # Write report to CSV
    report_path = os.path.join(here, "test_report.csv")
    try:
        with open(report_path, "w", newline="") as csvfile:
            fieldnames = ["row_index", "ranks", "rank_width", "expected", "actual", "status"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in report_rows:
                writer.writerow(r)
    except Exception as e:
        print(f"ERROR: Failed to write 'test_report.csv': {e}")
        sys.exit(1)

    # Print summary
    print(f"Tested {total_rows} rows → {pass_count} passed, {fail_count} failed.")
    print(f"Report written to: {report_path}")

if __name__ == "__main__":
    main()
