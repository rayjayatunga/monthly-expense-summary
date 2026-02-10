# Dev/Prod Schema Setup

## 🎯 Overview

Your dbt project is now configured with separate dev and prod environments to prevent accidentally overwriting production data during development.

## 📊 How It Works

### **Development (default)**
When you run: `dbt run`

**Tables are created in:**
- `expenses-486200.dev_base.*`
- `expenses-486200.dev_intermediate.*`
- `expenses-486200.dev_mart.*`

### **Production**
When you run: `dbt run --target prod`

**Tables are created in:**
- `expenses-486200.base.*`
- `expenses-486200.intermediate.*`
- `expenses-486200.mart.*`

## 🔧 Configuration Files

### 1. `~/.dbt/profiles.yml`
Defines two targets (dev and prod) with different base datasets:

```yaml
expense_pipeline:
  target: dev  # Default to dev
  outputs:
    dev:
      dataset: dev  # Base dataset for dev
    prod:
      dataset: raw  # Base dataset for prod
```

### 2. `dbt/macros/generate_schema_name.sql`
Custom macro that controls final schema naming:

- **Dev:** Prefixes schemas with `dev_`
  - `base` → `dev_base`
  - `intermediate` → `dev_intermediate`
  - `mart` → `dev_mart`

- **Prod:** Uses schema names directly
  - `base` → `base`
  - `intermediate` → `intermediate`
  - `mart` → `mart`

### 3. `dbt/dbt_project.yml`
Defines schema suffixes for each model layer:

```yaml
models:
  expense_pipeline:
    base:
      +schema: base
    intermediate:
      +schema: intermediate
    marts:
      +schema: mart
```

## 🚀 Usage

### **Daily Development Work**

```bash
# Activate environment
cd /Users/rayjayatunga/Documents/Experiments/monthly-expense-summary/dbt
source ../.venv/bin/activate

# Run models (goes to dev_* datasets)
dbt run --profiles-dir .

# Run specific models
dbt run --select base_amex__transactions --profiles-dir .

# Run tests
dbt test --profiles-dir .

# Generate docs
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

### **Production Deployment**

```bash
# Run in production (goes to base/intermediate/mart datasets)
dbt run --target prod --profiles-dir .

# Or run specific models in prod
dbt run --select marts --target prod --profiles-dir .
```

### **Check Which Target You're Using**

```bash
dbt debug --profiles-dir .
# Look for: "schema: dev" or "schema: raw"
```

## 📋 BigQuery Datasets

### **Development Datasets:**
- ✅ `dev_base` - Development base models
- ✅ `dev_intermediate` - Development intermediate models
- ✅ `dev_mart` - Development mart models

### **Production Datasets:**
- ✅ `raw` - Raw data from statements
- ✅ `base` - Production base models
- ✅ `intermediate` - Production intermediate models
- ✅ `mart` - Production mart models (connected to Looker Studio)

## 🔄 Typical Workflow

### **1. Develop Locally (Dev)**
```bash
# Make changes to models
# Run in dev
dbt run

# Test in dev
dbt test

# Query dev data in BigQuery:
# SELECT * FROM `expenses-486200.dev_mart.mart_expense_summary`
```

### **2. Promote to Production**
```bash
# Once satisfied with changes, run in prod
dbt run --target prod

# Query prod data in BigQuery:
# SELECT * FROM `expenses-486200.mart.mart_expense_summary`
```

### **3. Looker Studio**
- Point your Looker Studio dashboard to **production** mart tables
- `expenses-486200.mart.mart_expense_summary`
- Never use dev_* tables in dashboards

## 🧹 Cleaning Up Dev Data

To clean up dev tables when they're no longer needed:

```bash
# Delete all dev models
dbt run-operation drop_schema --args "{schema_name: dev_base}"
dbt run-operation drop_schema --args "{schema_name: dev_intermediate}"
dbt run-operation drop_schema --args "{schema_name: dev_mart}"

# Or manually in BigQuery Console:
# Delete datasets: dev_base, dev_intermediate, dev_mart
```

## ⚠️ Important Notes

### **Raw Data**
- Raw tables (`raw.amex_transactions`, etc.) are shared between dev and prod
- The Python processing script always writes to `raw.*`
- Both dev and prod read from the same raw tables

### **Target Selection**
- **Default:** `dev` (safe for experimentation)
- **Production:** Must explicitly use `--target prod`
- GitHub Actions should use `--target prod`

### **Cost Considerations**
- Dev and prod tables both count toward BigQuery storage (10 GB free tier)
- Queries against dev or prod both count toward query quota (1 TB free tier)
- Clean up dev tables regularly to save storage

## 🎯 Benefits

✅ **Safety:** Can't accidentally overwrite production data
✅ **Experimentation:** Test changes without affecting dashboards
✅ **Clear Separation:** Easy to see what's dev vs prod
✅ **Flexibility:** Can have different data in dev for testing
✅ **Best Practice:** Industry-standard approach

## 📚 Further Reading

- [dbt Custom Schemas](https://docs.getdbt.com/docs/build/custom-schemas)
- [dbt Deployment Best Practices](https://docs.getdbt.com/guides/best-practices/environment-setup/1-env-setup-overview)
- [BigQuery Datasets](https://cloud.google.com/bigquery/docs/datasets-intro)
