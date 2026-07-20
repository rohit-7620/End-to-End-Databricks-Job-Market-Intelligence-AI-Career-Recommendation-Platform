# Dataset Setup Guide - Quick Reference

## 🎯 Recommended Dataset

**LinkedIn Job Postings from Kaggle**
- **URL**: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
- **Size**: 33,000+ real job postings
- **Format**: CSV
- **Perfect for**: This project (has all required fields)

## 📥 Quick Setup (3 Steps)

### Step 1: Download the Dataset

1. Visit: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
2. Click "Download" (requires free Kaggle account)
3. Extract the downloaded ZIP file
4. You'll get a file like `job_postings.csv` or `postings.csv`

### Step 2: Place the File

Copy the CSV file to:
```
data/raw/
```

Supported filenames (any of these will work):
- `linkedin_jobs_original.csv`
- `job_postings.csv`
- `linkedin_job_postings.csv`
- `postings.csv`

### Step 3: Run Preprocessing

```bash
python src/preprocess_linkedin_data.py
```

This will:
- Read your downloaded LinkedIn CSV
- Map columns to the expected schema
- Generate `data/raw/job_postings_raw.csv` (ready for the pipeline)
- Show you a data quality report

## 🔄 What Happens Next

The preprocessing script converts:

| LinkedIn Column | → | Our Column |
|----------------|---|------------|
| title | → | job_title |
| company | → | company |
| location | → | location |
| formatted_work_type | → | employment_type |
| description | → | job_description |
| listed_time | → | posting_date |
| formatted_experience_level | → | experience_level |

Missing columns (like `salary`, `required_skills`) will be set to `None` and handled by the Silver layer cleaning logic.

## ✅ Verify It Works

After preprocessing, check the output:

```bash
python -c "import pandas as pd; df = pd.read_csv('data/raw/job_postings_raw.csv'); print(f'✅ Loaded {len(df)} rows with {len(df.columns)} columns')"
```

## 🚀 Run the Pipeline

### Option A: In Databricks (Recommended)

1. Upload this entire folder as a Databricks Repo
2. Open `notebooks/01_data_ingestion.py`
3. Set `USE_SYNTHETIC = False` (around line 29)
4. Run notebooks 00-08 in order

### Option B: Local Testing

Generate synthetic data for quick testing:
```bash
python src/data_generator.py
```

Run the test suite:
```bash
pytest tests/ -v
```

## 🎨 Alternative Datasets

### Option 1: Naukri.com Jobs (India-focused)
- **URL**: https://www.kaggle.com/datasets/PromptCloudHQ/us-technology-jobs-on-naukri
- **Good for**: India-specific jobs, INR salaries

### Option 2: Data Science Jobs on Glassdoor
- **URL**: https://www.kaggle.com/datasets/rashikrahmanpritom/data-science-job-posting-on-glassdoor
- **Good for**: Data-focused roles

### Option 3: Indeed Job Postings
- **URL**: https://www.kaggle.com/datasets/promptcloud/jobs-on-naukricom
- **Good for**: Large variety of jobs

## 🔧 Troubleshooting

### Issue: "File not found"
**Solution**: Make sure you placed the CSV in `data/raw/` folder

### Issue: "Column not found"
**Solution**: The preprocessing script handles this automatically - missing columns are added as `None`

### Issue: "Too many rows / Out of memory"
**Solution**: Use only a subset for testing:
```python
# In preprocess_linkedin_data.py, add after reading CSV:
df = df.head(5000)  # Use first 5000 rows only
```

### Issue: Different column names
**Solution**: The preprocessing script tries multiple common names. If your dataset has different columns, edit the `column_map` dictionary in `src/preprocess_linkedin_data.py`

## 📊 Expected Output

After preprocessing, you should see:

```
✅ Preprocessed 33,150 records -> data/raw/job_postings_raw.csv

Column summary:
job_id                  0
job_title               0
company                45
location              120
experience_level     1200
salary              15000
required_skills      5000
job_description         0
employment_type       500
posting_date          150
dtype: int64
```

Missing values are OK! The Silver layer is designed to handle them.

## 🎓 What Makes This Dataset Perfect

1. **Real-world messiness**: Duplicates, missing values, inconsistent formats
2. **Right size**: 30K+ rows (not too small, not too large)
3. **Relevant**: Tech/data jobs that match your use case
4. **Free**: No API keys or paid access required
5. **Recent**: Updated regularly on Kaggle

## Next Steps

Once your dataset is ready:

1. ✅ Preprocess: `python src/preprocess_linkedin_data.py`
2. ✅ Verify: Check `data/raw/job_postings_raw.csv` exists
3. ✅ Upload to Databricks
4. ✅ Run notebooks 00-08
5. ✅ Build your dashboard
6. ✅ Showcase on your resume!

---

**Need help?** Check `docs/dataset_integration_guide.md` for detailed instructions.
