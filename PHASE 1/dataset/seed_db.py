import pandas as pd
from sqlalchemy import create_engine
import os

def save_to_sqlite(df: pd.DataFrame, db_path: str = "sqlite:///zomato.db", table_name: str = "restaurants"):
    """Saves the pandas DataFrame to an SQLite database with full logging."""
    print(f"\n{'='*55}")
    print(f"  Seeding database: {db_path}")
    print(f"{'='*55}")

    # ── Dataset diagnostics ─────────────────────────────
    print(f"\n[INFO] Total dataset rows   : {len(df)}")
    print(f"[INFO] Columns found        : {list(df.columns)}")

    # Detect the location column (handle both 'Location' and 'City')
    loc_col = None
    for candidate in ["Location", "City", "city", "location"]:
        if candidate in df.columns:
            loc_col = candidate
            break

    if loc_col:
        unique_cities = sorted(df[loc_col].dropna().unique().tolist())
        print(f"[INFO] Unique cities ({len(unique_cities)})   : {unique_cities}")
    else:
        print("[WARN] No city/location column found in dataset!")

    # Detect cuisine column
    cuis_col = None
    for candidate in ["Cuisines", "Cuisine", "cuisine", "cuisines"]:
        if candidate in df.columns:
            cuis_col = candidate
            break

    if cuis_col:
        # Split comma-separated cuisines and deduplicate
        all_cuisines = set()
        for val in df[cuis_col].dropna():
            for c in str(val).split(","):
                all_cuisines.add(c.strip())
        print(f"[INFO] Unique cuisines ({len(all_cuisines)})  : {sorted(all_cuisines)}")

    # ── Write to DB ─────────────────────────────────────
    engine = create_engine(db_path)
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"\n[OK] Database seeded: {len(df)} records => table '{table_name}'")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    csv_path = "zomato_cleaned.csv"
    try:
        df = pd.read_csv(csv_path)
        save_to_sqlite(df)
    except FileNotFoundError:
        print(f"[ERROR] '{csv_path}' not found. Please run clean_data.py first.")
