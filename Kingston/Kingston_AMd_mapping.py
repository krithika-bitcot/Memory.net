
import re
import ast
import pandas as pd
import pytest

# ===============================================================
# Utility Functions
# ===============================================================
def norm(s):
    """Normalize string by making it lowercase, removing special chars and extra spaces."""
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_list(s):
    """Parse a string to a list, handling possible representations of lists."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return []
    if isinstance(s, list):
        return [x.strip() for x in s if isinstance(x, str)]
    s = str(s).strip()
    if not s:
        return []
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, (list, tuple)):
                return [str(i).strip() for i in obj if str(i).strip()]
        except Exception:
            pass
    return [p.strip() for p in re.split(r"[;,|\n]", s) if p.strip()]

# ---------- Matching Helpers ----------
def canonical_token(t):
    """
    Reduce a processor token to a canonical form for matching:
    - lowercases, strips symbols
    - removes generic suffix words (series/processors/processor/family/cpu)
    - collapses multiple spaces
    """
    if not isinstance(t, str):
        return ""
    t = t.lower().strip()
    t = t.replace("®", "").replace("™", "")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    noisy_suffixes = [
        " series", " processors", " processor", " family"
    ]
    for suf in noisy_suffixes:
        if t.endswith(suf):
            t = t[: -len(suf)].strip()

    t = re.sub(r"\s+", " ", t).strip()
    return t

def to_canonical_set(tokens):
    """Make a set of canonical tokens from a list; filter empties."""
    out = set()
    for tok in tokens or []:
        c = canonical_token(tok)
        if c:
            out.add(c)
    return out

def contains_match(cand, stack):
   
    if cand in stack:
        return True
    for h in stack:
        if cand in h or h in cand:
            return True
    return False

# ===============================================================
# Fixtures to load data
# ===============================================================
@pytest.fixture(scope="module")
def amd_df():
    path = "amd_mapped_with_kingston_extended_processor_chunks/amd_mapped_with_kingston_extended_processor_2.csv"
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)

    # Only AMD rows
    df = df[df["processor"].astype(str).str.contains("AMD", case=False)]

    # Normalize tokens
    df["amd_list"] = df["processor"].apply(parse_list)
    df["amd_norm"] = df["amd_list"].apply(lambda arr: [norm(x) for x in arr])

    # Normalize series
    df["series_raw"] = df["processor_series"].astype(str)
    df["series_norm"] = df["series_raw"].apply(norm)

    # Filter invalid series and empty processor lists
    df = df[df["series_norm"].notna() & (df["series_norm"] != "")]
    df = df[~df["series_norm"].isin(["nan", "none", "null"])]
    df = df[df["amd_norm"].apply(lambda x: len(x) > 0)]

    return df[["series_norm", "amd_norm"]]

@pytest.fixture(scope="module")
def kingston_df():
    path = "kingston_mapped_with_all_intel_products_chunks/kingston_mapped_with_all_intel_products_1.csv"
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)

    # Keep raw columns for reporting
    df["processor_series"] = df["processor_series"].astype(str)
    df["final_processor_data"] = df["final_processor_data"].astype(str)

    # Focus only on AMD rows
    df = df[df["final_processor_data"].str.contains("AMD", case=False)]

    # Parse and normalize the processor array
    df["ks_list"] = df["final_processor_data"].apply(parse_list)
    df["ks_norm"] = df["ks_list"].apply(lambda arr: [norm(x) for x in arr])

    # Normalize series
    df["series_raw"] = df["processor_series"].astype(str)
    df["series_norm"] = df["series_raw"].apply(norm)

    # Filter invalid series and empty processor lists
    df = df[df["series_norm"].notna() & (df["series_norm"] != "")]
    df = df[~df["series_norm"].isin(["nan", "none", "null"])]
    df = df[df["ks_norm"].apply(lambda x: len(x) > 0)]

    # Preserve original row position for traceability
    df = df[["processor_series", "final_processor_data", "series_norm", "ks_norm"]].copy()
    df.reset_index(inplace=True)
    df.rename(columns={"index": "row_id"}, inplace=True)
    return df

# ===============================================================
# Main Test using `request` to avoid pytest dumping huge fixtures
# ===============================================================
def test_amd_vs_kingston(request):

    # --- Fetch fixtures inside the test to prevent giant dumps in failure headers ---
    amd_df = request.getfixturevalue("amd_df")
    kingston_df = request.getfixturevalue("kingston_df")

    # ---------------------------
    # Build AMD maps (original + canonical) per series
    # ---------------------------
    amd_map = {}
    amd_canon_map = {}
    for _, r in amd_df.iterrows():
        key = r["series_norm"]
        if key:
            amd_map.setdefault(key, set()).update(r["amd_norm"])
            amd_canon_map.setdefault(key, set()).update(to_canonical_set(r["amd_norm"]))

    # ---------------------------
    # Missing processors per-row in Kingston (canonical fuzzy matching)
    # ---------------------------
    row_missing_report = []
    for _, r in kingston_df.iterrows():
        series = r["series_norm"]

        ks_canon_row = to_canonical_set(r["ks_norm"])
        amd_canon_for_series = amd_canon_map.get(series, set())
        amd_orig_for_series = sorted(amd_map.get(series, set()))
        canon_to_amd_orig = {canonical_token(a): a for a in amd_orig_for_series}

        missing_canon = []
        for a_c in sorted(amd_canon_for_series):
            if not contains_match(a_c, ks_canon_row):
                missing_canon.append(a_c)

        missing_display = [canon_to_amd_orig.get(c, c) for c in missing_canon]

        row_missing_report.append({
            "row_id": r["row_id"],
            "processor_series": r["processor_series"],
            "final_processor_data": r["final_processor_data"],
            "series_norm": series,
            "ks_norm": ", ".join(r["ks_norm"]),
            "missing_processors": ", ".join(missing_display),
            "missing_count": len(missing_display),
        })

    pd.DataFrame(row_missing_report).to_csv("kingston_missing_processors.csv", index=False)

    # ---------------------------
    # Duplicate processors per row (within Kingston's ks_norm list)
    # ---------------------------
    report_rows = []
    for _, r in kingston_df.iterrows():
        tokens = [t for t in r["ks_norm"] if isinstance(t, str)]
        seen, row_dupes = set(), set()
        for t in tokens:
            if t in seen:
                row_dupes.add(t)
            else:
                seen.add(t)

        duplicate_status = "Duplicates Found" if row_dupes else "No Duplicates"

        report_rows.append({
            "row_id": r["row_id"],
            "processor_series": r["processor_series"],
            "final_processor_data": r["final_processor_data"],
            "series_norm": r["series_norm"],
            "ks_norm": ", ".join(tokens),
            "duplicate_status": duplicate_status,
            "duplicates": ", ".join(sorted(row_dupes)) if row_dupes else "",
            "total_duplicate_tokens": len(row_dupes),
        })

    pd.DataFrame(report_rows).to_csv("kingston_row_duplicates.csv", index=False)

    # ---------------------------
    # Fail gracefully with clear terminal messages (no traceback)
    # ---------------------------
    rows_with_missing = [row for row in row_missing_report if row["missing_count"] > 0]
    rows_with_dupes   = [row for row in report_rows       if row["total_duplicate_tokens"] > 0]

    if rows_with_missing:
        print("\n Test Failed: Some Kingston rows are missing AMD processors for their series.")
        print("→ See detailed report: kingston_missing_processors.csv")
        print("Examples:")
        for row in rows_with_missing[:5]:
            print(f"  Row {row['row_id']} | Series: {row['series_norm']} | Missing: {row['missing_processors']}")
        assert False  # stop the test cleanly

    if rows_with_dupes:
        print("\n Test Failed: Some Kingston rows contain duplicate processors within the same row.")
        print("→ See detailed report: kingston_row_duplicates.csv")
        print("Examples:")
        for row in rows_with_dupes[:5]:
            print(f"  Row {row['row_id']} | Series: {row['series_norm']} | Duplicates: {row['duplicates']}")
        assert False  # stop the test cleanly