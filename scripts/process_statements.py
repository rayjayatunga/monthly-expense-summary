"""
Main script for processing bank statements and loading to BigQuery.

This script:
1. Downloads statement files from GCS
2. Parses different formats (XLSX, CSV)
3. Standardizes the data
4. Uploads to BigQuery raw tables
5. Archives processed files
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import os
from datetime import datetime

from gcs_utils import GCSHandler, get_unprocessed_files, archive_processed_files
from bigquery_loader import BigQueryLoader, add_metadata_columns


# Configuration
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'monthly-expense-statements')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
BQ_RAW_DATASET = 'raw'
LOCAL_TEMP_DIR = Path('/tmp/statements')


def parse_amex_file(file_path: str) -> pd.DataFrame:
    """
    Parse Amex statement file (XLSX or CSV format).
    
    Args:
        file_path: Path to Amex statement file
        
    Returns:
        Parsed DataFrame
    """
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    
    # Expected columns based on your sample:
    # Date, Date Processed, Description, Card Member, Account #, Amount, 
    # Foreign Spend Amount, Commission, Exchange Rate, Additional Information, 
    # Merchant, Address, City / Province, Postal Code, Country, Reference
    
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
