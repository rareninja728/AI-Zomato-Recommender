from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from src.models.schemas import RecommendationRequest, RecommendationResponse, Restaurant
from src.services.db_service import get_metadata, filter_restaurants

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
    (in Phase 3) will hand off to the LLM layer. 
    Currently returns the deterministic filtered results.
    """
    try:
        # Step 1: Base Recommendation Engine
        filtered_results = filter_restaurants(
            location=request.location,
            min_rating=request.min_rating,
            cuisine=request.cuisine,
            max_price=request.max_price
        )
        
        # Format for output
        restaurants = [Restaurant(**item) for item in filtered_results]
        
        message = "Successfully filtered restaurants."
        if not restaurants:
            message = "No restaurants found matching those strict criteria."
            
        return RecommendationResponse(restaurants=restaurants, message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
