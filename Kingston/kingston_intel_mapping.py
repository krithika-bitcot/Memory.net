import os
import re
import ast
import time
import warnings
import pytest
import pandas as pd
from functools import lru_cache

#warnings.filterwarnings('ignore', category=FutureWarning)

try:
    import swifter  # type: ignore
    USE_SWIFTER = True
    print("Swifter available")
except Exception:
    USE_SWIFTER = False
    print("Swifter not available")
   

# Normalization helpers

@lru_cache(maxsize=1000)
def normalize_chipset_name(chipset: str) -> str:
    if not isinstance(chipset, str):
        return ""
    s = chipset.lower().strip().replace('®', '').replace('™', '')
    s = s.replace('/', ' ').replace('-', ' ').replace(',', ' ')
    noise = {'chipset', 'express', 'series', 'platform'}
    tokens = [t for t in s.split() if t not in noise]
    return ' '.join(tokens).strip()

def _extract_model_token(s: str) -> str:
    if not s:
        return ""
    m = re.search(r'\b([a-z]{1,2}\d{2,3})\b', s)
    return m.group(1) if m else ""

def chipset_key(s: str) -> str:
    token = _extract_model_token(s)
    return token if token else s

@lru_cache(maxsize=10000)
def normalize_processor_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    s = name.lower().strip().replace('®', '').replace('™', '')
    return ' '.join(s.split())

# For per-row duplicate detection

def dup_norm(name: str) -> str:
    return normalize_processor_name(name)

# --------------------
# Utils
# --------------------

def merge_processors_unique(series_of_lists):
    merged, seen = [], set()
    for lst in series_of_lists:
        if not isinstance(lst, list):
            continue
        for p in lst:
            n = normalize_processor_name(p)
            if n and n not in seen:
                seen.add(n)
                merged.append(p)
    return merged

def compute_unmatched_both_sides(intel_procs, kingston_procs):
    inorm = [normalize_processor_name(p) for p in intel_procs if isinstance(p, str) and p.strip()]
    knorm = [normalize_processor_name(p) for p in kingston_procs if isinstance(p, str) and p.strip()]
    i_set, k_set = set(inorm), set(knorm)
    intel_missing_norm = sorted(list(i_set - k_set))
    kingston_extra_norm = sorted(list(k_set - i_set))

    def backmap(norm_list, originals):
        rmap = {}
        for p in originals:
            n = normalize_processor_name(p)
            if n and n not in rmap:
                rmap[n] = p
        return [rmap.get(n, n) for n in norm_list]

    return backmap(intel_missing_norm, intel_procs), backmap(kingston_extra_norm, kingston_procs)

# Helper: detect server description column name from Kingston file (case-insensitive)

def detect_server_description_col(df: pd.DataFrame):
    candidates = {
        'server description', 'server_description', 'serverdesc',
        'server details', 'server_details', 'server-detail', 'server-desc',
        'server', 'system description', 'system_description'
    }
    lower_map = {c.lower().strip(): c for c in df.columns}
    for key in candidates:
        if key in lower_map:
            return lower_map[key]
    return None

# --------------------
# Loaders
# --------------------
@pytest.fixture(scope="module")
def intel_df():
    intel_file = "19052025_intel_processors (2).csv"
    if not os.path.exists(intel_file):
        pytest.fail(f" Intel file not found: {intel_file}")

    df = pd.read_csv(intel_file, low_memory=False)
    assert 'chipset' in df.columns and 'product_name' in df.columns, \
        "Intel CSV must contain 'chipset' and 'product_name'"

    df = df[df['chipset'].notna()]
    df = df[df['chipset'].astype(str).str.strip() != ""]
    df['chipset'] = df['chipset'].astype(str).str.strip().str.lower()

    grouped = (
        df.groupby('chipset', dropna=True)['product_name']
          .apply(list).reset_index()
          .rename(columns={'product_name': 'intel_processors'})
    )
    return grouped

@pytest.fixture(scope="module")
def kingston_df():
    kingston_file = "kingston_mapped_with_all_intel_products_1.csv"
    if not os.path.exists(kingston_file):
        pytest.fail(f" Kingston file not found: {kingston_file}")

    df = pd.read_csv(kingston_file, low_memory=False)
    assert 'chipset' in df.columns and 'final_processor_data' in df.columns, \
        "Kingston CSV must contain those columns memtioned"

    # Keep original server description col name (if any)
    server_desc_col = detect_server_description_col(df)
    df.attrs['server_desc_col'] = server_desc_col  # stash for later

    df = df[df['chipset'].notna()]
    df = df[df['chipset'].astype(str).str.strip() != ""]

    def parse_chipset(val):
        s = str(val).strip()
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list) and parsed:
                    return parsed[0]
            except Exception:
                pass
        return s

    df['chipset'] = df['chipset'].swifter.apply(parse_chipset) if USE_SWIFTER else df['chipset'].apply(parse_chipset)
    df = df[df['chipset'].notna()]
    df['chipset'] = df['chipset'].astype(str).str.strip().str.lower()

    def safe_eval(val):
        if pd.isna(val):
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            s = val.strip()
            if s == "":
                return []
            if s.startswith('[') and s.endswith(']'):
                try:
                    return ast.literal_eval(s)
                except Exception:
                    return [s]
            if s.startswith('(') and s.endswith(')'):
                try:
                    tup = ast.literal_eval(s)
                    return list(tup) if isinstance(tup, tuple) else [s]
                except Exception:
                    return [s]
            return [s]
        return [str(val)]

    df['final_processor_data'] = df['final_processor_data'].swifter.apply(safe_eval) if USE_SWIFTER else df['final_processor_data'].apply(safe_eval)

    df = df.reset_index().rename(columns={'index': 'kingston_row_index'})
    df['chipset_normalized'] = df['chipset'].apply(normalize_chipset_name)
    return df

# --------------------
# Main test
# --------------------

def test_compare_intel_and_kingston(intel_df, kingston_df):
    start = time.time()
    print("\n" + "=" * 80)
    print("Intel-Kingston Processor")
    print("=" * 80)

    # Normalize Intel chipsets
    intel_df['chipset_normalized'] = intel_df['chipset'].apply(normalize_chipset_name)

    # Map Intel chipsets to Kingston via model token
    intel_set = {c for c in set(intel_df['chipset_normalized']) if c}
    kingston_set = {c for c in set(kingston_df['chipset_normalized']) if c}
    ikey = {s: chipset_key(s) for s in intel_set}
    kkey = {s: chipset_key(s) for s in kingston_set}

    kidx = {}
    for s, k in kkey.items():
        kidx.setdefault(k, s)

    mapping = {i_norm: kidx[i_key] for i_norm, i_key in ikey.items() if i_key in kidx}
    if len(mapping) == 0:
        pytest.fail(" No chipset mappings created")

    intel_df['chipset_mapped'] = intel_df['chipset_normalized'].map(mapping)
    intel_df_mapped = intel_df[intel_df['chipset_mapped'].notna()].copy()
    if len(intel_df_mapped) == 0:
        pytest.fail(" No Intel rows mapped")

    # Aggregate Kingston processors per chipset (UNION unique)
    kingston_grouped = (
        kingston_df.groupby('chipset_normalized', dropna=True)['final_processor_data']
                   .apply(merge_processors_unique)
                   .reset_index()
                   .rename(columns={'chipset_normalized': 'chipset_normalized_k', 'final_processor_data': 'processor_agg'})
    )

    merged = pd.merge(
        intel_df_mapped,
        kingston_grouped,
        left_on='chipset_mapped',
        right_on='chipset_normalized_k',
        how='left'  # keep Intel even if Kingston side missing
    )

    print(f"Total mapped chipset rows in Intel: {len(merged)}")

    # Collectors
    per_row_missing_records = []   # will later be merged with all-rows duplicate info + server desc
    result_rows = []

    # Convenience grouping: Kingston rows by chipset
    k_rows_by_chipset = {k: g for k, g in kingston_df.groupby('chipset_normalized', dropna=True)}

    # Precompute duplicates for ALL Kingston rows (independent of mapping)
    dup_all_rows = []
    for _, kr in kingston_df.iterrows():
        plist = kr['final_processor_data'] if isinstance(kr['final_processor_data'], list) else []
        seen, row_dups = set(), []
        for p in plist:
            n = dup_norm(p)
            if not n:
                continue
            if n in seen:
                row_dups.append(p)
            else:
                seen.add(n)
        dup_all_rows.append({
            'kingston_row_index': int(kr['kingston_row_index']),
            'per_row_duplicate_count': len(row_dups),
            'per_row_duplicate_list': str(row_dups),
            'chipset_normalized': kr['chipset_normalized']
        })
    dup_all_df = pd.DataFrame(dup_all_rows)

    # Determine server description column name
    server_desc_col = kingston_df.attrs.get('server_desc_col', None)

    for _, row in merged.iterrows():
        chipset_intel_raw = row['chipset']
        chipset_norm_key = row['chipset_mapped']
        intel_procs = row['intel_processors']
        kingston_procs_agg = row.get('processor_agg', []) or []

        # Aggregated subset comparison
        intel_missing_list_agg, kingston_extra_list_agg = compute_unmatched_both_sides(intel_procs, kingston_procs_agg)

        # Per-row checks (missing + duplicates per-row) for MAPPED chipsets
        krows = k_rows_by_chipset.get(chipset_norm_key, pd.DataFrame())
        rows_total = len(krows)
        rows_all_empty = 0
        rows_with_missing = 0
        rows_with_duplicates = 0

        i_norm_set = {normalize_processor_name(p) for p in intel_procs if isinstance(p, str) and p.strip()}
        backmap = {normalize_processor_name(p): p for p in intel_procs if isinstance(p, str) and p.strip()}

        per_row_duplicate_accum = []

        if rows_total == 0:
            per_row_missing_records.append({
                'chipset_intel': chipset_intel_raw,
                'chipset_normalized': chipset_norm_key,
                'kingston_row_index': None,
                'kingston_row_has_data': False,
                'missing_count': len(i_norm_set),
                'missing_intel_processors': str([backmap[n] for n in sorted(list(i_norm_set))])
            })
        else:
            for _, krow in krows.iterrows():
                plist = krow['final_processor_data'] if isinstance(krow['final_processor_data'], list) else []

                # per-row duplicates (for mapped set roll-up)
                seen, row_dups = set(), []
                for p in plist:
                    n = dup_norm(p)
                    if not n:
                        continue
                    if n in seen:
                        row_dups.append(p)
                    else:
                        seen.add(n)
                if row_dups:
                    rows_with_duplicates += 1
                    per_row_duplicate_accum.extend(row_dups)

                # per-row missing
                k_norm_set = {normalize_processor_name(p) for p in plist if isinstance(p, str) and p.strip()}
                missing_norm = sorted(list(i_norm_set - k_norm_set))
                missing_originals = [backmap[n] for n in missing_norm]

                if len(plist) == 0:
                    rows_all_empty += 1
                if missing_norm:
                    rows_with_missing += 1

                per_row_missing_records.append({
                    'chipset_intel': chipset_intel_raw,
                    'chipset_normalized': chipset_norm_key,
                    'kingston_row_index': int(krow['kingston_row_index']) if 'kingston_row_index' in krow else None,
                    'kingston_row_has_data': len(plist) > 0,
                    'missing_count': len(missing_norm),
                    'missing_intel_processors': str(missing_originals)
                })

        matched_count_agg = max(0, len(intel_procs) - len(intel_missing_list_agg))
        match_pct_agg = round((matched_count_agg / len(intel_procs) * 100), 2) if intel_procs else 0.0

        violates_rule = (
            len(intel_missing_list_agg) > 0 or
            rows_total == 0 or
            rows_with_missing > 0 or
            rows_all_empty > 0 or
            rows_with_duplicates > 0
        )

        result_rows.append({
            'chipset_intel': chipset_intel_raw,
            'chipset_kingston': chipset_norm_key,
            'chipset_normalized': chipset_norm_key,
            'total_intel_processors': len(intel_procs),
            'total_kingston_processors_aggregated': len(kingston_procs_agg),
            'matched_count_aggregated': matched_count_agg,
            'missing_count_aggregated': len(intel_missing_list_agg),
            'match_percentage_aggregated': match_pct_agg,
            'violates_rule': violates_rule,
            'intel_processors': str(intel_procs),
            'kingston_processors_aggregated': str(kingston_procs_agg),
            'intel_missing_in_kingston_count': len(intel_missing_list_agg),
            'intel_missing_in_kingston_list': str(intel_missing_list_agg),
            'kingston_extra_count': len(kingston_extra_list_agg),
            'kingston_extra_list': str(kingston_extra_list_agg),
            'rows_total_for_chipset': int(rows_total),
            'rows_with_missing_cpus': int(rows_with_missing),
            'rows_all_empty_processors': int(rows_all_empty),
            'rows_with_duplicates': int(rows_with_duplicates),
            'per_row_duplicate_count': len(per_row_duplicate_accum),
            'per_row_duplicate_list': str(per_row_duplicate_accum),
        })

    # Build DataFrames
    result_df = pd.DataFrame(result_rows)

    # ---- Build the ALL-ROWS per-row output with duplicates and server description ----
    # Start from all Kingston rows
    per_row_all = kingston_df[['kingston_row_index', 'chipset', 'chipset_normalized']].copy()

    # Attach server description if present
    server_desc_col = kingston_df.attrs.get('server_desc_col', None)
    if server_desc_col and server_desc_col in kingston_df.columns:
        per_row_all['server_description'] = kingston_df[server_desc_col]
    else:
        per_row_all['server_description'] = None

    # Attach per-row duplicates for ALL rows
    per_row_all = per_row_all.merge(
        dup_all_df[['kingston_row_index', 'per_row_duplicate_count', 'per_row_duplicate_list']],
        on='kingston_row_index', how='left'
    )

    # Attach missing info we computed ONLY for mapped chipsets/rows
    per_row_missing_df = pd.DataFrame(per_row_missing_records)
    if not per_row_missing_df.empty:
        per_row_all = per_row_all.merge(
            per_row_missing_df[['kingston_row_index', 'chipset_intel', 'missing_count', 'missing_intel_processors', 'kingston_row_has_data']],
            on='kingston_row_index', how='left'
        )
    else:
        per_row_all['chipset_intel'] = None
        per_row_all['missing_count'] = pd.NA
        per_row_all['missing_intel_processors'] = pd.NA
        per_row_all['kingston_row_has_data'] = pd.NA

    # Save ONLY requested outputs
    result_df.to_csv('intel_kingston_comparison_result.csv', index=False)
    per_row_all.to_csv('missing_per_row_in_kingston.csv', index=False)

    # STRICT assertion (evaluate only on mapped chipsets)
    violations = result_df[result_df['violates_rule'] == True]
    assert len(violations) == 0, (
    
        "(aggregated missing and/or per-row missing/empty/no-data and/or per-row duplicates). "
    )

    
    print(f"Total time : {time.time() - start:.2f}s")

# Runner (optional)
if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
