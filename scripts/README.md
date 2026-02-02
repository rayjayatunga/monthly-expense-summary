# Scripts

This directory contains Python scripts for processing bank statements and loading data to BigQuery.

## Files

### `gcs_utils.py`
Utilities for interacting with Google Cloud Storage:
- Download files from GCS
- Upload files to GCS
- Move/archive files within GCS
- List unprocessed files

### `bigquery_loader.py`
Utilities for loading data to BigQuery:
- Load pandas DataFrames to BigQuery tables
- Create datasets
- Add metadata columns
- Query BigQuery

### `process_statements.py`
Main orchestration script that:
1. Downloads unprocessed statement files from GCS
2. Parses different file formats (XLSX for Amex, CSV for Scotia)
3. Standardizes the data schema
4. Uploads to BigQuery raw tables
5. Archives processed files in GCS

## Usage

### Local Testing

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCS_BUCKET_NAME="monthly-expense-statements"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Run the processing script
cd scripts
python process_statements.py
```

### In GitHub Actions

The script is automatically run by GitHub Actions workflow. Environment variables are set from GitHub Secrets.

## Requirements

All dependencies are managed via `pyproject.toml` in the root directory:
- `pandas` - Data manipulation
- `openpyxl` - Excel file parsing
- `google-cloud-storage` - GCS operations
- `google-cloud-bigquery` - BigQuery operations
- `python-dotenv` - Environment variable management
