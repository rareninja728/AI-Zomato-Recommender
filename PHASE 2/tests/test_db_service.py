import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.db_service import get_metadata, filter_restaurants

@patch('src.services.db_service.sqlite3.connect')
def test_filter_restaurants(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Mocking rows directly
    mock_row1 = {'name': 'Spicy Bites', 'location': 'Delhi', 'rating': 4.2, 'cost': 500.0, 'cuisine': 'North Indian'}
    mock_cursor.fetchall.return_value = [mock_row1]
    
    result = filter_restaurants(location='Delhi', min_rating=4.0, cuisine='Indian', max_price=1000.0)
    
    assert len(result) == 1
    assert result[0]['name'] == 'Spicy Bites'
    # Verify the SQL query execution call params
    args, kwargs = mock_cursor.execute.call_args
    assert args[1] == ('%Delhi%', 4.0, 1000.0, '%Indian%')

@patch('src.services.db_service.sqlite3.connect')
def test_get_metadata(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # First fetchall call (Locations)
    mock_cursor.fetchall.side_effect = [
        [{'Location': 'Pune'}, {'Location': 'Mumbai'}],
        [{'Cuisines': 'Cafe, Italian'}, {'Cuisines': 'Fast Food'}]
    ]
    
    result = get_metadata()
    
    assert "locations" in result
    assert "cuisines" in result
    assert result["locations"] == ['Mumbai', 'Pune'] # Testing sort logic
    assert result["cuisines"] == ['Cafe, Italian', 'Fast Food']
