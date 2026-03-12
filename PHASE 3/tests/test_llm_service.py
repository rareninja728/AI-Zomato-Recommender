import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm_service import process_with_llm

@pytest.fixture
def sample_db_restaurants():
    return [
        {
            "name": "Romantic Luigi's",
            "location": "Downtown",
            "rating": 4.8,
            "cost": 1500.0,
            "cuisine": "Italian"
        },
        {
            "name": "Loud Joe's Diner",
            "location": "Uptown",
            "rating": 4.1,
            "cost": 500.0,
            "cuisine": "American"
        },
        {
            "name": "Quiet Tea House",
            "location": "Downtown",
            "rating": 4.5,
            "cost": 800.0,
            "cuisine": "Cafe"
        }
    ]

@patch('src.services.llm_service.Groq')
def test_process_with_llm_success(mock_groq, sample_db_restaurants):
    # Setup the mock Groq client and its chained response
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    # Mock the LLM returning a JSON string wrapped in markdown block
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '''```json
[
  {
    "name": "Romantic Luigi's",
    "location": "Downtown",
    "rating": 4.8,
    "cost": 1500.0,
    "cuisine": "Italian",
    "reasoning": "With its high rating and traditional Italian menu, it provides the perfect quiet and romantic ambiance you requested."
  },
  {
    "name": "Quiet Tea House",
    "location": "Downtown",
    "rating": 4.5,
    "cost": 800.0,
    "cuisine": "Cafe",
    "reasoning": "A highly rated cafe that fits your preference for a quiet, intimate setting for a date."
  }
]
```'''
    mock_client.chat.completions.create.return_value = mock_response

    # Execute
    optional_preferences = "A quiet romantic place for a date"
    result = process_with_llm(sample_db_restaurants, optional_preferences)

    # Assertions
    assert len(result) == 2
    assert result[0]["name"] == "Romantic Luigi's"
    assert "reasoning" in result[0]
    assert result[0]["reasoning"] == "With its high rating and traditional Italian menu, it provides the perfect quiet and romantic ambiance you requested."
    
    # Verify the LLM was called with the correct model and settings
    mock_client.chat.completions.create.assert_called_once()
    args, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs['model'] == "llama3-8b-8192"
    assert kwargs['temperature'] == 0.2

@patch('src.services.llm_service.Groq')
def test_process_with_llm_fallback_on_error(mock_groq, sample_db_restaurants):
    # Simulate an API error (e.g. Rate limit or invalid key)
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Groq API Rate Limited")
    
    optional_preferences = "Find me good food"
    result = process_with_llm(sample_db_restaurants, optional_preferences)
    
    # It should fallback gracefully to the original list
    assert len(result) == 3
    assert result[0]["name"] == "Romantic Luigi's"
    # Fallback won't have the LLM reasoning field
    assert "reasoning" not in result[0]

def test_process_with_llm_empty_input(sample_db_restaurants):
    # If no optional preferences are provided, it should immediately return the DB results
    result = process_with_llm(sample_db_restaurants, "")
    
    assert len(result) == 3
    assert result == sample_db_restaurants
