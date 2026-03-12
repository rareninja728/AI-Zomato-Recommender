import sqlite3
import os
from typing import List, Dict

# Use an absolute path anchored to this file's directory so it works regardless
# of what directory uvicorn is launched from.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "..", "PHASE 1", "zomato.db"))
DB_PATH = os.environ.get("DB_PATH", _DEFAULT_DB)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_metadata() -> Dict[str, List[str]]:
    """Returns valid locations and cuisines to populate UI dropdowns."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT Location FROM restaurants WHERE Location IS NOT NULL")
        locations = sorted({row['Location'].strip() for row in cursor.fetchall() if row['Location']})

        # Cuisines may be comma-separated (e.g. "North Indian, Chinese") — split and deduplicate
        cursor.execute("SELECT Cuisines FROM restaurants WHERE Cuisines IS NOT NULL")
        cuisine_set = set()
        for row in cursor.fetchall():
            for c in row['Cuisines'].split(','):
                stripped = c.strip()
                if stripped:
                    cuisine_set.add(stripped)
        cuisines = sorted(cuisine_set)

        conn.close()
        print(f"[db_service] DB_PATH resolved to: {DB_PATH}")
        print(f"[db_service] Loaded {len(locations)} locations, {len(cuisines)} cuisines")
        return {"locations": locations, "cuisines": cuisines}
    except Exception as e:
        print(f"[db_service] get_metadata ERROR: {e}")
        return {"locations": [], "cuisines": []}

def filter_restaurants(location: str, min_rating: float, cuisine: str, max_price: float) -> List[Dict]:
    """
    Performs deterministic hard-filtering on the database with fallback strategy.
    Always returns at least 3 restaurants using progressive filter relaxation.
    Removes duplicates based on restaurant name.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Try strict filtering first
        results = _execute_filtered_query(cursor, location, min_rating, cuisine, max_price)
        
        if len(results) >= 3:
            conn.close()
            return _remove_duplicates(results)

        # Step 2: Relax cuisine filter (include related cuisines)
        if len(results) < 3:
            related_cuisines = _get_related_cuisines(cuisine)
            for related_cuisine in related_cuisines:
                additional_results = _execute_filtered_query(cursor, location, min_rating, related_cuisine, max_price)
                results.extend(additional_results)
                results = _remove_duplicates(results)
                if len(results) >= 3:
                    conn.close()
                    return results[:10]  # Return top 10 to avoid too many results

        # Step 3: Relax rating constraint (reduce by 0.5)
        if len(results) < 3:
            relaxed_rating = max(1.0, min_rating - 0.5)
            relaxed_results = _execute_filtered_query(cursor, location, relaxed_rating, cuisine, max_price)
            results.extend(relaxed_results)
            results = _remove_duplicates(results)
            if len(results) >= 3:
                conn.close()
                return results[:10]

        # Step 4: Return top-rated restaurants in selected locality (ignore cuisine and price)
        if len(results) < 3:
            locality_query = """
                SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine
                FROM restaurants
                WHERE Location LIKE ?
                  AND Rating >= ?
                ORDER BY Rating DESC, Approx_cost ASC
                LIMIT 10
            """
            cursor.execute(locality_query, (f"%{location}%", max(1.0, min_rating - 1.0)))
            locality_results = [dict(row) for row in cursor.fetchall()]
            results.extend(locality_results)
            results = _remove_duplicates(results)
            if len(results) >= 3:
                conn.close()
                return results[:10]

        # Step 5: Return top-rated restaurants across Bangalore (ignore all filters)
        if len(results) < 3:
            fallback_query = """
                SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine
                FROM restaurants
                WHERE Rating >= ?
                ORDER BY Rating DESC, Approx_cost ASC
                LIMIT 10
            """
            cursor.execute(fallback_query, (3.5,))  # Minimum reasonable rating
            fallback_results = [dict(row) for row in cursor.fetchall()]
            results.extend(fallback_results)
            results = _remove_duplicates(results)

        conn.close()
        
        # Ensure we always return at least 3 results
        if len(results) < 3:
            # Last resort: return any restaurants from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine FROM restaurants ORDER BY Rating DESC LIMIT 3")
            emergency_results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            results.extend(emergency_results)
            results = _remove_duplicates(results)

        return results[:10]  # Return maximum 10 results

    except Exception as e:
        print(f"[db_service] filter_restaurants ERROR: {e}")
        # Emergency fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine FROM restaurants ORDER BY Rating DESC LIMIT 3")
            emergency_results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return emergency_results
        except:
            return []

def _execute_filtered_query(cursor, location: str, min_rating: float, cuisine: str, max_price: float) -> List[Dict]:
    """Execute the standard filtered query."""
    query = """
        SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine
        FROM restaurants
        WHERE Location LIKE ?
          AND Rating >= ?
          AND Approx_cost <= ?
          AND Cuisines LIKE ?
        ORDER BY Rating DESC, Approx_cost ASC
        LIMIT 30
    """
    params = (f"%{location}%", min_rating, max_price, f"%{cuisine}%")
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def _remove_duplicates(restaurants: List[Dict]) -> List[Dict]:
    """Remove duplicate restaurants based on name."""
    seen_names = set()
    unique_restaurants = []
    
    for restaurant in restaurants:
        name = restaurant.get('name', '').strip().lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_restaurants.append(restaurant)
    
    return unique_restaurants

def _get_related_cuisines(cuisine: str) -> List[str]:
    """Get related cuisines for fallback matching."""
    cuisine_mapping = {
        'bakery': ['cafe', 'desserts', 'pastry', 'confectionery'],
        'cafe': ['bakery', 'desserts', 'coffee', 'tea'],
        'desserts': ['bakery', 'cafe', 'ice cream', 'sweet'],
        'chinese': ['asian', 'thai', 'japanese', 'korean'],
        'italian': ['pizza', 'pasta', 'european', 'mediterranean'],
        'north indian': ['indian', 'mughlai', 'punjabi', 'awadhi'],
        'south indian': ['indian', 'kerala', 'andhra', 'tamil'],
        'burger': ['american', 'fast food', 'cafe'],
        'pizza': ['italian', 'fast food', 'american'],
        'healthy food': ['salad', 'organic', 'vegan', 'health food'],
        'barbecue': ['grill', 'bbq', 'american', 'steak'],
        'seafood': ['fish', 'coastal', 'goan'],
        'vegetarian': ['vegan', 'salad', 'healthy food'],
        'vegan': ['vegetarian', 'salad', 'healthy food']
    }
    
    related = cuisine_mapping.get(cuisine.lower(), [])
    return related[:3]  # Limit to avoid too many results
