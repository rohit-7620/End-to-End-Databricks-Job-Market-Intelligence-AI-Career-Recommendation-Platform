"""
preprocess_postings.py
-----------------------
Preprocesses the postings.csv file to match the expected schema for the pipeline.

This script reads src/postings.csv (LinkedIn Job Postings dataset) and converts
it to the format expected by the Bronze layer.

Usage:
    python src/preprocess_postings.py
"""

import pandas as pd
import os
import sys


def preprocess_postings(input_path, output_path, max_rows=None):
    """
    Convert postings.csv to our expected format.
    
    Parameters
    ----------
    input_path : str
        Path to the postings.csv file
    output_path : str
        Path where the preprocessed CSV will be saved
    max_rows : int, optional
        Limit number of rows for testing (None = use all data)
    """
    print(f"Reading job postings from: {input_path}")
    print("This may take a moment for large files...")
    
    try:
        # Read the CSV (limit rows if specified for testing)
        if max_rows:
            df = pd.read_csv(input_path, nrows=max_rows)
            print(f"Loaded first {len(df):,} records (testing mode)")
        else:
            df = pd.read_csv(input_path)
            print(f"Loaded {len(df):,} records")
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    
    print(f"\nOriginal columns: {df.columns.tolist()}")
    
    # Column mapping
    df_mapped = pd.DataFrame()
    
    # Direct mappings
    df_mapped['job_id'] = df['job_id'].astype(str)
    df_mapped['job_title'] = df['title']
    df_mapped['company'] = df['company_name']
    df_mapped['location'] = df['location']
    df_mapped['experience_level'] = df['formatted_experience_level']
    df_mapped['job_description'] = df['description']
    df_mapped['employment_type'] = df['formatted_work_type']
    df_mapped['posting_date'] = df['listed_time']
    
    # Handle skills
    df_mapped['required_skills'] = df['skills_desc']
    
    # Handle salary - combine salary information
    def format_salary(row):
        """Combine salary columns into a readable format"""
        if pd.notna(row.get('med_salary')):
            if pd.notna(row.get('pay_period')):
                return f"{row['currency']} {int(row['med_salary'])} {row['pay_period']}"
            return f"{row['currency']} {int(row['med_salary'])}"
        elif pd.notna(row.get('min_salary')) and pd.notna(row.get('max_salary')):
            return f"{row['currency']} {int(row['min_salary'])} - {int(row['max_salary'])}"
        elif pd.notna(row.get('normalized_salary')):
            return f"{int(row['normalized_salary'])}"
        return None
    
    print("\nProcessing salary information...")
    df_mapped['salary'] = df.apply(format_salary, axis=1)
    
    # Remove rows where critical fields are all null
    print("\nCleaning data...")
    df_clean = df_mapped[
        df_mapped['job_title'].notna() | 
        df_mapped['company'].notna() | 
        df_mapped['job_description'].notna()
    ].copy()
    
    print(f"Removed {len(df_mapped) - len(df_clean):,} rows with all critical fields null")
    
    # Save preprocessed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    
    print(f"\n✅ SUCCESS! Preprocessed {len(df_clean):,} records -> {output_path}")
    
    return df_clean


def analyze_dataset(df):
    """Quick analysis of the preprocessed dataset."""
    print("\n" + "="*70)
    print("DATASET ANALYSIS")
    print("="*70)
    print(f"Total records: {len(df):,}")
    
    print(f"\n📊 Missing values per column:")
    missing = df.isnull().sum()
    for col, count in missing.items():
        pct = (count / len(df)) * 100
        print(f"  {col:25s}: {count:8,} ({pct:5.1f}%)")
    
    print(f"\n📈 Unique values:")
    print(f"  Unique job titles: {df['job_title'].nunique():,}")
    print(f"  Unique companies: {df['company'].nunique():,}")
    print(f"  Unique locations: {df['location'].nunique():,}")
    
    print(f"\n🎯 Employment types:")
    if df['employment_type'].notna().sum() > 0:
        print(df['employment_type'].value_counts().head(5))
    
    print(f"\n🎓 Experience levels:")
    if df['experience_level'].notna().sum() > 0:
        print(df['experience_level'].value_counts())
    
    print(f"\n🔍 Sample job postings:")
    print(df[['job_id', 'job_title', 'company', 'location']].head(5))
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # Paths
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    INPUT_FILE = os.path.join(REPO_ROOT, "src", "postings.csv")
    OUTPUT_FILE = os.path.join(REPO_ROOT, "data", "raw", "job_postings_raw.csv")
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: File not found: {INPUT_FILE}")
        print("\nPlease ensure postings.csv is in the src/ folder")
        sys.exit(1)
    
    # Get file size
    file_size_mb = os.path.getsize(INPUT_FILE) / (1024 * 1024)
    print(f"File size: {file_size_mb:.1f} MB")
    
    # Ask user if they want to test with subset first
    print("\n" + "="*70)
    print("OPTIONS:")
    print("  1. Process all data (123K+ rows - recommended for final run)")
    print("  2. Process first 10,000 rows (quick test)")
    print("  3. Process first 1,000 rows (very quick test)")
    print("="*70)
    
    # For automation, default to option 2 (10K rows for testing)
    # Change to None for full dataset
    MAX_ROWS = None  # Process ALL 123K rows!
    
    if MAX_ROWS:
        print(f"\n▶ Processing first {MAX_ROWS:,} rows (testing mode)")
        print("  To process all data, set MAX_ROWS = None in this script\n")
    else:
        print("\n▶ Processing ALL data (this may take 1-2 minutes)...\n")
    
    # Preprocess
    df = preprocess_postings(INPUT_FILE, OUTPUT_FILE, max_rows=MAX_ROWS)
    
    # Analyze
    analyze_dataset(df)
    
    print("\n✅ PREPROCESSING COMPLETE!")
    print(f"\n📁 Output file: {OUTPUT_FILE}")
    print(f"📊 Ready for pipeline: {len(df):,} job postings")
    
    print("\n🚀 NEXT STEPS:")
    print("="*70)
    print("1. Review the preprocessed data in: data/raw/job_postings_raw.csv")
    print("2. To process ALL data, set MAX_ROWS = None and re-run")
    print("3. Run tests: pytest tests/ -v")
    print("4. For Databricks:")
    print("   - Upload this repo to Databricks as a Repo")
    print("   - In notebook 01_data_ingestion.py, set: USE_SYNTHETIC = False")
    print("   - Run notebooks 00-08 in order")
    print("="*70)
