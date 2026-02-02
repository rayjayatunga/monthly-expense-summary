# Monthly Expense Summary Pipeline

A hobbyist data engineering pipeline for tracking and analyzing personal credit card and banking expenses across multiple accounts.

## 📊 Project Overview

This pipeline processes weekly credit card and bank statements from multiple sources (Amex, Scotia credit card, Scotia chequing), transforms the data using dbt, loads it into Google BigQuery, and visualizes insights through Looker Studio dashboards.

### Data Sources
- **Amex Credit Card** - XLSX statements (downloaded manually)
- **Scotia Credit Card** - CSV statements (downloaded manually)
- **Scotia Chequing Account** - CSV statements (downloaded manually)

### Business Goals
- Track weekly/monthly spending patterns
- Categorize expenses across merchants
- Compare spending across different cards/accounts
- Identify trends and budget against targets
- Enable mobile-first statement uploads

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Manual Statement Downloads                │
│              (Sunday - From Banking Apps/Websites)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Storage (GCS Bucket)               │
│                 gs://monthly-expense-statements/             │
│  ├── raw/amex/*.xlsx                                         │
│  ├── raw/scotia_credit/*.csv                                 │
│  └── raw/scotia_chequing/*.csv                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions (Scheduled/Manual)               │
│                                                               │
│  ┌────────────────────────────────────────────────┐         │
│  │     Python Preprocessing Script                │         │
│  │  - Download files from GCS                     │         │
│  │  - Parse XLSX/CSV formats                      │         │
│  │  - Standardize schemas                         │         │
│  │  - Upload to BigQuery raw tables               │         │
│  │  - Archive processed files                     │         │
│  └────────────────────────────────────────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BigQuery - Raw Layer                      │
│                                                               │
│  - raw.amex_transactions                                     │
│  - raw.scotia_credit_transactions                            │
│  - raw.scotia_chequing_transactions                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              dbt Transformation (dbt-bigquery)               │
│                                                               │
│  BASE Layer          → Standardized schemas                  │
│  INTERMEDIATE Layer  → Business logic & enrichment           │
│  MART Layer          → Analytics-ready tables                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Looker Studio Dashboard                   │
│  - Weekly/monthly spending summaries                         │
│  - Category breakdowns                                       │
│  - Spending trends over time                                 │
│  - Budget vs actual comparisons                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| **Storage** | Google Cloud Storage | Free (5GB free tier) |
| **Data Warehouse** | Google BigQuery | Free (10GB storage, 1TB queries/month) |
| **Transformation** | dbt-core | Free (open source) |
| **Orchestration** | GitHub Actions | Free (2000 min/month) |
| **Visualization** | Looker Studio | Free |
| **Language** | Python 3.11+ | Free |
| **Package Manager** | uv | Free |

**Total Cost: $0/month** ✅

---

## 📁 Project Structure

```
monthly-expense-summary/
├── statements/
│   └── raw/                    # Local copies (optional)
│       ├── Amex/
│       ├── Scotia_Credit/
│       └── Scotia_Chequing/
├── scripts/
│   ├── process_statements.py  # Main preprocessing script
│   ├── gcs_utils.py           # GCS helper functions
│   └── bigquery_loader.py     # BigQuery upload utilities
├── dbt/
│   ├── models/
│   │   ├── base/              # Standardized raw data
│   │   │   ├── base_amex__transactions.sql
│   │   │   ├── base_scotia_credit__transactions.sql
│   │   │   └── base_scotia_chequing__transactions.sql
│   │   ├── intermediate/      # Business logic & enrichment
│   │   │   ├── int_all_transactions__unioned.sql
│   │   │   ├── int_transactions__categorized.sql
│   │   │   └── int_transactions__enriched.sql
│   │   └── marts/             # Analytics-ready tables
│   │       ├── mart_expense_summary.sql
│   │       ├── mart_expense_by_category.sql
│   │       └── mart_spending_trends.sql
│   ├── seeds/
│   │   └── category_mapping.csv  # Merchant → Category mapping
│   ├── macros/
│   ├── dbt_project.yml
│   └── profiles.yml
├── .github/
│   └── workflows/
│       └── run_pipeline.yml   # GitHub Actions workflow
├── pyproject.toml             # Python dependencies
├── uv.lock                    # Locked dependencies
├── .gitignore
└── README.md                  # This file
```

---

## 🔄 Data Flow & Transformation Layers

### **1. Raw Layer (BigQuery)**
Direct uploads from preprocessing script. Schema preserved as-is from source.

**Tables:**
- `raw.amex_transactions` - Raw Amex XLSX data
- `raw.scotia_credit_transactions` - Raw Scotia credit CSV data
- `raw.scotia_chequing_transactions` - Raw Scotia chequing CSV data

**Additional Fields:**
- `source` - Identifier (amex, scotia_credit, scotia_chequing)
- `uploaded_at` - Timestamp of upload
- `file_name` - Original file name
- `processing_date` - Date processed

### **2. Base Layer (dbt)**
Standardizes different source schemas into common format.

**Models:**
- `base_amex__transactions` - Renames Amex columns to standard names
- `base_scotia_credit__transactions` - Renames Scotia credit columns
- `base_scotia_chequing__transactions` - Renames Scotia chequing columns

**Standard Schema:**
```sql
transaction_date     DATE
description          STRING
merchant_name        STRING
amount               NUMERIC
transaction_type     STRING  -- (credit/debit)
account_type         STRING  -- (credit_card/chequing)
source               STRING  -- (amex/scotia_credit/scotia_chequing)
```

### **3. Intermediate Layer (dbt)**
Business logic, enrichment, and categorization.

**Models:**
- `int_all_transactions__unioned` - UNION ALL across base tables
- `int_transactions__categorized` - Join with category mapping seed
- `int_transactions__enriched` - Calculate additional fields:
  - Week/month/year
  - Is foreign transaction
  - Running totals
  - Previous period comparisons

### **4. Mart Layer (dbt)**
Analytics-ready tables optimized for reporting.

**Models:**
- `mart_expense_summary` - Aggregated by week/month/year
- `mart_expense_by_category` - Spending by category
- `mart_spending_trends` - Time-series analysis
- `mart_merchant_analysis` - Top merchants, frequency

---

## 📅 Implementation Plan

### **Phase 1: Environment Setup** (Week 1)
- [x] Verify Homebrew and uv installation
- [ ] Initialize Python project with uv
- [ ] Create GCP project and service account
- [ ] Set up BigQuery datasets (raw, base, intermediate, mart)
- [ ] Create GCS bucket for statement storage
- [ ] Configure GitHub repository

### **Phase 2: Preprocessing Scripts** (Week 1-2)
- [ ] Create `scripts/gcs_utils.py` - GCS download/upload functions
- [ ] Create `scripts/bigquery_loader.py` - BigQuery upload utilities
- [ ] Create `scripts/process_statements.py` - Main orchestration:
  - [ ] Parse Amex XLSX files
  - [ ] Parse Scotia CSV files
  - [ ] Standardize schemas
  - [ ] Upload to BigQuery raw tables
  - [ ] Archive processed files in GCS

### **Phase 3: dbt Models** (Week 2-3)
- [ ] Initialize dbt project
- [ ] Configure `dbt_project.yml` and `profiles.yml`
- [ ] Create base layer models
- [ ] Create intermediate layer models
- [ ] Create mart layer models
- [ ] Create category mapping seed
- [ ] Test and validate transformations

### **Phase 4: GitHub Actions** (Week 3)
- [ ] Create `.github/workflows/run_pipeline.yml`
- [ ] Configure secrets (GCP service account)
- [ ] Set up scheduled triggers (Sunday evenings)
- [ ] Add manual trigger option
- [ ] Test end-to-end pipeline

### **Phase 5: Looker Studio Dashboard** (Week 4)
- [ ] Connect to BigQuery mart tables
- [ ] Create spending overview page
- [ ] Create category analysis page
- [ ] Create trend analysis page
- [ ] Create merchant insights page
- [ ] Add filters and date ranges

---

## 🚀 Weekly Workflow

**Every Sunday:**

1. **Download Statements** (Manual)
   - Amex → Download XLSX from app/website
   - Scotia Credit → Download CSV from app/website
   - Scotia Chequing → Download CSV from app/website

2. **Upload to GCS** (Mobile or Desktop)
   - Open Google Cloud Console (web or app)
   - Navigate to `gs://monthly-expense-statements/raw/`
   - Upload files to appropriate folders:
     - `amex/` → XLSX files
     - `scotia_credit/` → CSV files
     - `scotia_chequing/` → CSV files

3. **Trigger Pipeline** (Automatic or Manual)
   - **Option A:** Wait for scheduled GitHub Action (Sunday 8 PM)
   - **Option B:** Manually trigger via GitHub Actions UI

4. **Review Dashboard**
   - Open Looker Studio dashboard
   - Verify new data loaded correctly
   - Analyze spending patterns

---

## 🔐 Security & Configuration

### **Google Cloud Service Account**
Required permissions:
- `BigQuery Admin` - Read/write BigQuery
- `Storage Object Admin` - Read/write GCS
- Store JSON key as GitHub Secret: `GCP_SERVICE_ACCOUNT_KEY`

### **GitHub Secrets**
- `GCP_SERVICE_ACCOUNT_KEY` - Service account JSON
- `GCP_PROJECT_ID` - GCP project ID
- `GCS_BUCKET_NAME` - GCS bucket name

---

## 📊 BigQuery Datasets

| Dataset | Purpose | Tables |
|---------|---------|--------|
| `raw` | Raw statement data | `amex_transactions`, `scotia_credit_transactions`, `scotia_chequing_transactions` |
| `base` | Standardized schemas | `base_amex__transactions`, `base_scotia_credit__transactions`, `base_scotia_chequing__transactions` |
| `intermediate` | Enriched data | `int_all_transactions__unioned`, `int_transactions__categorized`, `int_transactions__enriched` |
| `mart` | Analytics tables | `mart_expense_summary`, `mart_expense_by_category`, `mart_spending_trends` |

---

## 🎯 Success Metrics

- [ ] Can upload statements from phone in < 2 minutes
- [ ] Pipeline runs successfully on schedule
- [ ] All statements processed without errors
- [ ] Dashboard updates automatically
- [ ] Total monthly cost remains $0
- [ ] End-to-end pipeline takes < 10 minutes

---

## 📚 Future Enhancements

- [ ] Add PDF parsing for additional statement types
- [ ] Implement anomaly detection (unusual spending)
- [ ] Add budget alerts via email/Slack
- [ ] Create ML model for automatic categorization
- [ ] Add receipt image storage and OCR
- [ ] Build predictive spending forecasts
- [ ] Add multi-currency support improvements

---

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your own use!

---

## 📄 License

Personal use only.

---

**Last Updated:** February 2026
