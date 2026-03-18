import pytest
import numpy as np
from app import config
from app.embedding import VehicleEmbeddingEngine

def test_initialization():
    """Test that engine initializes correctly"""
    engine = VehicleEmbeddingEngine()
    assert engine.device is not None
    assert engine.preprocess is not None

def test_embedding_dimensions(test_image_path):
    """Test that embedding has correct dimensions"""
    if not test_image_path:
        pytest.skip("No test image found")
        
    engine = VehicleEmbeddingEngine()
    embedding = engine.extract_embedding(test_image_path)
    
    assert embedding is not None
    assert len(embedding) == config.TOTAL_EMBEDDING_DIM
    assert isinstance(embedding, np.ndarray)

def test_embedding_normalization(test_image_path):
    """Test that embedding is normalized"""
    if not test_image_path:
        pytest.skip("No test image found")
        
    engine = VehicleEmbeddingEngine()
    embedding = engine.extract_embedding(test_image_path)
    
    # Check L2 norm is approximately 1.0
    norm = np.linalg.norm(embedding)
    assert np.isclose(norm, 1.0, atol=1e-5)
