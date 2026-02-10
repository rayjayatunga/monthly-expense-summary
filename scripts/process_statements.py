"""
Main script for processing bank statements and loading to BigQuery.

This script:
1. Downloads statement files from GCS
2. Parses different formats (XLSX, CSV)
3. Standardizes the data
4. Uploads to BigQuery raw tables
5. Archives processed files
"""

import hashlib
import pandas as pd
from pathlib import Path
from typing import Optional
import os
from datetime import datetime

from gcs_utils import GCSHandler, get_unprocessed_files, archive_processed_files
from bigquery_loader import BigQueryLoader, add_metadata_columns


# Configuration
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'monthly-expense-statements')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
BQ_RAW_DATASET = 'raw'
LOCAL_TEMP_DIR = Path('/tmp/statements')


def _normalize_col_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise column names to BigQuery-safe snake_case."""
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(' ', '_', regex=False)
        .str.replace('/', '_', regex=False)
        .str.replace('#', 'Number', regex=False)
        .str.replace('-', '_', regex=False)
    )
    return df


def _find_header_row(file_path: str) -> int:
    """
    Locate the row index whose first non-null cell is 'Date'.

    Amex XLS files include several metadata / summary rows above the
    actual transaction table.  This function scans row-by-row (reading
    everything as plain strings) until it finds the header row.
    """
    df_raw = pd.read_excel(file_path, header=None, dtype=str)
    for idx, row in df_raw.iterrows():
        first_val = row.dropna().iloc[0] if not row.dropna().empty else ''
        if str(first_val).strip().lower() == 'date':
            return int(idx)
    return 0  # fallback: assume first row is the header


def _clean_amount(value) -> Optional[float]:
    """
    Strip currency symbols / commas and return a float, or None.

    Handles values like '$3,317.05', '-$28.16', '28.16 USD', '0', NaN.
    """
    if pd.isna(value):
        return None
    s = str(value).strip()
    # Remove currency symbols, commas, and trailing alpha codes (e.g. ' USD')
    s = s.replace('$', '').replace(',', '').split()[0]
    try:
        return float(s)
    except ValueError:
        return None


def _extract_currency(value) -> Optional[str]:
    """
    Extract a 3-letter ISO currency code from a raw amount string.

    Examples: '28.16 USD' → 'USD', '28.16USD' → 'USD', '$28.16' → None.
    """
    import re
    if pd.isna(value):
        return None
    match = re.search(r'[A-Z]{3}$', str(value).strip())
    return match.group(0) if match else None


def _compute_transaction_hash(date_str: str, description: str,
                               amount_raw: str, cardmember: str) -> str:
    """
    Return a stable SHA-256 hex digest that uniquely identifies a transaction.

    Fields are normalised before hashing so minor formatting differences
    (e.g. '$67.84' vs '67.84') do not produce different hashes for the
    same underlying transaction.
    """
    clean_amount = _clean_amount(amount_raw)
    amount_norm = f'{clean_amount:.2f}' if clean_amount is not None else ''

    payload = '|'.join([
        str(date_str).strip(),
        str(description).strip(),
        amount_norm,
        str(cardmember).strip().upper(),
    ])
    return hashlib.sha256(payload.encode()).hexdigest()


def parse_amex_file(file_path: str) -> pd.DataFrame:
    """
    Parse an Amex statement file (XLS, XLSX, or CSV).

    Amex XLS/XLSX exports contain several metadata rows before the
    transaction table header.  This function detects that header row
    dynamically, normalises column names, cleans monetary amounts, and
    appends a SHA-256 ``transaction_hash`` column for deduplication.
    """
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        header_row = _find_header_row(file_path)
        df = pd.read_excel(file_path, header=header_row, dtype=str)
        # Drop any completely empty rows that can appear after the data
        df = df.dropna(how='all')
    else:
        df = pd.read_csv(file_path, dtype=str)

    df = _normalize_col_names(df)

    # ------------------------------------------------------------------ #
    # Compute transaction_hash BEFORE cleaning, using raw string values.  #
    # Date, Description, Amount and Cardmember make a stable composite    #
    # key; Reference is used instead of Amount when available (CSV export)#
    # ------------------------------------------------------------------ #
    date_col       = 'Date'
    desc_col       = 'Description'
    amount_col     = 'Amount'
    # Cardmember column name varies slightly between formats
    cardmember_col = next(
        (c for c in df.columns if c.lower().startswith('card')),
        None
    )

    df['transaction_hash'] = [
        _compute_transaction_hash(
            date_str    = row.get(date_col, ''),
            description = row.get(desc_col, ''),
            amount_raw  = row.get(amount_col, ''),
            cardmember  = row.get(cardmember_col, '') if cardmember_col else '',
        )
        for _, row in df.iterrows()
    ]

    # ------------------------------------------------------------------ #
    # Extract currency codes BEFORE cleaning strips them away             #
    # Foreign_Spend_Amount may look like '28.16 USD' or '28.16USD'       #
    # ------------------------------------------------------------------ #
    if 'Foreign_Spend_Amount' in df.columns:
        df['Foreign_Currency'] = df['Foreign_Spend_Amount'].apply(_extract_currency)

    # ------------------------------------------------------------------ #
    # Clean monetary columns so BigQuery receives proper floats            #
    # ------------------------------------------------------------------ #
    for col in ('Amount', 'Foreign_Spend_Amount', 'Commission', 'Exchange_Rate'):
        if col in df.columns:
            df[col] = df[col].apply(_clean_amount)

    return df


def parse_scotia_credit_file(file_path: str) -> pd.DataFrame:
    """
    Parse Scotia credit card statement (CSV format).
    
    Args:
        file_path: Path to Scotia credit statement file
        
    Returns:
        Parsed DataFrame
    """
    df = pd.read_csv(file_path)
    
    # TODO: Update with actual Scotia credit CSV column structure
    return df


def parse_scotia_chequing_file(file_path: str) -> pd.DataFrame:
    """
    Parse Scotia chequing statement (CSV format).
    
    Args:
        file_path: Path to Scotia chequing statement file
        
    Returns:
        Parsed DataFrame
    """
    df = pd.read_csv(file_path)
    
    # TODO: Update with actual Scotia chequing CSV column structure
    return df


def process_file(
    file_path: str,
    source: str,
    bq_loader: BigQueryLoader
) -> bool:
    """
    Process a single statement file and load to BigQuery.
    
    Args:
        file_path: Path to the file
        source: Source identifier ('amex', 'scotia_credit', 'scotia_chequing')
        bq_loader: BigQueryLoader instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Processing {file_path} from {source}...")
        
        # Parse based on source
        if source == 'amex':
            df = parse_amex_file(file_path)
            table_id = 'amex_transactions'
        elif source == 'scotia_credit':
            df = parse_scotia_credit_file(file_path)
            table_id = 'scotia_credit_transactions'
        elif source == 'scotia_chequing':
            df = parse_scotia_chequing_file(file_path)
            table_id = 'scotia_chequing_transactions'
        else:
            print(f"Unknown source: {source}")
            return False
        
        # Skip empty files
        if df.empty:
            print(f"Skipping empty file: {file_path}")
            return True
        
        # Add metadata columns
        file_name = Path(file_path).name
        df = add_metadata_columns(df, source, file_name)
        
        # Load to BigQuery
        bq_loader.load_dataframe(
            df=df,
            dataset_id=BQ_RAW_DATASET,
            table_id=table_id,
            write_disposition='WRITE_APPEND'
        )
        
        print(f"Successfully processed {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def determine_source_from_path(file_path: str) -> str:
    """
    Determine the source (amex, scotia_credit, scotia_chequing) from file path.
    
    Args:
        file_path: GCS file path
        
    Returns:
        Source identifier
    """
    if 'amex' in file_path.lower():
        return 'amex'
    elif 'scotia_credit' in file_path.lower() or 'visa' in file_path.lower():
        return 'scotia_credit'
    elif 'scotia_chequing' in file_path.lower() or 'chequing' in file_path.lower():
        return 'scotia_chequing'
    else:
        # Default based on file location in GCS
        if '/amex/' in file_path.lower():
            return 'amex'
        elif '/scotia_credit/' in file_path.lower():
            return 'scotia_credit'
        elif '/scotia_chequing/' in file_path.lower():
            return 'scotia_chequing'
        else:
            return 'unknown'


def main():
    """Main execution function."""
    
    # Validate environment variables
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID environment variable must be set")
    
    print("Starting statement processing pipeline...")
    print(f"GCS Bucket: {GCS_BUCKET_NAME}")
    print(f"GCP Project: {GCP_PROJECT_ID}")
    print(f"BigQuery Dataset: {BQ_RAW_DATASET}")
    
    # Initialize handlers
    gcs_handler = GCSHandler(GCS_BUCKET_NAME)
    bq_loader = BigQueryLoader(GCP_PROJECT_ID)
    
    # Ensure BigQuery dataset exists
    bq_loader.create_dataset(BQ_RAW_DATASET)
    
    # Create local temp directory
    LOCAL_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get unprocessed files from GCS
    unprocessed_files = get_unprocessed_files(gcs_handler, raw_prefix='raw/')
    
    if not unprocessed_files:
        print("No unprocessed files found in GCS bucket")
        return
    
    print(f"Found {len(unprocessed_files)} unprocessed files")
    
    # Process each file
    successfully_processed = []
    
    for gcs_file_path in unprocessed_files:
        # Determine source
        source = determine_source_from_path(gcs_file_path)
        
        if source == 'unknown':
            print(f"Skipping file with unknown source: {gcs_file_path}")
            continue
        
        # Download file to local temp directory
        local_file_path = LOCAL_TEMP_DIR / Path(gcs_file_path).name
        gcs_handler.download_file(gcs_file_path, str(local_file_path))
        
        # Process file
        success = process_file(str(local_file_path), source, bq_loader)
        
        if success:
            successfully_processed.append(gcs_file_path)
        
        # Clean up local file
        local_file_path.unlink()
    
    # Archive successfully processed files
    if successfully_processed:
        print(f"\nArchiving {len(successfully_processed)} processed files...")
        archive_processed_files(gcs_handler, successfully_processed)
    
    print("\nProcessing complete!")
    print(f"Successfully processed: {len(successfully_processed)} files")
    print(f"Failed: {len(unprocessed_files) - len(successfully_processed)} files")


if __name__ == '__main__':
    main()
