# Setup Guide

This guide will help you set up the monthly expense summary pipeline.

## Prerequisites

- ✅ Homebrew installed
- ✅ uv installed
- ✅ Python 3.11+
- ✅ Google Cloud Platform account (free tier)
- ✅ BigQuery API enabled
- ✅ Cloud Storage API enabled

## Step 1: Google Cloud Setup

### 1.1 Create GCP Project
```bash
# Go to https://console.cloud.google.com
# Create a new project or use an existing one
```

### 1.2 Create Service Account
```bash
# In GCP Console:
# 1. Go to IAM & Admin > Service Accounts
# 2. Click "Create Service Account"
# 3. Name: expense-pipeline-sa
# 4. Grant roles:
#    - BigQuery Admin
#    - Storage Admin
# 5. Create and download JSON key
# 6. Save as ~/expense-pipeline-key.json
```

### 1.3 Create GCS Bucket
```bash
# In GCP Console or use gcloud CLI:
gsutil mb -l US gs://monthly-expense-statements

# Create folder structure
gsutil mkdir gs://monthly-expense-statements/raw/
gsutil mkdir gs://monthly-expense-statements/raw/amex/
gsutil mkdir gs://monthly-expense-statements/raw/scotia_credit/
gsutil mkdir gs://monthly-expense-statements/raw/scotia_chequing/
```

### 1.4 Create BigQuery Datasets
```bash
bq mk --dataset --location=US monthly_expense_summary:raw
bq mk --dataset --location=US monthly_expense_summary:base
bq mk --dataset --location=US monthly_expense_summary:intermediate
bq mk --dataset --location=US monthly_expense_summary:mart
```

## Step 2: Local Environment Setup

### 2.1 Clone/Navigate to Project
```bash
cd /path/to/monthly-expense-summary
```

### 2.2 Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2.3 Create Environment Variables File
```bash
# Copy example and edit with your values
cp .env.example .env

# Edit .env with your actual values:
# - GCP_PROJECT_ID
# - GCS_BUCKET_NAME
# - GOOGLE_APPLICATION_CREDENTIALS (path to JSON key)
```

### 2.4 Configure dbt Profile
```bash
# Copy example profile
cp dbt/profiles.yml.example ~/.dbt/profiles.yml

# Or set environment variables (recommended for CI/CD)
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Step 3: Test the Setup

### 3.1 Test Python Scripts
```bash
# Activate venv
source .venv/bin/activate

# Test imports
python -c "from scripts.gcs_utils import GCSHandler; print('✅ GCS utils working')"
python -c "from scripts.bigquery_loader import BigQueryLoader; print('✅ BigQuery loader working')"
```

### 3.2 Test dbt Connection
```bash
cd dbt
dbt debug --profiles-dir .
```

Expected output: `All checks passed!`

### 3.3 Upload Test File
```bash
# Upload one of your existing statements to GCS for testing
gsutil cp statements/raw/Amex/aug-2025.csv gs://monthly-expense-statements/raw/amex/
```

### 3.4 Run Processing Script
```bash
# From project root
python scripts/process_statements.py
```

### 3.5 Run dbt Models
```bash
cd dbt
dbt run --profiles-dir .
```

## Step 4: GitHub Setup (for GitHub Actions)

### 4.1 Create GitHub Repository
```bash
# In project root
git add .
git commit -m "Initial commit: expense pipeline setup"
gh repo create monthly-expense-summary --private --source=. --remote=origin --push
```

### 4.2 Add GitHub Secrets
```bash
# In GitHub repo settings > Secrets and variables > Actions
# Add the following secrets:

# 1. GCP_SERVICE_ACCOUNT_KEY
#    - Copy entire contents of your service account JSON key file

# 2. GCP_PROJECT_ID
#    - Your GCP project ID

# 3. GCS_BUCKET_NAME
#    - Your GCS bucket name (e.g., monthly-expense-statements)
```

## Step 5: Weekly Workflow

### Upload Statements (Every Sunday)

**Option A: Via Google Cloud Console Web**
1. Go to https://console.cloud.google.com/storage
2. Navigate to your bucket > raw folder
3. Upload files to appropriate subfolder (amex/, scotia_credit/, scotia_chequing/)

**Option B: Via gcloud CLI**
```bash
# Upload Amex statement (XLSX)
gsutil cp ~/Downloads/amex-statement.xlsx gs://monthly-expense-statements/raw/amex/

# Upload Scotia credit statement (CSV)
gsutil cp ~/Downloads/scotia-visa.csv gs://monthly-expense-statements/raw/scotia_credit/

# Upload Scotia chequing statement (CSV)
gsutil cp ~/Downloads/scotia-chequing.csv gs://monthly-expense-statements/raw/scotia_chequing/
```

**Option C: Via Google Cloud Storage App (Mobile)**
1. Open Google Cloud app on phone
2. Navigate to Storage > your bucket
3. Upload files from phone

### Trigger Pipeline

**Option A: Automatic (Scheduled)**
- GitHub Action runs automatically every Sunday at 8 PM

**Option B: Manual Trigger**
1. Go to GitHub repo > Actions tab
2. Select "Run Pipeline" workflow
3. Click "Run workflow"

**Option C: Local Run**
```bash
# Activate venv
source .venv/bin/activate

# Run processing
python scripts/process_statements.py

# Run dbt
cd dbt && dbt run --profiles-dir .
```

## Step 6: View Results

### BigQuery Console
```bash
# Open BigQuery console
open https://console.cloud.google.com/bigquery

# Query your data
SELECT * FROM `your-project.mart.mart_expense_summary` 
ORDER BY period_start_date DESC
LIMIT 10
```

### Looker Studio (Coming Soon)
1. Go to https://lookerstudio.google.com
2. Create new report
3. Connect to BigQuery
4. Select mart tables
5. Build visualizations

## Troubleshooting

### Python Import Errors
```bash
# Ensure venv is activated
source .venv/bin/activate

# Reinstall dependencies
uv sync
```

### dbt Connection Issues
```bash
# Check profile configuration
dbt debug --profiles-dir .

# Verify service account has correct permissions
# Check GOOGLE_APPLICATION_CREDENTIALS path is correct
```

### GCS Permission Errors
```bash
# Verify service account has Storage Admin role
# Check bucket name is correct in .env
```

### BigQuery Errors
```bash
# Verify datasets exist
bq ls

# Check service account has BigQuery Admin role
```

## Next Steps

- [ ] Update Scotia CSV column mappings once you have actual files
- [ ] Create category mapping seed file for expense categorization
- [ ] Set up Looker Studio dashboard
- [ ] Configure GitHub Actions workflow (see `.github/workflows/`)
- [ ] Add more dbt models for deeper analysis

## Useful Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run processing script
python scripts/process_statements.py

# Run dbt models
cd dbt && dbt run --profiles-dir .

# Run dbt tests
cd dbt && dbt test --profiles-dir .

# Generate dbt docs
cd dbt && dbt docs generate --profiles-dir .
cd dbt && dbt docs serve --profiles-dir .

# Check dbt lineage
cd dbt && dbt run-operation generate_model_yaml --args '{models: ["mart_expense_summary"]}'
```
