import os
import re
from typing import List, Tuple
import pandas as pd

# -------------------------
# FILE CONFIGURATION - UPDATE THESE PATHS
# -------------------------
SOURCE_CSV = "acer_mapping_servers_only.csv"    # Your source file
OUTPUT_CSV = "validation_results.csv"           # Output file name  
DESTINATION_CSV = "acer_servers_only.csv"       # Your destination file

# -------------------------
# Config & constants
# -------------------------
PROCESSORS_OF_INTEREST = [
    'Intel Xeon', 'Intel Pentium', 'Intel Core', 'Intel Celeron', 'Intel Celeron Dual Core',
    'AMD Sempron', 'AMD Ryzen', 'AMD Ryzen 3 Pro', 'AMD Ryzen 5 Pro', 'AMD Ryzen 7 Pro',
    'AMD E-Series', 'AMD A-Series', 'AMD EPYC', 'AMD C-Series', 'AMD Athlon'
]

KEEP_INTACT = {
    "AMD A-Series APU (FM2+) AMD A10-series",
    "(N AMD A8-7410 (N",
    "A) AMD A8-7410 A)",
    "(N AMD A4-5000 (N",
    "AMD A-Series APU AMD A4-5000 A)",
    "AMD A-Series APU AMD A4-5000 (N",
    "Intel Pentium Intel Pentium B940 (N/A)",
    "VIA C7 "
}

# -------------------------
# Text utilities - IMPROVED
# -------------------------

def _std_colnames(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase and strip whitespace"""
    df.columns = df.columns.str.strip().str.lower()
    return df


def _clean_text(s: str) -> str:
    """Clean text by removing extra whitespace and normalize case"""
    if not isinstance(s, str):
        s = "" if pd.isna(s) else str(s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_list_string(s: str) -> str:
    """Normalize comma-separated list string - FIXED to handle case properly"""
    if not isinstance(s, str):
        s = "" if pd.isna(s) else str(s)
    parts = [_clean_text(p) for p in s.split(',') if _clean_text(p)]
    # Remove duplicates while preserving original case but sorting case-insensitively
    unique_parts = []
    seen_lower = set()
    for part in parts:
        part_lower = part.lower()
        if part_lower not in seen_lower:
            unique_parts.append(part)
            seen_lower.add(part_lower)
    
    # Sort case-insensitively but preserve original case
    unique_parts.sort(key=str.lower)
    return ", ".join(unique_parts)


def _contains_interest(text: str) -> bool:
    """Check if text contains any processor of interest"""
    if pd.isna(text) or not isinstance(text, str):
        return False
    return any(k in text for k in PROCESSORS_OF_INTEREST)


def _has_meaningful_chipset(chipset_value: str) -> bool:
    """Check if chipset value is meaningful (not empty or placeholder)"""
    if pd.isna(chipset_value) or not isinstance(chipset_value, str):
        return False
    cleaned = chipset_value.strip()
    if not cleaned:
        return False
    # Consider empty string, "N/A", or very short values as not meaningful
    if cleaned.lower() in ['n/a', 'na', '', 'none']:
        return False
    return len(cleaned) > 1

# -------------------------
# Splitting rules
# -------------------------

def normalize_ryzen_variants(processor_string: str) -> str:
    """Normalize AMD Ryzen processor variants"""
    if not isinstance(processor_string, str) or 'AMD Ryzen' not in processor_string:
        return processor_string
    entries = [entry.strip() for entry in processor_string.split(',')]
    normalized = []
    last_gen = None
    for entry in entries:
        match_full = re.match(r"AMD Ryzen\s+(\d)\s+(PRO\s+)?\w+", entry)
        match_pro_only = re.match(r"AMD Ryzen\s+(PRO\s+\w+)", entry)
        if match_full:
            last_gen = match_full.group(1)
            normalized.append(entry)
        elif match_pro_only and last_gen:
            normalized.append(f"AMD Ryzen {last_gen} {match_pro_only.group(1)}")
        else:
            normalized.append(entry)
    return ', '.join(normalized)


def split_processor_chipset(processor_string: str) -> pd.Series:
    """Split processor string into processor and chipset components"""
    if pd.isna(processor_string):
        return pd.Series({'processor': "", 'chipset': ""})
    if processor_string in KEEP_INTACT:
        return pd.Series({'processor': processor_string, 'chipset': ""})
    
    # (N/A) + Intel/AMD (not Cedar) → treat as chipset
    if re.match(r"^\(N/A\)\s+(Intel|AMD) (?!Cedar\b)", processor_string, re.IGNORECASE):
        return pd.Series({'processor': "", 'chipset': processor_string})

    # Two or more occurrences of Intel/AMD → split at last occurrence
    count_intel_amd = len(re.findall(r"\b(Intel|AMD)\b", processor_string, re.IGNORECASE))
    if count_intel_amd >= 2:
        matches = list(re.finditer(r"\b(Intel|AMD)\b", processor_string, re.IGNORECASE))
        last = matches[-1]
        return pd.Series({
            'processor': processor_string[:last.start()].strip(),
            'chipset': processor_string[last.start():].strip(),
        })

    # Single Intel/AMD occurrence not at start → split into (prefix, token..)
    single = re.search(r"\b(Intel|AMD)\b", processor_string, re.IGNORECASE)
    if single and single.start() > 0:
        return pd.Series({
            'processor': processor_string[:single.start()].strip(),
            'chipset': processor_string[single.start():].strip(),
        })

    # Otherwise leave as-is
    return pd.Series({'processor': processor_string, 'chipset': ""})


def split_processors(processor_string: str) -> List[str]:
    """Split processors and remove trailing Intel chipsets"""
    if isinstance(processor_string, list):
        return processor_string
    processor_string = "" if pd.isna(processor_string) else str(processor_string)
    if not processor_string.strip():
        return [processor_string]

    # Remove trailing Intel Hxx/Qxx/Zxx tokens when present in the same string
    chipset_pat = r"\bIntel\s+[A-Z]\d{2,3}\b"
    m = re.search(chipset_pat, processor_string)
    if m:
        processor_string = processor_string.replace(m.group(0), '').strip()
    return [processor_string]


def _final_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Final cleaning of processor and chipset columns"""
    if 'chipset' in df.columns:
        df['chipset'] = (
            df['chipset'].astype(str)
            .str.replace("(N/A)", "", regex=False)
            .str.replace("(N", "", regex=False)
            .str.replace("A)", "", regex=False)
            .apply(_clean_text)
        )
    if 'processor' in df.columns:
        df['processor'] = (
            df['processor'].astype(str)
            .str.replace("(N/A)", "", regex=False)
            .str.replace("(N", "", regex=False)
            .str.replace("A)", "", regex=False)
            .apply(_clean_text)
        )
    return df

# -------------------------
# Main processing functions
# -------------------------

def process_source_csv(source_csv: str) -> pd.DataFrame:
    """Process the source CSV file and return cleaned/split data"""
    print(f"Reading source CSV: {source_csv}")
    src = pd.read_csv(source_csv)
    src = _std_colnames(src)

    # Ensure processor column exists
    if 'processor' not in src.columns:
        raise ValueError("Source CSV must have a 'processor' column")

    print(f"Initial rows: {len(src)}")
    
    # Filter to only processors of interest
    src = src[src['processor'].apply(_contains_interest)]
    print(f"Rows after filtering for processors of interest: {len(src)}")

    # Prepare processor text and explode quoted splits
    src['processor'] = src['processor'].astype(str).str.replace("(N/A)", "", regex=False).str.strip()
    src['processor'] = src['processor'].str.split("'")
    src = src.explode('processor')
    src = src[~src['processor'].astype(str).str.strip().eq(',')]
    src = src[~src['processor'].astype(str).str.contains(r'\[|\]', na=False)]

    # Split into processor and chipset components
    split_df = src['processor'].apply(split_processor_chipset)
    src['processor_split'] = split_df['processor']
    
    # Only update chipset if it doesn't exist or is empty - FIXED LOGIC
    if 'chipset' not in src.columns:
        src['chipset'] = split_df['chipset']
    else:
        # Only fill empty chipset values, preserve existing ones
        mask = src['chipset'].fillna('').astype(str).apply(lambda x: not _has_meaningful_chipset(x))
        src.loc[mask, 'chipset'] = split_df.loc[mask, 'chipset']

    # Normalize and expand processors
    src['processor'] = src['processor_split'].apply(normalize_ryzen_variants)
    src['processor'] = src['processor'].apply(split_processors)
    src = src.explode('processor')
    if 'processor_split' in src.columns:
        src = src.drop(columns=['processor_split'])

    # Final cleaning
    src = _final_clean(src)

    # Group by key columns and aggregate processors
    group_cols = ['option_part_no', 'server_description', 'chipset']
    for c in group_cols:
        if c not in src.columns:
            src[c] = ''
    
    grouped = (
        src.groupby(group_cols, as_index=False)
           .agg({'processor': lambda x: ', '.join(sorted(set(_clean_text(v) for v in x if _clean_text(v))))})
           .drop_duplicates()
    )
    
    print(f"Final grouped rows: {len(grouped)}")
    return grouped


def compare_with_destination(processed_source: pd.DataFrame, dest_csv: str = None) -> pd.DataFrame:
    """Compare processed source with destination CSV if provided - IMPROVED matching with FIXED chipset validation"""
    if dest_csv and os.path.exists(dest_csv):
        print(f"Reading destination CSV: {dest_csv}")
        dest = pd.read_csv(dest_csv)
        dest = _std_colnames(dest)
        
        # Handle common typo in column name
        if 'all_amd_processsor' in dest.columns and 'all_amd_processor' not in dest.columns:  
            dest = dest.rename(columns={'all_amd_processsor': 'all_amd_processor'})
        
        # Clean destination data BEFORE merging
        for col in ['chipset', 'all_amd_processor']:
            if col not in dest.columns:
                dest[col] = ''
        
        dest['chipset'] = dest['chipset'].fillna('').astype(str).apply(_clean_text)
        dest['all_amd_processor'] = dest['all_amd_processor'].fillna('').astype(str).apply(_clean_text)
        
        # Ensure merge keys exist and are clean
        key_cols = ['option_part_no', 'server_description', 'chipset']
        for c in key_cols:
            if c not in dest.columns:
                dest[c] = ''
            if c not in processed_source.columns:
                processed_source[c] = ''
            # Clean merge keys
            dest[c] = dest[c].fillna('').astype(str).apply(_clean_text)
            processed_source[c] = processed_source[c].fillna('').astype(str).apply(_clean_text)
        
        # Debug: Print merge key info
        print(f"Source rows: {len(processed_source)}")
        print(f"Destination rows: {len(dest)}")
        
        # Merge and compare
        merged = processed_source.merge(dest, on=key_cols, how='left', suffixes=('_src', '_dest'))
        merged = merged.rename(columns={'processor': 'processor_src'})
        
        print(f"Merged rows: {len(merged)}")
        print(f"Rows with destination data: {len(merged.dropna(subset=['all_amd_processor']))}")
        
        # Ensure we use the correctly processed data for normalization
        merged['processor_src_norm'] = merged['processor_src'].fillna('').apply(_norm_list_string)
        merged['all_amd_processor_norm'] = merged['all_amd_processor'].fillna('').apply(_norm_list_string)

        # FIXED validation logic - only check chipset if source has meaningful chipset data
        def validate_row(row):
            src_proc = row.get('processor_src_norm', '').strip()
            dst_proc = row.get('all_amd_processor_norm', '').strip()
            src_chip = row.get('chipset', '').strip()  # Source chipset
            reasons = []
            
            # Check if destination row exists (from merge)
            if pd.isna(row.get('all_amd_processor')):
                return 'NO_MATCH', 'No matching row found in destination'
            
            # FIXED: Only check for missing chipset if source actually has chipset data
            if _has_meaningful_chipset(src_chip):
                # Source has chipset data, so we should validate it exists in destination
                # Note: chipset is already part of merge key, so if we matched, chipsets should align
                pass  # Chipset validation is handled by the merge logic
            
            # Always check for processor data
            if not dst_proc:
                reasons.append('Missing all_amd_processor in destination')
                
            # Smart processor comparison that handles format differences
            if src_proc and dst_proc:
                # Normalize both to sets of individual processors for comparison
                src_procs = set(p.strip().lower() for p in src_proc.split(','))
                dst_procs = set(p.strip().lower() for p in dst_proc.split(','))
                
                if src_procs == dst_procs:
                    return 'PASS', ''
                else:
                    # Check if it's just a format difference (slash vs comma)
                    # Convert source format: "Intel Core i5 12400/12500" -> {"intel core i5 12400", "intel core i5 12500"}
                    src_expanded = set()
                    for proc in src_procs:
                        if '/' in proc:
                            # Handle slash-delimited format like "intel core i5 12400/12500"
                            parts = proc.split('/')
                            if len(parts) == 2:
                                base = parts[0].strip()
                                suffix = parts[1].strip()
                                # Find common prefix
                                base_words = base.split()
                                if len(base_words) >= 3:  # e.g. "intel core i5"
                                    prefix = ' '.join(base_words[:-1])
                                    src_expanded.add(base.lower())
                                    src_expanded.add(f"{prefix} {suffix}".lower())
                                else:
                                    src_expanded.add(proc.lower())
                            else:
                                # More than 2 parts, split all
                                base_parts = proc.split('/')
                                if len(base_parts[0].split()) >= 3:
                                    prefix = ' '.join(base_parts[0].split()[:-1])
                                    for part in base_parts:
                                        if part == base_parts[0]:
                                            src_expanded.add(part.lower())
                                        else:
                                            src_expanded.add(f"{prefix} {part}".lower())
                                else:
                                    src_expanded.add(proc.lower())
                        else:
                            src_expanded.add(proc.lower())
                    
                    # Compare expanded source with destination
                    if src_expanded == dst_procs:
                        return 'PASS', 'Matched after slash expansion'
                    else:
                        # Still different - this is a real mismatch
                        missing_in_dst = src_expanded - dst_procs
                        extra_in_dst = dst_procs - src_expanded
                        details = []
                        if missing_in_dst:
                            details.append(f"Missing in dest: {', '.join(sorted(missing_in_dst))}")
                        if extra_in_dst:
                            details.append(f"Extra in dest: {', '.join(sorted(extra_in_dst))}")
                        reasons.append(f'Processor content mismatch: {"; ".join(details)}')
                        
            if not reasons and not src_proc and not dst_proc:
                return 'PASS', 'Both empty'
                
            return ('FAIL' if reasons else 'PASS', '; '.join(reasons))

        validation_results = merged.apply(lambda r: pd.Series(validate_row(r)), axis=1)
        merged[['test_result', 'reason']] = validation_results
        
        return merged
    else:
        # No destination file, just return processed source with additional columns for consistency
        processed_source['test_result'] = 'NO_COMPARISON'
        processed_source['reason'] = 'No destination file provided'
        processed_source['processor_src_norm'] = processed_source['processor'].apply(_norm_list_string)
        return processed_source

def process_and_validate_csv(source_csv: str, output_csv: str, dest_csv: str = None): 
    """Main function to process source CSV and generate output"""
    
    try:
        if not os.path.exists(source_csv):
            raise FileNotFoundError(f"Source CSV file not found: {source_csv}")
        
        # Process source CSV
        processed_data = process_source_csv(source_csv)
        
        # Compare with destination if provided
        results = compare_with_destination(processed_data, dest_csv)
        
        # Prepare output columns
        output_columns = [
            'option_part_no', 'server_description', 'chipset',
            'processor_src_norm', 'test_result', 'reason'
        ]
        
        # Add destination columns if they exist
        if 'all_amd_processor' in results.columns:
            output_columns.insert(-2, 'all_amd_processor')
            output_columns.insert(-2, 'all_amd_processor_norm')
        
        # Ensure all columns exist
        for col in output_columns:
            if col not in results.columns:
                results[col] = ''
        
        # Save results
        results[output_columns].to_csv(output_csv, index=False)
        
        # Print detailed summary
        if dest_csv and os.path.exists(dest_csv):
            failed = int((results['test_result'] == 'FAIL').sum())
            passed = int((results['test_result'] == 'PASS').sum())
            no_match = int((results['test_result'] == 'NO_MATCH').sum())
            total = len(results)
            print(f"\n VALIDATION RESULTS:")
            print(f" PASSED: {passed}")
            print(f" FAILED: {failed}")
            print(f" NO_MATCH: {no_match}")
            print(f" TOTAL:  {total}")
            
            # Show some failed examples for debugging
            if failed > 0:
                print(f"\n First 3 failures:")
                fail_examples = results[results['test_result'] == 'FAIL'].head(3)
                for idx, row in fail_examples.iterrows():
                    print(f"  Row {idx}: {row['reason']}")
                    print(f"    Source: '{row.get('processor_src_norm', '')}'")
                    print(f"    Dest:   '{row.get('all_amd_processor_norm', '')}'")
                    print()
                    
            # Show some no-match examples if they exist
            if no_match > 0:
                print(f"\n First 3 no-matches:")
                no_match_examples = results[results['test_result'] == 'NO_MATCH'].head(3)
                for idx, row in no_match_examples.iterrows():
                    print(f"  Part: {row['option_part_no']}")
                    print(f"    Server: {row.get('server_description', '')}")
                    print(f"    Source Chipset: '{row.get('chipset', '')}'")
                    print()
        else:
            print(f"\n Processed {len(results)} rows from source CSV")
        
        print(f"\n Results saved to: {output_csv}")
        
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    print("=== CSV Processor (FIXED Chipset Validation) ===")                                      
    print(f" Source CSV: {SOURCE_CSV}")
    print(f" Output CSV: {OUTPUT_CSV}")
    print(f" Destination CSV: {DESTINATION_CSV if DESTINATION_CSV else 'None (no comparison)'}")
    print()
    
    success = process_and_validate_csv(SOURCE_CSV, OUTPUT_CSV, DESTINATION_CSV)
    
    if success:
        print("\n Processing completed successfully!")
    else:
        print("\n Processing failed!")