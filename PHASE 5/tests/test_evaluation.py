import pytest
import time
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm_service import process_with_llm, LLM_CACHE, generate_cache_key

@pytest.fixture
def test_restaurants():
    return [
        {"name": "Fast Cafe", "location": "City", "rating": 4.0, "cost": 300, "cuisine": "Cafe"},
        {"name": "Slow Diner", "location": "City", "rating": 3.9, "cost": 400, "cuisine": "Diner"}
    ]

@patch('src.services.llm_service.Groq')
def test_caching_speed_and_hit(mock_groq, test_restaurants):
    # Setup mock Groq to take artificial time
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    def slow_mock(*args, **kwargs):
        time.sleep(0.5) # Simulate API latency
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = '''[{"name": "Fast Cafe", "reasoning": "Fits query"}]'''
        return mock_resp
        
    mock_client.chat.completions.create.side_effect = slow_mock
    
    query = "Quick bite"
    
    # First call: Should be a MISS (meaning it hits the slow API)
    start_time_1 = time.time()
    result1, hit1 = process_with_llm(test_restaurants, query)
    duration_1 = time.time() - start_time_1
    
    assert hit1 is False
    assert duration_1 >= 0.5 # API latency occurred
    
    # Check cache state
    cache_key = generate_cache_key(test_restaurants, query)
    assert cache_key in LLM_CACHE
    
    # Second call: Should be a HIT (meaning it skips API entirely)
    start_time_2 = time.time()
    result2, hit2 = process_with_llm(test_restaurants, query)
    duration_2 = time.time() - start_time_2
    
    assert hit2 is True
    assert duration_2 < 0.05 # Near instant
    assert result1 == result2 # Results are identical

def test_evaluation_hallucination_check(test_restaurants):
    # Simulates an Evaluation test to ensure the LLM didn't hallucinate a restaurant not in the DB
    llm_output = [
        {"name": "Fast Cafe", "reasoning": "Fits"},
        {"name": "Fake Magic Restaurant", "reasoning": "Hallucinated name"} # The LLM hallucinated this
    ]
    
    valid_names = {r['name'] for r in test_restaurants}
    hallucinations = [r for r in llm_output if r['name'] not in valid_names]
    
    # In a real eval testing suite, we fail the threshold if hallucination > 0%.
    assert len(hallucinations) == 1
    assert hallucinations[0]['name'] == "Fake Magic Restaurant"
