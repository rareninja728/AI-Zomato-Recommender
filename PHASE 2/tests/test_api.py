from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import sys

# Add parent directory to path to enable importing src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import app

client = TestClient(app)

@patch("src.api.routes.get_metadata")
def test_get_metadata_success(mock_get_metadata):
    mock_get_metadata.return_value = {
        "locations": ["Bangalore", "Delhi"],
        "cuisines": ["Italian", "North Indian"]
    }
    response = client.get("/api/metadata")
    assert response.status_code == 200
    assert response.json() == {
        "locations": ["Bangalore", "Delhi"],
        "cuisines": ["Italian", "North Indian"]
    }

@patch("src.api.routes.get_metadata")
def test_get_metadata_failure(mock_get_metadata):
    mock_get_metadata.return_value = {}  # Simulate DB failure
    response = client.get("/api/metadata")
    assert response.status_code == 500
    assert "detail" in response.json()

@patch("src.api.routes.filter_restaurants")
def test_process_recommendation_success(mock_filter):
    # Mocking the deterministic filter logic from Phase 2
    mock_filter.return_value = [
        {
            "name": "Italiano Pizza",
            "location": "Bangalore",
            "rating": 4.5,
            "cost": 800.0,
            "cuisine": "Italian"
        }
    ]
    
    payload = {
        "location": "Bangalore",
        "min_rating": 4.0,
        "cuisine": "Italian",
        "max_price": 1000.0,
        "optional_preferences": "A quiet place for anniversary"
    }
    
    response = client.post("/api/recommend", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "restaurants" in data
    assert len(data["restaurants"]) == 1
    assert data["restaurants"][0]["name"] == "Italiano Pizza"
    assert data["message"] == "Successfully filtered restaurants."

def test_process_recommendation_validation_error():
    # Missing required field 'cuisine'
    payload = {
        "location": "Delhi",
        "min_rating": 4.0,
        "max_price": 500.0
    }
    
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 422 # FastAPI validation Error
