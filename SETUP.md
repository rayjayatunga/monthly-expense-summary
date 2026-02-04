# Setup Guide

This guide will help you set up the monthly expense summary pipeline.

## Prerequisites

- ✅ Homebrew installed
- ✅ uv installed
- ✅ Python 3.11+
- ✅ Google Cloud Platform account
- ✅ Credit card (required for GCP billing, but won't be charged within free tier)

## Step 1: Google Cloud Setup

⚠️ **Important**: You must set up billing in GCP even though this project stays within the free tier limits. Your credit card is required but you won't be charged if you stay within the generous free tier quotas (which this project does by default).

### 1.1 Create GCP Project
```bash
# 1. Go to https://console.cloud.google.com
# 2. Click "Select a project" > "New Project"
# 3. Name: monthly-expense-summary (or your preferred name)
# 4. Click "Create"
# 5. Note your Project ID (you'll need this later)
```

### 1.2 Enable Billing & Set Budget Alerts

**Enable Billing:**
```bash
# 1. Go to https://console.cloud.google.com/billing
# 2. Click "Create billing account" (or link existing one)
# 3. Enter your credit card information
# 4. Link the billing account to your project
```

**Set Up Budget Alerts (Highly Recommended):**
```bash
# 1. Go to Billing > Budgets & Alerts
# 2. Click "Create Budget"
# 3. Select your project
# 4. Set budget amount: $5.00 per month
# 5. Set alert thresholds: 50%, 90%, 100%
# 6. Add your email address
# 7. Click "Finish"
```

**Expected Costs:** $0.00/month (well within free tier)
- BigQuery Free Tier: 10 GB storage, 1 TB queries/month
- Cloud Storage Free Tier: 5 GB storage
- Your Expected Usage: ~100 MB storage, ~5 GB queries/month

### 1.3 Enable Required APIs
```bash
# In GCP Console, go to APIs & Services > Enable APIs and Services
# Search for and enable:
# 1. BigQuery API
# 2. Cloud Storage API

# Or use gcloud CLI:
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
```

### 1.4 Create Service Account
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

### 1.5 Create GCS Bucket
```bash
# In GCP Console or use gcloud CLI:
gsutil mb -l US gs://monthly-expense-statements

# Create folder structure
gsutil mkdir gs://monthly-expense-statements/raw/
gsutil mkdir gs://monthly-expense-statements/raw/amex/
gsutil mkdir gs://monthly-expense-statements/raw/scotia_credit/
gsutil mkdir gs://monthly-expense-statements/raw/scotia_chequing/
```

### 1.6 Create BigQuery Datasets
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

### Billing & Cost Concerns
```bash
# Check current billing status
# Go to: https://console.cloud.google.com/billing

# Monitor BigQuery usage
# Go to: BigQuery Console > More > Query history
# Check "Bytes processed" column

# Check Cloud Storage usage
gsutil du -sh gs://monthly-expense-statements

# View detailed costs (if any)
# Go to: Billing > Reports
# Set date range and filter by service
```

**Expected Usage (stays within free tier):**
- BigQuery Storage: ~100 MB (Free: 10 GB)
- BigQuery Queries: ~5 GB/month (Free: 1 TB)
- Cloud Storage: ~500 MB (Free: 5 GB)
- **Cost: $0.00/month**

**If you see unexpected charges:**
1. Check if you accidentally created Compute Engine instances
2. Verify you're only using BigQuery and Cloud Storage
3. Review budget alerts
4. Delete any unused resources

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
bq ls --project_id=your-project-id

# Check service account has BigQuery Admin role
# Go to: IAM & Admin > IAM
# Find your service account and verify roles

# Common error: "Billing has not been enabled"
# Solution: Enable billing in Step 1.2 above
```

### Billing Not Enabled Error
```bash
# Error message: "BigQuery API has not been used in project X before or it is disabled"
# 
# Solutions:
# 1. Verify billing is enabled:
#    Go to: https://console.cloud.google.com/billing
#    Ensure billing account is linked to your project
#
# 2. Enable BigQuery API:
#    gcloud services enable bigquery.googleapis.com --project=your-project-id
#
# 3. Wait 1-2 minutes for propagation
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
