from pydantic import BaseModel, Field
from typing import List, Optional

class RecommendationRequest(BaseModel):
    location: str = Field(..., description="The city or precise location to search in.")
    min_rating: float = Field(..., description="The minimum acceptable rating, typically 0.0 to 5.0.")
    cuisine: str = Field(..., description="The type of cuisine desired.")
    max_price: float = Field(..., description="The maximum acceptable cost/price for the meal.")
    optional_preferences: Optional[str] = Field(None, description="Natural language string for nuances like 'good for a romantic date', passed to LLM later.")

class Restaurant(BaseModel):
    name: str = Field(..., description="Name of the restaurant")
    location: str = Field(..., description="Address/Location of the restaurant")
    rating: float = Field(..., description="Current rating")
    cost: float = Field(..., description="Approximate cost")
    cuisine: str = Field(..., description="Cuisines offered")
    reasoning: Optional[str] = Field(None, description="Groq LLM generated reasoning on why this fits the optional preferences.") # Added for Phase 3

class RecommendationResponse(BaseModel):
    restaurants: List[Restaurant]
    message: str = Field(..., description="System status or context message")
