import sqlite3
import os
import json
import uuid
from typing import Dict, Any

ANALYTICS_DB_PATH = os.environ.get("ANALYTICS_DB_PATH", "analytics.db")

def init_analytics_db():
    """Initializes the SQLite database for tracking metrics and evaluations."""
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            location TEXT,
            cuisine TEXT,
            optional_preferences TEXT,
            llm_cache_hit BOOLEAN,
            results_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_query(location: str, cuisine: str, optional_preferences: str, llm_cache_hit: bool, results_count: int) -> str:
    """Logs the user query and analytics to the DB."""
    query_id = str(uuid.uuid4())
    try:
        conn = sqlite3.connect(ANALYTICS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO queries (id, location, cuisine, optional_preferences, llm_cache_hit, results_count) VALUES (?, ?, ?, ?, ?, ?)",
            (query_id, location, cuisine, optional_preferences or "", llm_cache_hit, results_count)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics logging failed: {e}")
    return query_id

# Initialize DB on load
init_analytics_db()
