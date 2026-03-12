import sqlite3
import os
from typing import List, Dict

# Assumes the Phase 1 DB is created in root or a specified path. Currently falls back to a default location.
DB_PATH = os.environ.get("DB_PATH", "../PHASE 1/zomato.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_metadata() -> Dict[str, List[str]]:
    """Returns valid locations and cuisines to populate UI dropdowns."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Example queries, assuming 'Location' and 'Cuisines' columns exist in DB 
        cursor.execute("SELECT DISTINCT Location FROM restaurants WHERE Location IS NOT NULL LIMIT 50")
        locations = [row['Location'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT Cuisines FROM restaurants WHERE Cuisines IS NOT NULL LIMIT 50")
        # further logic would be needed to split comma-separated cuisines if applicable, returning raw for now
        cuisines = [row['Cuisines'] for row in cursor.fetchall()]
        
        conn.close()
        return {
            "locations": sorted(locations),
            "cuisines": sorted(cuisines)
        }
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return {"locations": [], "cuisines": []}

def filter_restaurants(location: str, min_rating: float, cuisine: str, max_price: float) -> List[Dict]:
    """
    Performs deterministic hard-filtering on the database before passing to LLM.
    Acts as the baseline Recommendation Engine.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Standardized query. 'Cuisines' uses LIKE for substring match.
        query = """
            SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine
            FROM restaurants
            WHERE Location LIKE ?
              AND Rating >= ?
              AND Approx_cost <= ?
              AND Cuisines LIKE ?
            ORDER BY Rating DESC, Approx_cost ASC
            LIMIT 20
        """
        
        params = (f"%{location}%", min_rating, max_price, f"%{cuisine}%")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = [dict(row) for row in rows]
        conn.close()
        return results
    except Exception as e:
        print(f"Database error during filtering: {e}")
        return []
