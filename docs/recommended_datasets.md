# Recommended Real-World Datasets

## 🥇 Best Choice: LinkedIn Job Postings

### Dataset Information
- **Name**: LinkedIn Job Postings (2023-2024)
- **URL**: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
- **Size**: 33,000+ job postings
- **Format**: CSV
- **Update Frequency**: Regularly updated
- **License**: CC0 (Public Domain)

### Why This is Perfect
✅ Has all required fields (title, company, location, skills, experience, etc.)  
✅ Real-world data with natural messiness (perfect for your cleaning pipeline)  
✅ Tech-focused jobs (Data Engineer, Data Scientist, ML Engineer, etc.)  
✅ Global locations including India  
✅ Free to download (just needs Kaggle account)  
✅ Large enough to be impressive (30K+ rows)  
✅ Recent data (2023-2024)  

### Key Columns Available
- `job_id` - Unique identifier
- `title` - Job title (needs standardization - perfect!)
- `company` - Company name
- `location` - Job location
- `description` - Full job description
- `formatted_work_type` - Full-time, Part-time, Contract
- `formatted_experience_level` - Entry, Mid-Senior, Director
- `listed_time` - When job was posted
- `applies` - Number of applications
- `views` - Number of views
- `skills_desc` - Required skills (may need parsing)

### How to Use
1. Download from Kaggle
2. Place in `data/raw/` folder
3. Run: `python src/preprocess_linkedin_data.py`
4. Set `USE_SYNTHETIC = False` in notebook 01
5. Run the pipeline!

---

## 🥈 Alternative Option 1: Glassdoor Data Science Jobs

### Dataset Information
- **Name**: Data Science Job Postings on Glassdoor
- **URL**: https://www.kaggle.com/datasets/rashikrahmanpritom/data-science-job-posting-on-glassdoor
- **Size**: 672 jobs
- **Focus**: Data Science, ML, Analytics roles

### Why Use This
✅ Highly relevant to your target roles  
✅ Clean salary data  
✅ Detailed job descriptions  
✅ Company ratings included  

### Limitations
⚠️ Smaller dataset (only 672 rows)  
⚠️ US-focused (fewer India locations)  
⚠️ May need more preprocessing  

### Key Columns
- Job Title
- Salary Estimate
- Job Description
- Rating
- Company Name
- Location
- Size
- Industry
- Sector

---

## 🥉 Alternative Option 2: Naukri.com Jobs

### Dataset Information
- **Name**: Technology Jobs on Naukri.com
- **URL**: https://www.kaggle.com/datasets/PromptCloudHQ/us-technology-jobs-on-naukri
- **Size**: 2,500+ jobs
- **Focus**: Technology jobs in India

### Why Use This
✅ India-specific (perfect for Indian location data)  
✅ Salary in INR (matches your project)  
✅ Real company names used in India  
✅ Tech-focused roles  

### Limitations
⚠️ Smaller dataset  
⚠️ May have fewer data engineering roles  
⚠️ Skills might need extraction from descriptions  

### Key Columns
- Job Title
- Job Experience Required
- Key Skills
- Role Category
- Location
- Functional Area
- Industry
- Role

---

## 🎯 Alternative Option 3: Indeed Job Postings

### Dataset Information
- **Name**: Indeed Job Postings
- **URL**: Multiple datasets available on Kaggle - search "Indeed jobs"
- **Size**: Varies (1K - 50K+)
- **Focus**: General jobs across industries

### Why Use This
✅ Large variety of roles  
✅ Multiple datasets to choose from  
✅ Often has complete information  

### Limitations
⚠️ Multiple datasets with different schemas  
⚠️ May include non-tech roles  
⚠️ Needs more filtering  

---

## 🔥 Advanced Option: Combine Multiple Datasets

### The Strategy
Mix 2-3 datasets for richer, more diverse data:

1. **LinkedIn** (30K rows) - Main dataset for tech jobs
2. **Naukri** (2K rows) - Add India-specific jobs
3. **Glassdoor** (600 rows) - Add high-quality salary data

### How to Combine
```python
import pandas as pd

# Load all datasets
linkedin = pd.read_csv('data/raw/linkedin_jobs.csv')
naukri = pd.read_csv('data/raw/naukri_jobs.csv')
glassdoor = pd.read_csv('data/raw/glassdoor_jobs.csv')

# Preprocess each to common schema
linkedin_clean = preprocess_linkedin(linkedin)
naukri_clean = preprocess_naukri(naukri)
glassdoor_clean = preprocess_glassdoor(glassdoor)

# Combine
combined = pd.concat([linkedin_clean, naukri_clean, glassdoor_clean], ignore_index=True)

# Remove duplicates
combined = combined.drop_duplicates(subset=['job_title', 'company', 'location'])

# Save
combined.to_csv('data/raw/job_postings_raw.csv', index=False)
```

---

## 🆚 Dataset Comparison Table

| Dataset | Rows | Tech Focus | India Jobs | Salary Data | Skills Data | Difficulty |
|---------|------|------------|------------|-------------|-------------|------------|
| **LinkedIn** | 33K+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Easy |
| Glassdoor | 672 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Medium |
| Naukri | 2.5K | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |
| Indeed | Varies | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Hard |
| **Combined** | 36K+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |

---

## 📋 Required Columns Checklist

Your dataset needs these columns (or we can derive them):

✅ **Must Have:**
- [ ] Job ID (or can be generated)
- [ ] Job Title (raw is fine - we standardize it)
- [ ] Company Name
- [ ] Location

✅ **Should Have:**
- [ ] Job Description (for skill extraction)
- [ ] Experience Level (or can derive from title)
- [ ] Employment Type (Full-time, Part-time, etc.)
- [ ] Posting Date

✅ **Nice to Have:**
- [ ] Salary (many datasets lack this - OK!)
- [ ] Required Skills (or we extract from description)
- [ ] Benefits
- [ ] Remote/Hybrid info

---

## 🎬 Getting Started (Step-by-Step)

### For LinkedIn Dataset (Recommended):

```bash
# Step 1: Download
# Go to: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
# Click "Download"

# Step 2: Extract and place
# Unzip the downloaded file
# Copy the CSV to: data/raw/job_postings.csv

# Step 3: Preprocess
python src/preprocess_linkedin_data.py

# Step 4: Verify
python -c "import pandas as pd; print(pd.read_csv('data/raw/job_postings_raw.csv').shape)"

# Step 5: Update notebook
# In notebooks/01_data_ingestion.py, set:
# USE_SYNTHETIC = False

# Step 6: Run in Databricks
# Upload to Databricks and run notebooks 00-08
```

---

## 🤔 Still Can't Decide?

**Use LinkedIn!** It's the most complete, largest, and easiest to integrate.

**Why LinkedIn wins:**
1. Largest dataset (33K+ rows - impressive on a resume!)
2. Most complete information (fewer missing values)
3. Perfect for your use case (tech/data jobs)
4. Easy to integrate (our preprocessing script handles it automatically)
5. Recent data (shows you're working with current market trends)
6. Global locations (demonstrates scalability)

---

## 💡 Pro Tips

1. **Start with LinkedIn** - easiest to integrate, most complete
2. **Test with 5K rows** first - faster iteration while testing
3. **Use full dataset** for final demo - more impressive!
4. **Combine datasets** if you want extra credit - shows initiative
5. **Document your choice** - add to your README and demo script

---

## 🚀 Ready to Go?

Quick commands to get started RIGHT NOW:

```bash
# 1. Download LinkedIn dataset from Kaggle (manual step)

# 2. Place in data/raw/

# 3. Run preprocessing
python src/preprocess_linkedin_data.py

# 4. Verify it worked
ls data/raw/job_postings_raw.csv

# 5. You're ready to run the pipeline!
```

---

**Questions?** Check the detailed integration guide: `docs/dataset_integration_guide.md`
