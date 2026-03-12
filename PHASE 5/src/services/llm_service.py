import os
import json
import hashlib
import logging
from pathlib import Path
from groq import Groq
from typing import List, Dict, Tuple

# ── Load .env from PHASE 5 directory ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    loaded = load_dotenv(dotenv_path=_env_path, override=True)
    print(f"[llm_service] .env loaded from {_env_path}: {loaded}")
except ImportError:
    print("[llm_service] WARNING: python-dotenv not installed. Install with: pip install python-dotenv")

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── In-memory cache (Phase 5 Optimisation) ────────────────────────────────
LLM_CACHE: Dict[str, List[Dict]] = {}

# ── Groq client initialisation ─────────────────────────────────────────────
def get_groq_client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_cache_key(restaurants: List[Dict], optional_preferences: str) -> str:
    """Generates a unique SHA-256 hash for a given set of candidates + user vibe."""
    rest_names = ",".join([r.get("name", "") for r in restaurants])
    raw_str = f"{rest_names}|{optional_preferences}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def generate_explanation_for_restaurant(restaurant: Dict, optional_preferences: str = "") -> str:
    """
    Generate a vibe explanation for a single restaurant using the exact prompt structure.
    """
    try:
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

        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )

        explanation = response.choices[0].message.content.strip()
        logger.info("[Groq] Generated explanation for %s", name)
        return explanation

    except Exception as e:
        logger.error("[Groq] Failed to generate explanation for %s: %s", restaurant.get('name', 'Unknown'), e)
        # Return fallback explanation
        return f"{name} in {location} offers great {cuisine} cuisine with a rating of {rating} and fits your budget at {cost}."

def process_with_llm(restaurants: List[Dict], optional_preferences: str) -> Tuple[List[Dict], bool]:
    """
    Process restaurants to add vibe explanations.
    Always calls LLM to generate explanations for each restaurant.
    Ensures minimum 3 restaurants are returned.
    Returns (final_list, cache_hit_bool).
    """
    if not restaurants:
        logger.info("[Groq] No candidate restaurants from DB — returning empty list.")
        return [], False

    # Ensure we have at least 3 restaurants to process
    restaurants_to_process = restaurants[:5]  # Process up to 5 restaurants
    
    # Generate explanations for each restaurant
    final_restaurants = []
    
    for restaurant in restaurants_to_process:
        # Generate explanation for this restaurant
        explanation = generate_explanation_for_restaurant(restaurant, optional_preferences)
        
        # Add the explanation to the restaurant object
        restaurant_copy = restaurant.copy()
        restaurant_copy["vibe_explanation"] = explanation
        
        final_restaurants.append(restaurant_copy)
    
    # Ensure we always return at least 3 restaurants
    if len(final_restaurants) < 3 and len(restaurants) > len(final_restaurants):
        # Add remaining restaurants without LLM explanations if needed
        remaining_restaurants = restaurants[len(final_restaurants):]
        for restaurant in remaining_restaurants[:3-len(final_restaurants)]:
            restaurant_copy = restaurant.copy()
            restaurant_copy["vibe_explanation"] = f"{restaurant.get('name', 'Restaurant')} in {restaurant.get('location', 'Bangalore')} offers {restaurant.get('cuisine', 'various cuisines')} with a rating of {restaurant.get('rating', 'N/A')}."
            final_restaurants.append(restaurant_copy)
    
    logger.info("[Groq] Generated explanations for %d restaurants", len(final_restaurants))
    return final_restaurants, False
