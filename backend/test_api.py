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
def test_predict():
    img_path = r"C:\Users\AYAN\Flocard Tree AI\data\own\single_tree\broadleaf\Pongamia_pinnata\98.jpg"
    with open(img_path, "rb") as f:
        response = client.post("/predict", files={"image": ("98.jpg", f, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    
    # Assert presence of all fields
    required_fields = [
        "species", "raw_species", "confidence", "species_group", "health", "age", "foliage",
        "image_quality", "occlusion", "needs_review", "top_predictions", "processing_time_ms",
        "ood_check", "used_cropped_region", "tree_detector_used", "tree_detector_status",
        "multiple_trees_detected", "tree_candidate_count"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
        
    # Assert types of new fields
    assert isinstance(data["tree_detector_used"], bool)
    assert isinstance(data["tree_detector_status"], str)
    assert isinstance(data["multiple_trees_detected"], bool)
    assert isinstance(data["tree_candidate_count"], int)
    
    # Confirm it matches tree_detector_used=True for Pongamia_pinnata/98.jpg
    assert data["tree_detector_used"] is True
    assert data["tree_detector_status"] == "auto_selected"
    
    print("✓ Predict Endpoint test passed!")
    import pprint
    print("\nAPI Response JSON:")
    pprint.pprint(data)

if __name__ == "__main__":
    print("Executing FastAPI Backend Integration Tests...")
    print("===============================================")
    try:
        test_health()
        test_model_info()
        test_predict()
        print("===============================================")
        print("All API Endpoint integration checks PASSED successfully!")
    except Exception as e:
        print("===============================================")
        print(f"❌ Test verification FAILED: {e}")
        exit(1)
