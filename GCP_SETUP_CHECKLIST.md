# GCP Setup Checklist

Complete these steps in order. Check off each item as you complete it.

## ✅ Pre-Setup (Already Done!)
- [x] Free trial activated ($300 credit, 90 days)
- [x] Python environment set up locally
- [x] Project structure created

---

## 📋 Step 1: Create/Verify GCP Project

### 1.1 Create Project
- [x] Go to: https://console.cloud.google.com
- [x] Click "Select a project" dropdown (top bar)
- [x] Click "New Project"
- [x] Enter project name: `monthly-expense-summary` (or your preference)
- [x] Click "Create"
- [x] **Note your Project ID** (e.g., `monthly-expense-summary-123456`)
  - Write it here: `expenses-486200`

---

## 📋 Step 2: Enable Required APIs

### 2.1 Enable BigQuery API
- [x] Go to: https://console.cloud.google.com/apis/library/bigquery.googleapis.com
- [x] Make sure your project is selected (top bar)
- [x] Click "Enable"
- [x] Wait for confirmation (~30 seconds)

### 2.2 Enable Cloud Storage API
- [x] Go to: https://console.cloud.google.com/apis/library/storage.googleapis.com
- [x] Click "Enable"
- [x] Wait for confirmation

---

## 📋 Step 3: Create Service Account

### 3.1 Navigate to Service Accounts
- [ ] Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
- [ ] Make sure correct project is selected

### 3.2 Create Service Account
- [x] Click "Create Service Account"
- [x] Service account name: `expense-pipeline-sa`
- [x] Service account ID: `expense-pipeline-sa` (auto-filled)
- [x] Description: `Service account for monthly expense pipeline`
- [x] Click "Create and Continue"

### 3.3 Grant Roles
- [x] Click "Select a role" dropdown
- [x] Search for and select: `BigQuery Admin`
- [x] Click "+ Add Another Role"
- [x] Search for and select: `Storage Admin`
- [x] Click "Continue"
- [x] Click "Done" (skip optional steps)

### 3.4 Create JSON Key
- [x] Find your new service account in the list
- [x] Click the three dots (⋮) on the right
- [x] Click "Manage keys"
- [x] Click "Add Key" > "Create new key"
- [x] Select "JSON"
- [x] Click "Create"
- [x] File downloads automatically (e.g., `monthly-expense-summary-abc123-456def.json`)
- [x] **Move the file to a safe location:**
  ```bash
  mv ~/Downloads/monthly-expense-summary-*.json ~/expense-pipeline-key.json
  ```
- [x] Verify it's there: `ls -lh ~/expense-pipeline-key.json`

---

## 📋 Step 4: Create Cloud Storage Bucket

### 4.1 Navigate to Cloud Storage
- [ ] Go to: https://console.cloud.google.com/storage/browser
- [ ] Click "Create Bucket"

### 4.2 Configure Bucket
- [x] Bucket name: `monthly-expense-statements` (must be globally unique)
  - If taken, try: `monthly-expense-statements-yourname`
  - Write actual name here: `monthly-expense-statements`
- [x] Location type: `Region`
- [x] Location: `northamerica-northeast1` (Montreal - closest to Toronto)
- [x] Storage class: `Standard`
- [x] Access control: `Uniform`
- [x] Click "Create"

### 4.3 Create Folder Structure
- [x] Click on your bucket name
- [x] Click "Create Folder" > Name: `raw` > Click "Create"
- [x] Click into `raw` folder
- [x] Create folder: `amex`
- [x] Create folder: `scotia_credit`
- [x] Create folder: `scotia_chequing`

**Your structure should look like:**
```
monthly-expense-statements/
└── raw/
    ├── amex/
    ├── scotia_credit/
    └── scotia_chequing/
```

---

## 📋 Step 5: Create BigQuery Datasets

### Option A: Via Console (Easier)

#### 5.1 Create 'raw' Dataset
- [x] Go to: https://console.cloud.google.com/bigquery
- [x] In the Explorer panel, click your project name
- [x] Click the three dots (⋮) next to your project
- [x] Click "Create dataset"
- [x] Dataset ID: `raw`
- [x] Location: `northamerica-northeast1` (Montreal - matches GCS bucket)
- [x] Click "Create Dataset"

#### 5.2 Create 'base' Dataset
- [x] Repeat above steps
- [x] Dataset ID: `base`
- [x] Click "Create Dataset"

#### 5.3 Create 'intermediate' Dataset
- [x] Repeat above steps
- [x] Dataset ID: `intermediate`
- [x] Click "Create Dataset"

#### 5.4 Create 'mart' Dataset
- [x] Repeat above steps
- [x] Dataset ID: `mart`
- [x] Click "Create Dataset"

**Verify:** You should see 4 datasets under your project in BigQuery Explorer:
- ☑ raw
- ☑ base
- ☑ intermediate
- ☑ mart
- (Note: You also have a 'scratch' dataset - that's fine!)

---

## 📋 Step 6: Set Up Budget Alert (Recommended)

- [ ] Go to: https://console.cloud.google.com/billing/budgets
- [ ] Click "Create Budget"
- [ ] Budget name: `Monthly Free Tier Monitor`
- [ ] Projects: Select `monthly-expense-summary`
- [ ] Budget type: `Specified amount`
- [ ] Target amount: `$5.00`
- [ ] Threshold rules:
  - [ ] 50% ($2.50)
  - [ ] 90% ($4.50)
  - [ ] 100% ($5.00)
- [ ] Check "Email alerts to billing admins and users"
- [ ] Click "Finish"

---

## 📋 Step 7: Configure Local Environment

### 7.1 Set Environment Variables
```bash
cd /Users/rayjayatunga/Documents/Experiments/monthly-expense-summary

# Create .env file (not tracked by git)
cat > .env << EOF
# Replace with your actual values
GCP_PROJECT_ID=expenses-486200
GCS_BUCKET_NAME=monthly-expense-statements
GOOGLE_APPLICATION_CREDENTIALS=/Users/rayjayatunga/Documents/Experiments/monthly-expense-summary/credentials/expenses-486200-aac89b8bb809.json
EOF
```

- [x] Run the above command
- [x] Edit `.env` and replace with actual Project ID: `expenses-486200`
- [x] Updated path to credentials in `credentials/` folder
- [x] Verify: `cat .env`

### 7.2 Configure dbt Profile
```bash
# Copy example to dbt config directory
mkdir -p ~/.dbt
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
```

- [x] Run the above command
- [x] Verify: `ls -la ~/.dbt/profiles.yml`

---

## 📋 Step 8: Test Your Setup

### 8.1 Test Python Environment
```bash
cd /Users/rayjayatunga/Documents/Experiments/monthly-expense-summary
source .venv/bin/activate

# Test imports
python -c "from scripts.gcs_utils import GCSHandler; print('✅ GCS utils working')"
python -c "from scripts.bigquery_loader import BigQueryLoader; print('✅ BigQuery loader working')"
```

- [x] Run the above commands
- [x] Both should print success messages

### 8.2 Test dbt Connection
```bash
cd /Users/rayjayatunga/Documents/Experiments/monthly-expense-summary/dbt
source ../.venv/bin/activate
dbt debug --profiles-dir ~/.dbt
```

- [x] Run the above commands
- [x] Should see: `All checks passed!`

---

## 📋 Step 9: Upload Test File

### 9.1 Test with Existing Amex CSV
```bash
# Upload was done via Python script
# File uploaded: aug-2025.csv to gs://monthly-expense-statements/raw/amex/
```

- [x] File uploaded successfully
- [x] Verify in GCS Console: https://console.cloud.google.com/storage/browser

---

## 📋 Step 10: Run First Pipeline Test

### 10.1 Process Statements
```bash
cd /Users/rayjayatunga/Documents/Experiments/monthly-expense-summary
source .venv/bin/activate
export $(cat .env | xargs)

python scripts/process_statements.py
```

- [x] Run the above
- [x] Successfully processed 81 rows
- [x] Data loaded to `raw.amex_transactions`
- [x] File archived to `raw/amex/processed/`

### 10.2 Run dbt Models
```bash
cd dbt
source ../.venv/bin/activate
dbt run --profiles-dir ~/.dbt
```

- [x] Run the above
- [x] 3 models built successfully:
  - ✅ `dev_base.base_amex__transactions` (view)
  - ✅ `dev_intermediate.int_all_transactions__unioned` (view)
  - ✅ `dev_mart.mart_expense_summary` (table)

### 10.3 Query Results
```sql
-- Go to: https://console.cloud.google.com/bigquery
-- Run this query:

SELECT * 
FROM `expenses-486200.dev_mart.mart_expense_summary` 
ORDER BY period_start_date DESC 
LIMIT 10
```

- [x] Query successful!
- [x] Expense summaries showing:
  - Monthly: $5,883.55 total
  - Weekly: $5,883.55 total  
  - Yearly: $5,883.55 total

---

## ✅ Setup Complete! 🎉

**Congratulations!** Your expense tracking pipeline is fully operational!

Once all checkboxes are checked, your pipeline is fully operational!

### Next Steps:
1. Set up GitHub Actions for automation (see SETUP.md)
2. Create Looker Studio dashboard
3. Start your weekly workflow

### Weekly Workflow:
Every Sunday:
1. Download statements from banks
2. Upload to GCS bucket
3. Run pipeline (or let GitHub Actions do it)
4. View dashboard

---

## 📞 Need Help?

- Can't find something? Check SETUP.md for detailed instructions
- Errors? Check "Troubleshooting" section in SETUP.md
- Questions? Review STATUS.md for architecture overview
