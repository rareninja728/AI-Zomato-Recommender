import pandas as pd
import numpy as np
import re

def parse_rating(val):
    """Parses rating like '4.1 /5' or 'NEW' or '-'."""
    if pd.isna(val):
        return 0.0
    val = str(val).split('/')[0].strip()
    try:
        if val.upper() in ['NEW', '-', '']:
            return 0.0
        return float(val)
    except ValueError:
        return 0.0

def parse_cost(val):
    """Parses cost like '1,200'."""
    if pd.isna(val):
        return 0.0
    val = str(val).replace(',', '').strip()
    try:
        return float(val)
    except ValueError:
        return 0.0

def clean_zomato_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and normalizes the Bangalore Zomato dataset."""
    print(f"Cleaning dataset with {len(df)} records...")
    
    # 1. Map columns if they exist
    mapping = {
        'name': 'Name',
        'location': 'Location',
        'rate': 'Rating',
        'approx_cost(for two people)': 'Approx_cost',
        'cuisines': 'Cuisines'
    }
    
    # Filter for columns that actually exist in the dataframe
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    
    # 2. Keep only columns we need for the recommendation engine
    target_columns = ['Name', 'Location', 'Rating', 'Approx_cost', 'Cuisines']
    available_cols = [c for c in target_columns if c in df.columns]
    df = df[available_cols].copy()
    
    # 3. Drop rows missing critical information
    df = df.dropna(subset=['Name', 'Location', 'Cuisines'])
    
    # 4. Parse Rating (e.g., "4.1/5" -> 4.1)
    if 'Rating' in df.columns:
        df['Rating'] = df['Rating'].apply(parse_rating)
        
    # 5. Parse Cost (e.g., "1,200" -> 1200)
    if 'Approx_cost' in df.columns:
        df['Approx_cost'] = df['Approx_cost'].apply(parse_cost)
    
    # 6. Final string cleaning
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    # 7. Remove duplicates
    df = df.drop_duplicates()
        
    print(f"Cleaned dataset. Remaining records: {len(df)}")
    return df

if __name__ == "__main__":
    try:
        # Load raw data
        raw_df = pd.read_csv("zomato_raw.csv")
        cleaned_df = clean_zomato_data(raw_df)
        
        # Save cleaned data
        cleaned_df.to_csv("zomato_cleaned.csv", index=False)
        print("Cleaned data saved to zomato_cleaned.csv")
        
        # Display some info
        print("\nSummary Statistics:")
        print(f"Total Restaurants: {len(cleaned_df)}")
        print(f"Unique Localities: {cleaned_df['Location'].nunique()}")
        print(f"Average Rating: {cleaned_df['Rating'][cleaned_df['Rating'] > 0].mean():.2f}")
        
    except FileNotFoundError:
        print("Error: zomato_raw.csv not found. Please run fetch_dataset.py first.")
    except Exception as e:
        print(f"An error occurred during cleaning: {e}")
