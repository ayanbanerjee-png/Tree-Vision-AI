from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "device" in data
    assert "models_loaded" in data
    print("✓ Health Check Endpoint test passed!")

def test_model_info():
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "species_model" in data
    assert "embedding_model" in data
    assert "device" in data
    assert data["version"] == "1.0"
    print("✓ Model Info Endpoint test passed!")

if __name__ == "__main__":
    print("Executing FastAPI Backend Integration Tests...")
    print("===============================================")
    try:
        test_health()
        test_model_info()
        print("===============================================")
        print("All API Endpoint integration checks PASSED successfully!")
    except Exception as e:
        print("===============================================")
        print(f"❌ Test verification FAILED: {e}")
        exit(1)
