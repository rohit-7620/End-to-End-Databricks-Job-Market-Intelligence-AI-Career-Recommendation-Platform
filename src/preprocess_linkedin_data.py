"""
preprocess_linkedin_data.py
-----------------------------
Preprocesses the LinkedIn Job Postings dataset from Kaggle to match
the expected schema for this pipeline.

Dataset: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings

Usage:
    python src/preprocess_linkedin_data.py

This will read the downloaded LinkedIn CSV and convert it to the format
expected by the Bronze layer (01_data_ingestion.py).
"""

import pandas as pd
import os
import sys


def preprocess_linkedin_data(input_path, output_path):
    """
    Convert LinkedIn dataset to our expected format.
    
    Parameters
    ----------
    input_path : str
        Path to the downloaded LinkedIn jobs CSV
    output_path : str
        Path where the preprocessed CSV will be saved
    
    Returns
    -------
    pd.DataFrame
        Preprocessed dataframe
    """
    print(f"Reading LinkedIn data from: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}")
        print("\nPlease download the dataset from:")
        print("https://www.kaggle.com/datasets/arshkon/linkedin-job-postings")
        print(f"And place it at: {input_path}")
        sys.exit(1)
    
    print(f"Loaded {len(df)} records")
    print(f"Columns in source data: {df.columns.tolist()}")
    
    # Column mapping (adjust based on actual LinkedIn dataset columns)
    column_map = {}
    
    # Try to map common column names
    if 'title' in df.columns:
        column_map['title'] = 'job_title'
    elif 'job_title' not in df.columns:
        df['job_title'] = df.iloc[:, 0]  # Use first column as fallback
    
    if 'company' in df.columns or 'company_name' in df.columns:
        if 'company' in df.columns:
            column_map['company'] = 'company'
        else:
            column_map['company_name'] = 'company'
    
    if 'location' in df.columns:
        column_map['location'] = 'location'
    
    if 'formatted_work_type' in df.columns:
        column_map['formatted_work_type'] = 'employment_type'
    elif 'work_type' in df.columns:
        column_map['work_type'] = 'employment_type'
    
    if 'description' in df.columns:
        column_map['description'] = 'job_description'
    elif 'job_description' not in df.columns:
        df['job_description'] = ''
    
    if 'listed_time' in df.columns:
        column_map['listed_time'] = 'posting_date'
    elif 'posted_date' in df.columns:
        column_map['posted_date'] = 'posting_date'
    
    if 'formatted_experience_level' in df.columns:
        column_map['formatted_experience_level'] = 'experience_level'
    elif 'experience_level' not in df.columns:
        df['experience_level'] = None
    
    # Apply column mapping
    df = df.rename(columns=column_map)
    
    # Generate job_id if not present
    if 'job_id' not in df.columns:
        df['job_id'] = ['job_' + str(i).zfill(8) for i in range(len(df))]
        print("Generated job_id column")
    
    # Add required_skills column
    # LinkedIn dataset might have this in skills_desc or needs extraction
    if 'required_skills' not in df.columns:
        if 'skills_desc' in df.columns:
            df['required_skills'] = df['skills_desc']
        elif 'skills' in df.columns:
            df['required_skills'] = df['skills']
        else:
            # Extract from description or set as None (will be extracted in Silver layer)
            df['required_skills'] = None
            print("required_skills not found - will be extracted from job_description in Silver layer")
    
    # Add salary column if missing
    if 'salary' not in df.columns:
        # Check for salary-related columns
        if 'pay_period' in df.columns:
            df['salary'] = df['pay_period']
        elif 'compensation' in df.columns:
            df['salary'] = df['compensation']
        else:
            df['salary'] = None
            print("salary column not found - set to None")
    
    # Ensure all required columns exist
    required_columns = [
        'job_id', 'job_title', 'company', 'location',
        'experience_level', 'salary', 'required_skills',
        'job_description', 'employment_type', 'posting_date'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
            print(f"Added missing column: {col}")
    
    # Select only required columns in the correct order
    df_final = df[required_columns].copy()
    
    # Basic cleaning
    # Remove rows where critical fields are ALL null
    df_final = df_final[
        df_final['job_title'].notna() | 
        df_final['company'].notna() | 
        df_final['job_description'].notna()
    ]
    
    # Save preprocessed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False)
    
    print(f"\n✅ Preprocessed {len(df_final)} records -> {output_path}")
    print(f"\nColumn summary:")
    print(df_final.isnull().sum())
    print(f"\nSample data:")
    print(df_final.head(3))
    
    return df_final


def analyze_dataset(csv_path):
    """Quick analysis of the preprocessed dataset."""
    df = pd.read_csv(csv_path)
    
    print("\n" + "="*60)
    print("DATASET ANALYSIS")
    print("="*60)
    print(f"Total records: {len(df):,}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nMissing values per column:")
    print(df.isnull().sum())
    print(f"\nData types:")
    print(df.dtypes)
    print(f"\nUnique job titles: {df['job_title'].nunique():,}")
    print(f"Unique companies: {df['company'].nunique():,}")
    print(f"Unique locations: {df['location'].nunique():,}")
    print(f"\nSample records:")
    print(df.head())


if __name__ == "__main__":
    # Paths
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Input: Downloaded LinkedIn dataset (adjust filename as needed)
    INPUT_FILE = os.path.join(REPO_ROOT, "data", "raw", "linkedin_jobs_original.csv")
    
    # Alternative common filenames to try
    alternative_files = [
        "job_postings.csv",
        "linkedin_job_postings.csv", 
        "postings.csv",
    ]
    
    # Try to find the input file
    if not os.path.exists(INPUT_FILE):
        print(f"⚠️  Primary file not found: {INPUT_FILE}")
        print("\nSearching for alternative files...")
        
        for alt_file in alternative_files:
            alt_path = os.path.join(REPO_ROOT, "data", "raw", alt_file)
            if os.path.exists(alt_path):
                INPUT_FILE = alt_path
                print(f"✅ Found: {INPUT_FILE}")
                break
        else:
            print("\n❌ No LinkedIn dataset found!")
            print("\nPlease download from:")
            print("https://www.kaggle.com/datasets/arshkon/linkedin-job-postings")
            print(f"\nAnd place the CSV file in: {os.path.join(REPO_ROOT, 'data', 'raw')}")
            print("\nSupported filenames:")
            for f in alternative_files:
                print(f"  - {f}")
            sys.exit(1)
    
    # Output: Standardized format for the pipeline
    OUTPUT_FILE = os.path.join(REPO_ROOT, "data", "raw", "job_postings_raw.csv")
    
    # Preprocess
    df = preprocess_linkedin_data(INPUT_FILE, OUTPUT_FILE)
    
    # Analyze
    analyze_dataset(OUTPUT_FILE)
    
    print("\n✅ Preprocessing complete!")
    print(f"\nNext steps:")
    print("1. Review the preprocessed data in: data/raw/job_postings_raw.csv")
    print("2. In notebook 01_data_ingestion.py, set: USE_SYNTHETIC = False")
    print("3. Upload this repo to Databricks and run notebooks 00-08 in order")
