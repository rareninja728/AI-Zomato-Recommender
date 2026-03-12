from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import logging
from src.models.schemas import RecommendationRequest, RecommendationResponse, Restaurant
from src.services.db_service import get_metadata, filter_restaurants
from src.services.llm_service import process_with_llm
from src.services.analytics_service import log_query

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/metadata", response_model=Dict[str, List[str]])
async def get_filter_options():
    options = get_metadata()
    return options

@router.post("/api/recommend", response_model=RecommendationResponse)
async def process_recommendation(request: RecommendationRequest, background_tasks: BackgroundTasks):
    try:
        # Step 1: Base Recommendation Engine with Fallback Strategy
        db_filtered_results = filter_restaurants(
            location=request.location,
            min_rating=request.min_rating,
            cuisine=request.cuisine,
            max_price=request.max_price
        )
        
        if not db_filtered_results:
             # This should never happen with our fallback strategy, but just in case
             return RecommendationResponse(restaurants=[], message="No restaurants found in database.")
        
        # Step 2: Always call LLM to generate explanations for each restaurant
        final_results, cache_hit = process_with_llm(db_filtered_results, request.optional_preferences or "")
        
        # Step 3: Ensure we have at least 3 results
        if len(final_results) < 3:
            logger.warning(f"Only {len(final_results)} results returned, expected minimum 3")
            # The fallback logic in db_service should prevent this, but add extra safety
            
        if request.optional_preferences:
            message = f"Successfully filtered and AI-ranked {len(final_results)} restaurants."
        else:
            message = f"Successfully filtered {len(final_results)} restaurants with AI-generated explanations."
            
        # Step 4: Analytics and Tracking Logging in Background (Non-blocking)
        background_tasks.add_task(
            log_query, 
            request.location, 
            request.cuisine, 
            request.optional_preferences, 
            cache_hit, 
            len(final_results)
        )
            
        restaurants = [Restaurant(**item) for item in final_results]
        return RecommendationResponse(restaurants=restaurants, message=message)
        
    except Exception as e:
        logger.error(f"Error in process_recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
