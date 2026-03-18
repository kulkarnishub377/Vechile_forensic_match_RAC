import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200

def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database_ok" in data

def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    # Prometheus metrics return plain text
    assert response.status_code == 200

def test_search_validation():
    """Test search endpoint validation"""
    # Missing transaction_id
    response = client.post("/search?include_details=true", json={
        "k": 10
    })
    # Should fail validation
    assert response.status_code == 422 
