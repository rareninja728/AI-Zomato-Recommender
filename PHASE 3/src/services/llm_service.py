import os
import json
from groq import Groq
from typing import List, Dict

# Ensure GROQ_API_KEY is set in your environment variables (.env)
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Groq] ERROR: GROQ_API_KEY not found in environment.")
        return None
    return Groq(api_key=api_key.strip())

def process_with_llm(restaurants: List[Dict], optional_preferences: str) -> List[Dict]:
    """
    Takes a hard-filtered list of restaurants and the user's natural language preferences.
    Uses Groq LLM to re-evaluate, select the top matches, and provide personalized reasoning.
    """
    if not optional_preferences or not restaurants:
        print("[Groq] No preferences or restaurants provided, skipping LLM.")
        return restaurants[:5]
    
    try:
        print(f"[Groq] >>> Triggering Groq API request for {len(restaurants)} candidates...")
        print(f"[Groq]     User Vibe: '{optional_preferences[:100]}...'")
        
        client = get_groq_client()
        if not client:
            return restaurants[:5]
        
        # Prepare context for the prompt
        restaurant_context = json.dumps(restaurants, indent=2)
        
        system_prompt = (
            "You are an expert culinary AI assistant inside the Zomato Restaurant Recommendation System. "
            "Your job is to analyze a provided list of candidate restaurants and select the top 3 to 5 options "
            "that uniquely match the user's specific conversational 'optional preferences'.\n"
            "Return the output STRICTLY as a JSON array of objects. "
            "Each object must have the exact same keys as the provided candidates, PLUS a 'reasoning' key "
            "where you briefly explain why this restaurant perfectly matches their nuanced preferences (1-2 sentences max).\n"
            "Do NOT include markdown formatting (like ```json), just output the raw JSON array."
        )
        
        user_prompt = (
            f"User's Optional Preferences: '{optional_preferences}'\n\n"
            f"Candidate Restaurants:\n{restaurant_context}\n\n"
            "Please filter out the bad matches, re-rank the best ones, and add your 'reasoning'."
        )
        
        response = client.chat.completions.create(
            # Llama 3.1 is the current recommended fast model on Groq
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # Low temp for more deterministic JSON adherence
            max_tokens=2048
        )
        
        # Parse the JSON response securely
        content = response.choices[0].message.content.strip()
        print(f"[Groq] <<< Response received from API. Raw Content: {content[:500]}")
        
        # Robustly clean the JSON content
        clean_content = content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_content:
            clean_content = clean_content.split("```")[1].strip()
            
        ranked_restaurants = json.loads(clean_content)
        print(f"[Groq] Successfully parsed {len(ranked_restaurants)} recommendations.")
        return ranked_restaurants
        
    except Exception as e:
        print(f"[Groq] ERROR during LLM Processing or Parsing: {str(e)}")
        print(f"[Groq] Raw content preview: {content[:200] if 'content' in locals() else 'N/A'}")
        # In case of API failure, fallback gracefully to the original list
        return restaurants[:5]
