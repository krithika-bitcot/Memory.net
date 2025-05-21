import os
import re
import pandas as pd
import pytest

# ─── CONFIG ───
# In-code brand→required-columns mapping (all keys & values lowercase)
MASTER_RULES = {
    'asus': [
        'host_image_url', 'host_url', 'server_description', 'server_specification',
        'store', 'dimm_slots', 'maximum_memory', 'part_description', 'processor',
        'a', 'b', 'c', 'encode_status', 'memory_sku', 'capacity', 'speed',
        'ranks', 'rank_width', 'memory_type', 'dimm_type', 'ecc', 'voltage',
        'height', 'qty', 'category', 'part_url'
    ],
    'axiom': [
        'store', 'a', 'b', 'c', 'server_description', 'category', 'option_part_no',
        'part_description', 'oem', 'mfr_part_no', 'part_specification', 'memory',
        'ssd', 'hdd', 'processor', 'dimm_slots', 'maximum_memory', 'maximum_rdimm',
        'maximum_lrdimm', 'maximum_sodimm', 'maximum_udimm', 'encode_status',
        'capacity', 'speed', 'ranks', 'rank_width', 'memory_type', 'dimm_type',
        'ecc', 'voltage', 'height', 'qty', 'interface', 'form_factor',
        'sequential_read', 'sequential_write', 'random_read', 'random_write',
        'dwpd', 'part_image_url', 'host_url', 'part_url', 'capacity_in_tb',
        'capacity_in_gb', 'dimensions', 'product_id'
    ],
    'cisco': [
        'store', 'option_part_no', 'server_description', 'a', 'b', 'c',
        'part_description', 'dimm_slots', 'maximum_memory', 'maximum_rdimm',
        'maximum_lrdimm', 'maximum_udimm', 'maximum_sodimm', 'category',
        'processor', 'memory', 'ssd', 'hdd', 'capacity', 'speed', 'ranks',
        'rank_width', 'memory_type', 'dimm_type', 'ecc', 'voltage', 'height',
        'qty', 'interface', 'form_factor', 'encode_status', 'file_name',
        'host_url', 'part_url', 'capacity_in_tb', 'capacity_in_gb', 'product_id',
        'dimm_ranks', 'server_dimm_ranks', 'mfr_part_no', 'spare_part_no',
        'oem', 'model'
    ],
    'crucial': [
        'store', 'a', 'b', 'c', 'server_description', 'category', 'part_number',
        'part_description', 'part_specification', 'server_specification',
        'configuration_notes', 'memory', 'ssd', 'processor', 'dimm_slots',
        'maximum_memory', 'storage_support', 'memory_specification', 'encode_status',
        'speed', 'ranks', 'rank_width', 'memory_type', 'dimm_type', 'ecc',
        'voltage', 'qty', 'part_image_url', 'host_url', 'part_url', 'capacity',
        'capacity_in_gb', 'capacity_in_tb', 'dimensions', 'form_factor', 'height',
        'interface', 'memory_sku'
    ],
    'dell': [
        'store', 'a', 'b', 'c', 'server_description', 'category', 'mfr_part_no',
        'part_description', 'part_specification', 'server_specification', 'oem',
        'memory', 'ssd', 'processor', 'hba', 'adapter', 'compatibility',
        'dimm_slots', 'maximum_memory', 'product_id', 'memory_specification',
        'maximum_lrdimm', 'maximum_rdimm', 'maximum_udimm', 'maximum_sodimm',
        'encode_status', 'configuration_notes', 'capacity', 'capacity_in_tb',
        'capacity_in_gb', 'speed', 'ranks', 'rank_width', 'memory_type',
        'dimm_type', 'ecc', 'voltage', 'height', 'qty', 'interface',
        'form_factor', 'dimensions', 'server_dimm_ranks', 'dimm_ranks',
        'part_image_url', 'host_url', 'part_url', 'gen_series', 'gen'
    ],
    'fujitsu': [
        'store', 'a', 'b', 'c', 'server_description', 'category', 'part_description',
        'server_specification', 'product_id', 'processor', 'dimm_slots',
        'maximum_udimm', 'maximum_sodimm', 'maximum_lrdimm', 'maximum_rdimm',
        'maximum_memory', 'capacity', 'speed', 'ranks', 'rank_width',
        'memory_type', 'dimm_type', 'ecc', 'voltage', 'height', 'qty',
        'interface', 'form_factor', 'capacity_in_tb', 'capacity_in_gb',
        'encoded_status', 'file_name', 'file_urls', 'host_image_url', 'host_url',
        'part_url'
    ],
    'giga byte': [
        'server_description', 'server_specification', 'host_image_url', 'host_url',
        'store', 'part_description', 'dimm_slots', 'processor', 'a', 'b', 'c',
        'encode_status', 'product_id', 'category', 'capacity', 'speed', 'ranks',
        'rank_width', 'memory_type', 'dimm_type', 'ecc', 'voltage', 'height',
        'qty', 'part_url'
    ],
    'hpe': [
        'store', 'a', 'b', 'c', 'option_part_no', 'server_description',
        'part_description', 'category', 'product_id', 'dimm_slots',
        'maximum_memory', 'maximum_rdimm', 'maximum_lrdimm', 'maximum_udimm',
        'maximum_sodimm', 'processor', 'memory', 'ssd', 'hdd', 'adapter', 'hba',
        'optical_drives', 'capacity', 'speed', 'ranks', 'rank_width',
        'memory_type', 'dimm_type', 'ecc', 'voltage', 'height', 'qty',
        'processor_sockets', 'capacity_in_tb', 'capacity_in_gb', 'form_factor',
        'interface', 'dimensions', 'server_specification', 'storage',
        'server_form_factor', 'chassis', 'dimm_ranks', 'server_dimm_ranks',
        'file_name', 'host_url', 'part_url', 'gen'
    ],
    'kingston': [
        'store', 'a', 'b', 'c', 'server_description', 'server_form_factor',
        'category', 'option_part_no', 'part_description', 'part_specification',
        'server_specification', 'configuration_notes', 'memory', 'ssd',
        'dimm_slots', 'processor_sockets', 'maximum_memory', 'storage_support',
        'ssd_sku', 'memory_specification', 'encode_status', 'capacity',
        'capacity_in_tb', 'capacity_in_gb', 'speed', 'ranks', 'rank_width',
        'memory_type', 'dimm_type', 'ecc', 'voltage', 'height', 'qty',
        'interface', 'form_factor', 'dimensions', 'part_image_url', 'host_url',
        'part_url', 'product_id', 'dimm_ranks', 'server_dimm_ranks',
        'chipset', 'processor', 'processor_max_memory_speed'
    ],
    'lenovo': [
        'server_description', 'server_specification', 'a', 'b', 'c', 'processor',
        'gpu', 'memory', 'ssd', 'hdd', 'dimm_slots', 'memory_channels',
        'maximum_memory', 'maximum_udimm', 'maximum_sodimm', 'maximum_lrdimm',
        'maximum_rdimm', 'storage_support', 'mfr_part_no', 'category',
        'part_description', 'speed', 'ranks', 'rank_width', 'memory_type',
        'dimm_type', 'ecc', 'voltage', 'height', 'qty', 'encode_status',
        'part_image_url', 'host_image_url', 'file_url', 'api_url', 'part_url',
        'host_url', 'store', 'capacity', 'capacity_in_gb', 'capacity_in_tb',
        'dimensions', 'form_factor', 'interface', 'product_id', 'gen'
    ],
    'oracle': [
        'store', 'part_number', 'memory_sku', 'server_description', 'a', 'b', 'c',
        'part_description', 'dimm_slots', 'maximum_memory', 'maximum_rdimm',
        'maximum_lrdimm', 'maximum_udimm', 'maximum_sodimm', 'category',
        'processor', 'memory', 'ssd', 'hdd', 'hba', 'adapter', 'optical_drives',
        'capacity', 'speed', 'ranks', 'rank_width', 'memory_type', 'dimm_type',
        'ecc', 'voltage', 'height', 'qty', 'encode_status', 'file_name',
        'host_url', 'part_url'
    ],
    'supermicro': [
        'store', 'a', 'b', 'c', 'server_description', 'category', 'option_part_no',
        'part_description', 'oem', 'mfr_part_no', 'part_specification',
        'server_specification', 'processor', 'memory', 'ssd', 'hdd', 'dimm_slots',
        'maximum_memory', 'storage_support', 'memory_specification', 'encode_status',
        'speed', 'ranks', 'rank_width', 'memory_type', 'dimm_type', 'ecc',
        'voltage', 'height.1', 'qty', 'host_url', 'part_url', 'dimensions',
        'height', 'product_id', 'model', 'sequential_read', 'sequential_write',
        'random_read', 'random_write', 'dwpd', 'form_factor', 'interface',
        'capacity', 'capacity_in_gb', 'capacity_in_tb'
    ],
    'serversupply': [
        'store', 'part_description', 'category', 'mfr_part_no', 'manufacturer',
        'part_specification', 'memory', 'ssd', 'hhd', 'processor', 'dimm_slots',
        'maximum_memory', 'storage_support', 'product_id', 'encode_status',
        'capacity', 'speed', 'ranks', 'rank_width', 'memory_type', 'dimm_type',
        'ecc', 'voltage', 'height', 'qty', 'part_url'
    ],
    'memory.net': [
        'a', 'b', 'c', 'dimm_slots', 'maximum_memory', 'processor',
        'server_description', 'store'
    ],
    'samsung': [
        'store', 'category', 'mfr_part_no', 'model', 'interface', 'form_factor',
        'capacity', 'sequential_read', 'sequential_write', 'random_read',
        'random_write', 'product_status', 'dwpd', 'part_url', 'capacity_in_tb',
        'capacity_in_gb', 'product_id'
    ],
    'vmware': [
        'category', 'part_number', 'oem', 'dwpd', 'form_factor', 'capacity',
        'oem_part_number', 'part_description', 'interface', 'part_specification',
        'part_url', 'store', 'capacity_in_tb', 'capacity_in_gb', 'memory_sku'
    ],
    'asacomputer': [
        'store', 'category', 'server_specification', 'host_url',
        'server_description', 'management_software', 'm2_drives', 'pcie', 'note',
        'operating_system', 'sata_dom', 'ready_to_ship_system', 'u2_nvme_drives',
        'dimm_slots', 'drive_bays', 'system_management', 'm2_nvme',
        'optical_drive', 'lan', 'power_supply', 'memory', 'add_on_pcie', 'cpu',
        'hard_drive', 'network', 'sata_ssd_drives', 'warranty'
    ],
    'amd': [
        'store', 'category', 'product_family', 'memory_type',
        'maximum_memory_channels', 'maximum_memory_speed', 'launch_date',
        'platform', 'mfr_part_no', 'processor_series', 'product_specification',
        'product_name', 'part_url'
    ],
    'intel': [
        'product_name', 'category', 'product_family', 'product_line', 'platform',
        'model_number', 'maximum_memory_channels', 'maximum_memory_size',
        'maximum_memory_bandwidth', 'memory_type', 'maximum_memory_speed',
        'ecc_memory_supported', 'physical_address_extensions',
        'product_specification', 'compliance_description', 'specification_code',
        'ordering_code', 'part_url', 'store', 'chipset', 'specifications',
        'compatible_products', 'chipset_url', 'marketing status', 'launch date',
        'servicing status', 'end of servicing updates date', 'dpc'
    ],
    'asrock': [
        'server_description', 'host_url', 'server_specification', 'dimm_slots',
        'maximum_memory', 'part_description', 'a', 'b', 'c', 'encode_status',
        'product_id', 'capacity', 'speed', 'ranks', 'rank_width',
        'memory_type', 'dimm_type', 'ecc', 'voltage', 'height', 'qty',
        'store', 'category', 'part_url'
    ],
    'distech': [
        'store', 'part_number', 'part_description', 'category', 'oem',
        'oem_part_number', 'part_specification', 'memory_sku', 'capacity',
        'interface', 'form_factor', 'sequential_read', 'sequential_write',
        'random_read', 'random_write', 'dwpd', 'height', 'dimensions',
        'capacity_in_gb', 'capacity_in_tb', 'part_url'
    ],
}

TEST_FILE   = '27012025_hpe_db_import.csv'
REPORT_FILE = 'validation_results.csv'


# ─── HELPERS ───

def load_any_file(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, dtype=str, engine='openpyxl')
    else:
        df = pd.read_csv(path, dtype=str)



  # ── DROP ALL "Unnamed" COLUMNS ──
    # pandas names blank‐header cols as "Unnamed: N"
    df = df.loc[:, ~df.columns
                   .str.lower()
                   .str.startswith('unnamed')]

    return df


def infer_brand_from_filename(filename: str) -> str:
    base = os.path.basename(filename).lower()
    tokens = re.split(r'[^a-z0-9\.]+', base)
    for t in tokens:
        if t in MASTER_RULES:
            return t
    raise ValueError(f"Cannot infer brand from filename '{filename}'")


def write_report(file: str, brand: str, missing: list[str], extra: list[str]):
    """
    Append or create REPORT_FILE with columns:
      file, brand, result
    where result may include missing and/or extra columns.
    """
    parts = []
    if missing:
        parts.append("missing: " + ", ".join(missing))
    if extra:
        parts.append("extra: "   + ", ".join(extra))
    result = "all pass" if not parts else "; ".join(parts)

    df = pd.DataFrame([{
        'file':   file,
        'brand':  brand,
        'result': result
    }])
    write_header = not os.path.exists(REPORT_FILE)
    df.to_csv(REPORT_FILE, mode='a', index=False, header=write_header)


# ─── TEST ───

def test_required_columns_present():
    # 1) infer brand and required set
    brand    = infer_brand_from_filename(TEST_FILE)
    required = set(MASTER_RULES[brand])
    assert required, f"No rules defined for brand '{brand}'"

    # 2) load the file and normalize headers
    df      = load_any_file(TEST_FILE)
    present = {col.strip().lower() for col in df.columns}

    # 3) compute missing *and* extra columns
    missing = sorted(required - present)
    extra   = sorted(present  - required)

    # 4) write the CSV report (always runs, even if assertion fails)
    write_report(TEST_FILE, brand, missing, extra)

    # 5) assert that nothing is missing *or* extra
    assert not missing and not extra, (
        f"File '{TEST_FILE}' for brand '{brand}' has:\n"
        f"  • {len(missing)} missing columns: {missing}\n"
        f"  • {len(extra)} extra   columns: {extra}"
    )
