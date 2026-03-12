import pytest
import pandas as pd
import sqlite3
import os
import sys

# Add parent dir to path so we can import from dataset
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataset.clean_data import clean_zomato_data
from dataset.seed_db import save_to_sqlite

@pytest.fixture
def sample_raw_data():
    return pd.DataFrame({
        'Name': ['Rest A', None, 'Rest C ', 'Rest D'],
        'Location': ['Loc A', 'Loc B', '  ', 'Loc D'],
        'Rating': ['4.5', 'not a num', None, '3.2'],
        'Approx_cost': ['Rs. 100', '200$', '', '150']
    })

def test_clean_data(sample_raw_data):
    cleaned_df = clean_zomato_data(sample_raw_data)
    
    # 1. Should drop row with no Name (index 1)
    assert len(cleaned_df) == 3 
    
    # 2. Rating should be parsed to numeric float
    assert cleaned_df.iloc[0]['Rating'] == 4.5
    assert cleaned_df.iloc[1]['Rating'] == 0.0 # From None
    assert cleaned_df.iloc[2]['Rating'] == 3.2
    
    # 3. Prices should be parsed (stripping currency symbols)
    assert cleaned_df.iloc[0]['Approx_cost'] == 100.0
    assert cleaned_df.iloc[1]['Approx_cost'] == 0.0 # From empty string
    assert cleaned_df.iloc[2]['Approx_cost'] == 150.0

    # 4. Text stripping
    assert cleaned_df.iloc[1]['Name'] == 'Rest C'

def test_seed_db(tmp_path):
    df = pd.DataFrame({
        'Name': ['Rest A', 'Rest B'],
        'Location': ['Loc A', 'Loc B'],
        'Rating': [4.5, 3.8]
    })
    
    db_file = tmp_path / "test_zomato.db"
    db_uri = f"sqlite:///{db_file}"
    
    save_to_sqlite(df, db_path=db_uri, table_name="test_restaurants")
    
    assert os.path.exists(db_file)
    
    # Verify content in DB
    conn = sqlite3.connect(str(db_file))
    result = pd.read_sql("SELECT * FROM test_restaurants", conn)
    
    assert len(result) == 2
    assert result.iloc[0]['Name'] == 'Rest A'
    assert result.iloc[1]['Rating'] == 3.8
    conn.close()
