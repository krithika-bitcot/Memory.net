import os
import csv
import ast
import pandas as pd
import pytest
from pandas.errors import EmptyDataError

def test_dimm_ranks_and_write_csv():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "03062025_cisco_db_import.csv")

    if not os.path.exists(csv_path):
        pytest.fail(f"CSV not found at {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except EmptyDataError:
        pytest.fail(f"No data found in CSV at {csv_path}")

    # normalize column names
    df.columns = df.columns.str.strip()

    # ensure required columns
    for col in ("option_part_no", "ranks", "rank_width", "dimm_ranks"):
        if col not in df.columns:
            pytest.fail(f"Missing required column '{col}' in CSV")

    # strip and convert types
    df["option_part_no"] = df["option_part_no"].astype(str).str.strip()
    df["dimm_ranks"]     = df["dimm_ranks"].astype(str).str.strip()
    df["ranks"]          = pd.to_numeric(df["ranks"], errors="coerce")
    df["rank_width"]     = pd.to_numeric(df["rank_width"], errors="coerce")

    report_rows = []
    validated_rows = []

    for part_no, group in df.groupby("option_part_no"):
        # expected combos
        valid_rs = group["ranks"].dropna().unique().astype(int)
        valid_ws = group["rank_width"].dropna().unique().astype(int)
        expected = {f"{r}Rx{w}" for r in valid_rs for w in valid_ws}

        # parse actual dimm_ranks into a flat set
        actual = set()
        for cell in group["dimm_ranks"].dropna().astype(str):
            if cell.lower() in ("nan", "", "[]"):
                continue
            try:
                lst = ast.literal_eval(cell)
            except Exception:
                lst = [cell]
            def _flatten(x):
                for i in x:
                    if isinstance(i, (list, tuple)):
                        yield from _flatten(i)
                    else:
                        yield str(i).strip().strip("'\"")
            for combo in _flatten(lst):
                c = combo.strip()
                if c and c.lower() != "nan":
                    actual.add(c)

        missing = sorted(expected - actual)
        extra   = sorted(actual - expected)
        status  = "PASS" if not missing and not extra else "FAIL"

        report_rows.append({
            "option_part_no": part_no,
            "missing": ",".join(missing),
            "extra": ",".join(extra),
            "status": status
        })

        if status == "PASS":
            # record matched combos for passed parts
            validated_rows.append({
                "option_part_no": part_no,
                "matched_combos": ",".join(sorted(expected))
            })

    # write full report
    report_path = os.path.join(base_dir, "dimm_ranks_report.csv")
    with open(report_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["option_part_no", "missing", "extra", "status"])
        writer.writeheader()
        writer.writerows(report_rows)

    # write only-validated file
    validated_path = os.path.join(base_dir, "validated_data.csv")
    with open(validated_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["option_part_no", "matched_combos"])
        writer.writeheader()
        writer.writerows(validated_rows)

    # fail if any mismatches
    fails = [r["option_part_no"] for r in report_rows if r["status"] == "FAIL"]
    if fails:
        pytest.fail(
            f"DIMM-ranks mismatches for option_part_no(s): {fails}\n"
            f"See '{os.path.basename(report_path)}' for details."
        )

    # on success, notify where validated data lives
    print(f"All parts passed. Validated data in '{os.path.basename(validated_path)}'")
