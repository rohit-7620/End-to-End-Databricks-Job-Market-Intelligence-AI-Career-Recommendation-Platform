# Dataset Integration Guide

## Recommended Dataset: LinkedIn Job Postings

### Step 1: Download the Dataset

1. Go to: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
2. Click "Download" (you'll need a Kaggle account)
3. Extract the CSV file

### Step 2: Place the Dataset

Copy the downloaded CSV to:
```
data/raw/job_postings_raw.csv
```

### Step 3: Column Mapping

The LinkedIn dataset has these columns. You'll need to map them to our expected schema:

| LinkedIn Column | Our Expected Column | Notes |
|----------------|---------------------|-------|
| `job_id` | `job_id` | Direct mapping |
| `title` | `job_title` | Direct mapping |
| `company` | `company` | Direct mapping |
| `location` | `location` | Direct mapping |
| `formatted_work_type` | `employment_type` | Full-time, Part-time, etc. |
| `description` | `job_description` | Direct mapping |
| `listed_time` | `posting_date` | May need date format conversion |
| `formatted_experience_level` | `experience_level` | Entry level, Mid-Senior, etc. |
| `skills_desc` or extract from description | `required_skills` | May need parsing |
| `salary` or `pay_period` | `salary` | May be in various formats |

### Step 4: Modify Data Ingestion

Option A: **Update the ingestion notebook** (01_data_ingestion.py):

```python
# In notebook 01_data_ingestion.py, replace the synthetic generation with:

USE_SYNTHETIC = False  # Set to False

# Read the real dataset
import pandas as pd
csv_path = os.path.join(REPO_ROOT, "data", "raw", "linkedin_jobs.csv")
pdf = pd.read_csv(csv_path)

# Map columns to expected schema
pdf = pdf.rename(columns={
    'title': 'job_title',
    'company': 'company',
    'location': 'location',
    'formatted_work_type': 'employment_type',
    'description': 'job_description',
    'listed_time': 'posting_date',
    'formatted_experience_level': 'experience_level',
    # Add salary and skills mapping based on actual columns
})

# Select only required columns
required_columns = [
    'job_id', 'job_title', 'company', 'location', 
    'experience_level', 'salary', 'required_skills', 
    'job_description', 'employment_type', 'posting_date'
]

# Add missing columns as None if they don't exist
for col in required_columns:
    if col not in pdf.columns:
        pdf[col] = None

pdf = pdf[required_columns]
```

Option B: **Create a preprocessing script**:

Create `src/preprocess_linkedin_data.py`:

```python
import pandas as pd
import os

def preprocess_linkedin_data(input_path, output_path):
    """
    Convert LinkedIn dataset to our expected format.
    """
    # Read LinkedIn data
    df = pd.read_csv(input_path)
    
    # Column mapping
    column_map = {
        'title': 'job_title',
        'company': 'company',
        'location': 'location',
        'formatted_work_type': 'employment_type',
        'description': 'job_description',
        'listed_time': 'posting_date',
        'formatted_experience_level': 'experience_level',
    }
    
    df = df.rename(columns=column_map)
    
    # Extract skills from description if not available
    if 'required_skills' not in df.columns:
        df['required_skills'] = None  # Will be extracted in Silver layer
    
    # Generate job_id if not present
    if 'job_id' not in df.columns:
        df['job_id'] = df.index.astype(str)
    
    # Add salary column if missing
    if 'salary' not in df.columns:
        df['salary'] = None
    
    # Select final columns
    final_columns = [
        'job_id', 'job_title', 'company', 'location',
        'experience_level', 'salary', 'required_skills',
        'job_description', 'employment_type', 'posting_date'
    ]
    
    df = df[final_columns]
    
    # Save
    df.to_csv(output_path, index=False)
    print(f"Preprocessed {len(df)} records -> {output_path}")
    
    return df

if __name__ == "__main__":
    input_file = "data/raw/linkedin_jobs_original.csv"
    output_file = "data/raw/job_postings_raw.csv"
    preprocess_linkedin_data(input_file, output_file)
```

### Step 5: Alternative Datasets

#### Option 1: Mix Multiple Datasets
You can combine multiple datasets for richer data:
- LinkedIn for tech jobs
- Naukri for India-specific jobs
- Glassdoor for salary data

#### Option 2: Use Synthetic + Real Data
Keep some synthetic data and add real data on top for testing.

### Step 6: Validate the Data

After preprocessing, validate your data:

```python
import pandas as pd

df = pd.read_csv("data/raw/job_postings_raw.csv")

print(f"Total records: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nSample data:")
print(df.head())
print(f"\nMissing values:")
print(df.isnull().sum())
print(f"\nUnique job titles: {df['job_title'].nunique()}")
print(f"Unique companies: {df['company'].nunique()}")
```

## Quick Start Commands

```bash
# 1. Download dataset from Kaggle
# (Manual step - download from website)

# 2. Preprocess the data
python src/preprocess_linkedin_data.py

# 3. Verify the data
python -c "import pandas as pd; df = pd.read_csv('data/raw/job_postings_raw.csv'); print(f'Loaded {len(df)} rows')"

# 4. Run the pipeline
# Upload to Databricks and run notebooks 00-08 in order
```

## Important Notes

1. **Skills Extraction**: If the dataset doesn't have a dedicated skills column, the Silver layer's skill extractor will parse them from the job description using NLP.

2. **Salary Formats**: Different datasets have different salary formats (annual, monthly, hourly). The Silver layer's `normalize_salary()` function handles multiple formats.

3. **Data Quality**: Real datasets are messy (duplicates, missing values, inconsistent formats) - that's exactly what this pipeline is designed to handle!

4. **Size Considerations**: 
   - For testing: Use 1,000-5,000 rows
   - For demo: Use 5,000-20,000 rows
   - For production: Use 50,000+ rows

## Testing the Integration

Before running in Databricks:

```bash
# Generate a small test file
python src/data_generator.py  # Creates 1000 rows for testing

# Run tests to ensure transformations work
pytest tests/ -v

# Once working, replace with real data
```
