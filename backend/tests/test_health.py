from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check_ep01():
    """Test EP-01 Health Check endpoint contract"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "JobMatch" in response.json()["message"]
