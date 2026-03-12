import streamlit as st
import os
import sys
import sqlite3
from typing import List, Dict
import json
import hashlib
from groq import Groq

# Add PHASE 5 to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'PHASE 5'))

# Load environment variables
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), 'PHASE 3', '.env')
load_dotenv(dotenv_path=_env_path, override=True)

# Database configuration
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.normpath(os.path.join(_THIS_DIR, 'PHASE 1', 'zomato.db'))
DB_PATH = os.environ.get("DB_PATH", _DEFAULT_DB)

# In-memory cache for LLM responses
LLM_CACHE: Dict[str, List[Dict]] = {}

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

        cursor.execute("SELECT Cuisines FROM restaurants WHERE Cuisines IS NOT NULL")
        cuisine_set = set()
        for row in cursor.fetchall():
            for c in row['Cuisines'].split(','):
                stripped = c.strip()
                if stripped:
                    cuisine_set.add(stripped)
        cuisines = sorted(cuisine_set)

        conn.close()
        return {"locations": locations, "cuisines": cuisines}
    except Exception as e:
        st.error(f"Error loading metadata: {e}")
        return {"locations": [], "cuisines": []}

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
    return related[:3]

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
                    return results[:10]

        # Step 3: Relax rating constraint (reduce by 0.5)
        if len(results) < 3:
            relaxed_rating = max(1.0, min_rating - 0.5)
            relaxed_results = _execute_filtered_query(cursor, location, relaxed_rating, cuisine, max_price)
            results.extend(relaxed_results)
            results = _remove_duplicates(results)
            if len(results) >= 3:
                conn.close()
                return results[:10]

        # Step 4: Return top-rated restaurants in selected locality
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

        # Step 5: Return top-rated restaurants across Bangalore
        if len(results) < 3:
            fallback_query = """
                SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine
                FROM restaurants
                WHERE Rating >= ?
                ORDER BY Rating DESC, Approx_cost ASC
                LIMIT 10
            """
            cursor.execute(fallback_query, (3.5,))
            fallback_results = [dict(row) for row in cursor.fetchall()]
            results.extend(fallback_results)
            results = _remove_duplicates(results)

        conn.close()
        
        # Ensure we always return at least 3 results
        if len(results) < 3:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Name as name, Location as location, Rating as rating, Approx_cost as cost, Cuisines as cuisine FROM restaurants ORDER BY Rating DESC LIMIT 3")
            emergency_results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            results.extend(emergency_results)
            results = _remove_duplicates(results)

        return results[:10]

    except Exception as e:
        st.error(f"Error filtering restaurants: {e}")
        return []

def generate_explanation_for_restaurant(restaurant: Dict, optional_preferences: str = "") -> str:
    """Generate a vibe explanation for a single restaurant using Groq."""
    try:
        # Check for API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return f"{restaurant.get('name', 'Restaurant')} offers great dining options in {restaurant.get('location', 'Bangalore')}."
        
        # Extract restaurant data
        name = restaurant.get('name', 'Unknown Restaurant')
        location = restaurant.get('location', 'N/A')
        cuisine = restaurant.get('cuisine', 'Various')
        rating = restaurant.get('rating', 'N/A')
        cost = restaurant.get('cost', 'N/A')
        
        # Build the exact prompt structure
        prompt = (
            f"Generate a restaurant explanation following this exact structure:\n\n"
            f"[Restaurant Name] in [Location] is a great match for someone looking for\n"
            f"[Cuisine] cuisine because it serves a variety of [Cuisine foods]\n"
            f"and has a rating of [rating].\n\n"
            f"With a cost of [price], it fits within your budget.\n\n"
            f"Replace the brackets with this data:\n"
            f"- Restaurant Name: {name}\n"
            f"- Location: {location}\n"
            f"- Cuisine: {cuisine}\n"
            f"- Rating: {rating}\n"
            f"- Price: {cost}\n\n"
            f"Return only the completed explanation text, nothing else."
        )

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )

        explanation = response.choices[0].message.content.strip()
        return explanation

    except Exception as e:
        st.warning(f"Could not generate AI explanation for {restaurant.get('name', 'Unknown')}: {str(e)}")
        # Return fallback explanation
        return f"{restaurant.get('name', 'Restaurant')} in {restaurant.get('location', 'Bangalore')} offers great {restaurant.get('cuisine', 'cuisine')} with a rating of {restaurant.get('rating', 'N/A')} and fits your budget at {restaurant.get('cost', 'N/A')}."

def process_with_llm(restaurants: List[Dict], optional_preferences: str) -> List[Dict]:
    """Process restaurants to add vibe explanations."""
    if not restaurants:
        return []

    # Generate explanations for each restaurant
    final_restaurants = []
    
    for restaurant in restaurants[:5]:  # Process up to 5 restaurants
        # Generate explanation for this restaurant
        explanation = generate_explanation_for_restaurant(restaurant, optional_preferences)
        
        # Add the explanation to the restaurant object
        restaurant_copy = restaurant.copy()
        restaurant_copy["vibe_explanation"] = explanation
        
        final_restaurants.append(restaurant_copy)
    
    # Ensure we always return at least 3 restaurants
    if len(final_restaurants) < 3 and len(restaurants) > len(final_restaurants):
        remaining_restaurants = restaurants[len(final_restaurants):]
        for restaurant in remaining_restaurants[:3-len(final_restaurants)]:
            restaurant_copy = restaurant.copy()
            restaurant_copy["vibe_explanation"] = f"{restaurant.get('name', 'Restaurant')} in {restaurant.get('location', 'Bangalore')} offers {restaurant.get('cuisine', 'various cuisines')} with a rating of {restaurant.get('rating', 'N/A')}."
            final_restaurants.append(restaurant_copy)
    
    return final_restaurants

def get_recommendations(location: str, cuisines: List[str], min_rating: float, max_price: float, vibe: str) -> List[Dict]:
    """Main recommendation function."""
    all_results = []
    
    # Get recommendations for each selected cuisine
    for cuisine in cuisines:
        results = filter_restaurants(location, min_rating, cuisine, max_price)
        all_results.extend(results)
    
    # Remove duplicates across cuisines
    unique_results = _remove_duplicates(all_results)
    
    # Sort by rating and cost
    unique_results.sort(key=lambda x: (-x.get('rating', 0), x.get('cost', float('inf'))))
    
    # Generate explanations
    final_results = process_with_llm(unique_results[:10], vibe)
    
    return final_results[:5]  # Return top 5

def display_restaurant_card(restaurant: Dict):
    """Display a single restaurant card."""
    name = restaurant.get('name', 'Unknown Restaurant')
    rating = restaurant.get('rating', 'N/A')
    location = restaurant.get('location', 'N/A')
    cuisine = restaurant.get('cuisine', 'Various')
    cost = restaurant.get('cost', 'N/A')
    explanation = restaurant.get('vibe_explanation', 'No explanation available.')
    
    # Create card container
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 🍽️ {name}")
            st.markdown(f"**📍 Location:** {location}")
            st.markdown(f"**🍴 Cuisine:** {cuisine}")
            st.markdown(f"**💰 Cost for Two:** ₹{cost}")
        
        with col2:
            st.markdown(f"## ⭐ {rating}")
        
        st.markdown("### Why this could be a perfect option")
        st.markdown(explanation)
        st.markdown("---")

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Zomato AI Recommender",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        .card-container {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🍽️ Zomato AI Recommender</h1>', unsafe_allow_html=True)
    st.markdown("### Find your perfect dining experience with AI-powered recommendations")
    
    # Load metadata
    metadata = get_metadata()
    locations = metadata.get('locations', [])
    all_cuisines = metadata.get('cuisines', [])
    
    # Sidebar for preferences
    st.sidebar.markdown("## 🎯 Your Preferences")
    
    # Location selection
    location = st.sidebar.selectbox(
        "📍 Select Location",
        options=locations,
        index=0 if locations else None,
        help="Choose your preferred area in Bangalore"
    )
    
    # Multi-cuisine selection
    selected_cuisines = st.sidebar.multiselect(
        "🍴 Select Cuisines (Multiple)",
        options=all_cuisines,
        default=[],
        help="Choose multiple cuisines you're interested in"
    )
    
    # Rating slider
    min_rating = st.sidebar.slider(
        "⭐ Minimum Rating",
        min_value=1.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
        help="Minimum restaurant rating you're looking for"
    )
    
    # Budget slider
    max_price = st.sidebar.slider(
        "💰 Max Budget for Two",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
        help="Maximum cost for two people"
    )
    
    # Vibe preferences
    vibe = st.sidebar.text_area(
        "✨ Your Vibe",
        placeholder="Describe your perfect dining experience... (e.g., 'A quiet place for a romantic date, not too crowded')",
        help="Tell us about the atmosphere or occasion you're looking for"
    )
    
    # Get recommendations button
    if st.sidebar.button("🚀 Get Recommendations", type="primary"):
        if not location:
            st.sidebar.error("Please select a location!")
            return
        
        if not selected_cuisines:
            st.sidebar.error("Please select at least one cuisine!")
            return
        
        # Show loading spinner
        with st.spinner("🤖 AI is finding the perfect restaurants for you..."):
            try:
                recommendations = get_recommendations(location, selected_cuisines, min_rating, max_price, vibe)
                
                if recommendations:
                    st.success(f"🎉 Found {len(recommendations)} amazing restaurants for you!")
                    
                    # Display recommendations
                    for i, restaurant in enumerate(recommendations, 1):
                        st.markdown(f"## 🏆 Recommendation #{i}")
                        display_restaurant_card(restaurant)
                else:
                    st.error("😔 Couldn't find any restaurants. Please try different filters!")
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🤖 Powered by Groq LLM | 🍽️ Zomato Dataset | 💝 Made with ❤️"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
