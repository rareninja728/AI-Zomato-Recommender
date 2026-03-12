import pandas as pd
from datasets import load_dataset
import os

def fetch_zomato_data(output_path: str = "zomato_raw.csv") -> pd.DataFrame:
    """Fetches the Zomato restaurant dataset from Hugging Face."""
    print("Fetching dataset from Hugging Face...")
    dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    df = dataset.to_pandas()
    
    # Save raw data
    df.to_csv(output_path, index=False)
    print(f"Data fetched successfully! Saved to {output_path}")
    return df

if __name__ == "__main__":
    fetch_zomato_data()
