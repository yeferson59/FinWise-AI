from fastapi.testclient import TestClient
from app.main import application

client = TestClient(application)


def test_app_creation():
    """Test that the app is created successfully"""
    assert client is not None
    assert client.app is not None


def test_read_main():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_api_prefix():
    """Test that API endpoints are prefixed correctly"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    response = client.get("/health")
    assert response.status_code == 404
