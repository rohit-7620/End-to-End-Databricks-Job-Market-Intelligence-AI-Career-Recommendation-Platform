# ⚡ QUICK START GUIDE

## 🎯 Current Status: READY TO RUN!

Your dataset (postings.csv) has been preprocessed and the project is configured to use it.

## 🚀 Option 1: Run in Databricks (Recommended)

### Step 1: Upload to Databricks (5 minutes)

```
1. Open your Databricks workspace
2. Click "Repos" in the left sidebar
3. Click "Add Repo"
4. Choose:
   - Option A: Link your GitHub repo
   - Option B: Import via URL
   - Option C: Upload this folder as a workspace folder
```

### Step 2: Run the Pipeline (30 minutes)

Execute notebooks in order (click "Run All" on each):

```
00_setup_environment.py       → Creates catalog & schemas
01_data_ingestion.py         → Loads your 10K job postings  
02_bronze_layer.py           → Creates Bronze Delta table
03_silver_layer.py           → Cleans & standardizes data
04_gold_layer.py             → Creates 9 analytics tables
06_job_recommendation.py     → Builds ML recommender
07_mlflow_tracking.py        → Tracks experiments
08_ai_career_assistant.py    → Skill gap analysis
```

*Note: 05_data_analysis.sql contains dashboard queries to run in SQL Editor (next step)*

### Step 3: Build Dashboard (15 minutes)

```
1. Open Databricks SQL
2. For each query in notebooks/05_data_analysis.sql:
   - Create a new query
   - Paste the SQL
   - Save it
   - Add visualization
3. Create a new dashboard
4. Add all visualizations
5. Take screenshot for portfolio!
```

## 🧪 Option 2: Test Locally (Quick Validation)

```bash
# Verify preprocessing worked
python test_with_real_data.py

# View your data
python -c "import pandas as pd; df = pd.read_csv('data/raw/job_postings_raw.csv'); print(f'Ready: {len(df)} jobs'); print(df.head())"
```

## 📊 What You Get

After running the pipeline:

### ✅ Data Assets
- Bronze Table: 10,000 raw job postings
- Silver Table: 9,700+ cleaned records  
- Gold Tables: 9 analytics-ready tables

### ✅ Analytics Dashboard
- 7 visualizations
- 3 KPI metrics
- Interactive filtering

### ✅ ML Components
- Job recommender model
- MLflow experiment tracking
- Registered model in Model Registry

### ✅ AI Feature
- Skill gap analyzer
- Learning roadmap generator

## 🎮 Want to Process ALL 123K Rows?

```bash
# 1. Edit src/preprocess_postings.py
# Change line 76: MAX_ROWS = 10000  →  MAX_ROWS = None

# 2. Re-run preprocessing (takes 2-3 minutes)
python src/preprocess_postings.py

# 3. Upload to Databricks and run pipeline
# Same steps as above!
```

## 📂 Key Files Created for You

```
✅ data/raw/job_postings_raw.csv          Your preprocessed data (10K rows)
✅ src/preprocess_postings.py             Preprocessing script for your CSV
✅ test_with_real_data.py                 Validation script
✅ PROJECT_STATUS.md                       Detailed status report
✅ DATASET_SETUP.md                        Dataset guide
✅ notebooks/01_data_ingestion.py         Already configured (USE_SYNTHETIC=False)
```

## ⚡ Fastest Path to Demo

```
1. Open Databricks workspace                    (2 min)
2. Upload this project as Repo                  (3 min)
3. Run notebooks 00-08 in order                (30 min)
4. Build dashboard from 05_data_analysis.sql   (15 min)
5. Take screenshots                             (5 min)
────────────────────────────────────────────────────────
   Total: ~1 hour to fully working demo! 🎉
```

## 🎯 Success Criteria

You'll know it worked when you see:

✅ All notebooks run without errors
✅ Gold tables populated with data
✅ Dashboard showing visualizations
✅ MLflow experiment showing 3 runs
✅ Model registered in Model Registry
✅ Career assistant produces skill roadmaps

## 🆘 Common Issues & Solutions

### "Can't find postings.csv"
→ Make sure src/postings.csv uploaded to Databricks

### "Out of memory"  
→ Use a larger cluster (Standard_DS3_v2 or bigger)

### "Skills column empty"
→ Expected! Silver layer extracts skills from descriptions

### "Many null salaries"
→ Normal for real data, pipeline handles it

## 📞 Need Help?

Check these files:
- `PROJECT_STATUS.md` - Full status report
- `DATASET_SETUP.md` - Dataset integration guide  
- `README.md` - Complete documentation
- `docs/architecture.md` - System design
- `docs/data_dictionary.md` - Data schema

## 🎉 You're All Set!

Everything is configured and ready. Just:

1. Upload to Databricks
2. Run the notebooks
3. Build the dashboard
4. Showcase your work!

**Time to completion: ~1 hour**

Good luck! 🚀

---

**Pro tip**: Take screenshots of every step for your portfolio and interview presentations!
