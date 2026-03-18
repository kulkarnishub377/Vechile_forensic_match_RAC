import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import config

@pytest.fixture
def test_image_path():
    """Return path to a test image if it exists, else None"""
    # Try to find a real image in the repo for testing
    possible_paths = [
        "Refrence_ code/frontend/uploads/example_vehicle.jpg",
        "Refrence_ code/frontend/uploads/test.jpg",
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            return p
    
    return None

@pytest.fixture
def mock_embedding_engine():
    """Mock embedding engine for unit tests"""
    from unittest.mock import MagicMock
    engine = MagicMock()
    engine.extract_embedding.return_value = [0.1] * config.TOTAL_EMBEDDING_DIM
    return engine
