import os
import joblib
import numpy as np
from backend.utils.config import MODEL_WEIGHTS

# Global model state loaded once
_rf_health = None
_svm_foliage = None
_knn_age = None

def load_auxiliary_models():
    """
    Load Random Forest, SVM, and KNN classifiers using joblib.
    """
    global _rf_health, _svm_foliage, _knn_age
    print("Loading auxiliary classifier models...")
    
    health_path = MODEL_WEIGHTS["health"]
    foliage_path = MODEL_WEIGHTS["foliage"]
    age_path = MODEL_WEIGHTS["age"]
    
    if not os.path.exists(health_path):
        raise FileNotFoundError(f"Missing health classifier at {health_path}")
    if not os.path.exists(foliage_path):
        raise FileNotFoundError(f"Missing foliage classifier at {foliage_path}")
    if not os.path.exists(age_path):
        raise FileNotFoundError(f"Missing age classifier at {age_path}")
        
    try:
        _rf_health = joblib.load(health_path)
        _svm_foliage = joblib.load(foliage_path)
        _knn_age = joblib.load(age_path)
        print("Auxiliary classifiers loaded successfully!")
    except Exception as e:
        print(f"Error loading auxiliary model files: {e}")
        raise e

# Initialize models on import
load_auxiliary_models()

def predict_auxiliary_attributes(embedding: np.ndarray) -> dict:
    """
    Predict health status, foliage density, and age category using the 384-dimensional DINOv2 embedding.
    Preserves exact classification behavior of Notebook 05.
    """
    global _rf_health, _svm_foliage, _knn_age
    
    try:
        # Reshape input embedding to a 2D array [1, 384] to match scikit-learn expected format
        x = embedding.reshape(1, -1)
        
        # Perform inference using loaded scikit-learn models
        health_pred = _rf_health.predict(x)[0]
        foliage_pred = _svm_foliage.predict(x)[0]
        age_pred = _knn_age.predict(x)[0]
        
        return {
            "health": str(health_pred),
            "foliage": str(foliage_pred),
            "age": str(age_pred)
        }
    except Exception as e:
        print(f"Error in auxiliary prediction pipeline: {e}")
        return {
            "health": "Uncertain",
            "foliage": "Uncertain",
            "age": "Uncertain"
        }
