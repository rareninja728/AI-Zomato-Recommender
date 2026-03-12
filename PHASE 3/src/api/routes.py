from fastapi import APIRouter, HTTPException
from typing import Dict, List
from src.models.schemas import RecommendationRequest, RecommendationResponse, Restaurant
from src.services.db_service import get_metadata, filter_restaurants
from src.services.llm_service import process_with_llm

router = APIRouter()

@router.get("/api/metadata", response_model=Dict[str, List[str]])
async def get_filter_options():
    """Returns valid locations and cuisines to populate the frontend UI dropdowns."""
    options = get_metadata()
    if not options or (not options["locations"] and not options["cuisines"]):
        raise HTTPException(status_code=500, detail="Could not load metadata from the database.")
    return options

@router.post("/api/recommend", response_model=RecommendationResponse)
async def process_recommendation(request: RecommendationRequest):
    """
    Receives user preferences, performs rule-based filtering, and
    hands off to the Groq LLM layer for contextual re-ranking and reasoning extraction.
    """
    try:
        # Step 1: Base Recommendation Engine Strict Filtering
        db_filtered_results = filter_restaurants(
            location=request.location,
            min_rating=request.min_rating,
            cuisine=request.cuisine,
            max_price=request.max_price
        )
        
        if not db_filtered_results:
             return RecommendationResponse(restaurants=[], message="No restaurants found matching those strict criteria.")
        
        # Step 2: Groq LLM Contextual Filtering
        if request.optional_preferences:
            final_results = process_with_llm(db_filtered_results, request.optional_preferences)
            message = "Successfully filtered and AI-ranked restaurants."
        else:
            # If no optional preferences, just return top 5 from DB
            final_results = db_filtered_results[:5]
            message = "Successfully filtered restaurants using base engine."
            
        # Format for output
        restaurants = [Restaurant(**item) for item in final_results]
        
        return RecommendationResponse(restaurants=restaurants, message=message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
