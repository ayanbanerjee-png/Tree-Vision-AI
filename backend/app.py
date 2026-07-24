import os
import shutil
import uuid
import time
from typing import List, Optional, Union
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import the orchestrator and config
from backend.predict import predict_tree
from backend.utils.config import DEVICE, MODEL_WEIGHTS, TEMP_DIR, UPLOADS_DIR
from backend.database import insert_prediction, get_all_predictions, get_review_queue, submit_prediction_review

# Define Debug Mode flag (uses wildcards for CORS if True)
DEBUG_MODE = os.getenv("TREEVISION_DEBUG", "True").lower() == "true"

app = FastAPI(
    title="TreeVision AI API Server",
    description="REST API backend for automated tree species identification and health diagnostics.",
    version="1.0"
)

# CORS middleware configurations
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if DEBUG_MODE:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not DEBUG_MODE,  # Must be False if using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ── Pydantic Schemas for OpenAPI/Swagger ───────────────────

class SpeciesPrediction(BaseModel):
    species: str = Field(..., description="Name of the candidate species")
    confidence: float = Field(..., description="Prediction confidence score in percent")

class OODCheckResponse(BaseModel):
    nearest_known_species: str = Field(..., description="Name of the nearest trained species")
    similarity: float = Field(..., description="Cosine similarity score")
    runner_up_species_gap: float = Field(..., description="Similarity gap to the runner-up species")
    is_recognized_species: bool = Field(..., description="Whether the species is recognized as in-distribution")

class PredictionResponse(BaseModel):
    species: str = Field(..., description="Top predicted exact species name (potentially gated/taxonomic fallback)")
    raw_species: str = Field(..., description="Raw species prediction before confidence gating")
    confidence: float = Field(..., description="Top predicted species confidence in percent")
    species_group: str = Field(..., description="Species group or family classification")
    health: str = Field(..., description="Predicted physiological health stress level")
    age: str = Field(..., description="Predicted age group category")
    foliage: str = Field(..., description="Predicted canopy foliage density level")
    image_quality: str = Field(..., description="Diagnosed image quality label ('clear', 'blurry', etc.)")
    occlusion: str = Field(..., description="Occlusion severity classification ('None', 'Partial', 'Heavy')")
    needs_review: bool = Field(..., description="Consolidated indicator for human auditor attention")
    top_predictions: List[SpeciesPrediction] = Field(..., description="List of top-5 predicted candidate species")
    processing_time_ms: int = Field(..., description="Total execution time of the inference pipeline")
    ood_check: Optional[OODCheckResponse] = None
    used_cropped_region: bool = Field(False, description="True if the final prediction came from a cropped sub-region rather than the full image")
    tree_detector_used: bool = Field(False, description="True if the target tree detector succeeded and cropped the region")
    tree_detector_status: str = Field("detector_unavailable", description="Status of the target tree detector check")
    multiple_trees_detected: bool = Field(False, description="True if multiple target tree candidates were detected")
    tree_candidate_count: int = Field(0, description="Total number of target tree candidates detected")
    cropped_image_url: Optional[str] = Field(None, description="URL path of the cropped region if used")

class SavedPredictionResponse(BaseModel):
    id: int
    request_id: str
    timestamp: str
    filename: Optional[str] = None
    species: str
    raw_species: str
    confidence: float
    species_group: str
    health: str
    age: str
    foliage: str
    image_quality: str
    occlusion: str
    needs_review: bool
    processing_time_ms: int
    used_cropped_region: bool
    tree_detector_used: bool
    tree_detector_status: str
    multiple_trees_detected: bool
    tree_candidate_count: int
    ood_similarity: Optional[float] = None
    ood_nearest_species: Optional[str] = None
    review_status: str
    # Human-review override fields (None = not yet reviewed or field not overridden)
    reviewed_species: Optional[str] = None
    reviewed_health: Optional[str] = None
    reviewed_age: Optional[str] = None
    reviewed_foliage: Optional[str] = None
    reviewed_at: Optional[str] = None
    cropped_image_url: Optional[str] = None

class BatchPredictionError(BaseModel):
    filename: str = Field(..., description="The name of the file that failed processing")
    error: str = Field(..., description="The error message details")
    status: str = Field("failed", description="The failure status")


class ReviewSubmitRequest(BaseModel):
    review_status: str = Field(
        ...,
        description="Auditor decision: must be 'approved' or 'rejected'"
    )
    species: Optional[str] = Field(None, description="Reviewer-corrected species label (leave null to keep ML output)")
    health: Optional[str] = Field(None, description="Reviewer-corrected health label")
    age: Optional[str] = Field(None, description="Reviewer-corrected age label")
    foliage: Optional[str] = Field(None, description="Reviewer-corrected foliage label")


class HealthResponse(BaseModel):
    status: str
    backend: str
    device: str
    models_loaded: bool
    species_model: str
    embedding_model: str
    auxiliary_models: List[str]
    occlusion_model: str
    version: str

class ModelInfoResponse(BaseModel):
    species_model: str
    embedding_model: str
    health_model: str
    foliage_model: str
    age_model: str
    occlusion_model: str
    device: str
    version: str

# ── API Endpoints ──────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
async def predict_single(image: UploadFile = File(..., description="Upload tree image (JPG, PNG, or WebP)")):
    """
    Accepts a single image upload, runs the full ML classification and diagnostic pipeline, and returns the result.
    """
    print(f"\n[INFO] [app.py] POST /predict - Received file: {image.filename}")
    
    # 1. Validate image format extension
    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        error_msg = f"Unsupported image format: '{ext}'. Use JPG, JPEG, PNG, or WebP."
        print(f"[ERROR] - {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
        
    # 2. Save temporary upload file
    temp_file_name = f"{uuid.uuid4()}{ext}"
    temp_file_path = os.path.join(TEMP_DIR, temp_file_name)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # 3. Call execution pipeline orchestrator
        result = predict_tree(temp_file_path)
        
        request_id = result.get("request_id")
        
        # 4. Save metadata to database (non-blocking)
        try:
            insert_prediction(request_id, image.filename, result)
        except Exception as db_err:
            print(f"[WARNING] Database write failed: {db_err}")
            
        return PredictionResponse(**result)
        
    except Exception as e:
        error_msg = f"Prediction failed: {str(e)}"
        print(f"[ERROR] - {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
        
    finally:
        # 5. Assured cleanup: Delete temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_err:
                print(f"[WARNING] Failed to remove temp file {temp_file_path}: {cleanup_err}")

@app.post("/predict-batch", response_model=List[Union[PredictionResponse, BatchPredictionError]], tags=["Inference"])
async def predict_batch(files: List[UploadFile] = File(..., description="Upload multiple tree images")):
    """
    Accepts multiple tree images and processes them sequentially using the predict pipeline.
    """
    batch_id = str(uuid.uuid4())[:8]
    print(f"\n[INFO] [app.py] POST /predict-batch - Received {len(files)} files - Batch ID: {batch_id}")
    
    results = []
    for file in files:
        # Validate format
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            error_msg = f"Unsupported format '{ext}'"
            print(f"[WARNING] Batch ID: {batch_id} - {file.filename}: {error_msg}")
            results.append(BatchPredictionError(filename=file.filename, error=error_msg, status="failed"))
            continue
            
        # Temp save
        temp_file_name = f"{uuid.uuid4()}{ext}"
        temp_file_path = os.path.join(TEMP_DIR, temp_file_name)
        
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Process single
            res = predict_tree(temp_file_path)
            
            # Read request_id from result and insert prediction
            file_request_id = res.get("request_id")
            try:
                insert_prediction(file_request_id, file.filename, res)
            except Exception as db_err:
                print(f"[WARNING] Batch db insert failed: {db_err}")
                
            results.append(PredictionResponse(**res))
        except Exception as e:
            print(f"[ERROR] Batch item prediction failed for {file.filename}: {e}")
            results.append(BatchPredictionError(filename=file.filename, error=str(e), status="failed"))
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    return results

@app.get("/health", response_model=HealthResponse, tags=["System Status"])
async def health_check():
    """
    Check backend health status and active GPU/CPU device metrics.
    """
    # Simple check: verify model directories contain weights
    models_loaded = all(os.path.exists(path) for path in MODEL_WEIGHTS.values())
    
    return HealthResponse(
        status="healthy",
        backend="online",
        device=str(DEVICE),
        models_loaded=models_loaded,
        species_model=os.path.basename(MODEL_WEIGHTS["species"]),
        embedding_model="DINOv2-Small (dinov2_vits14)",
        auxiliary_models=[
            os.path.basename(MODEL_WEIGHTS["health"]),
            os.path.basename(MODEL_WEIGHTS["foliage"]),
            os.path.basename(MODEL_WEIGHTS["age"])
        ],
        occlusion_model="YOLOv8-Nano (yolov8n.pt)",
        version="1.0"
    )

@app.get("/model-info", response_model=ModelInfoResponse, tags=["System Status"])
async def model_info():
    """
    Exposes architecture definitions and filename mappings of loaded models.
    """
    return ModelInfoResponse(
        species_model=os.path.basename(MODEL_WEIGHTS["species"]),
        embedding_model="DINOv2-Small (dinov2_vits14)",
        health_model=os.path.basename(MODEL_WEIGHTS["health"]),
        foliage_model=os.path.basename(MODEL_WEIGHTS["foliage"]),
        age_model=os.path.basename(MODEL_WEIGHTS["age"]),
        occlusion_model="YOLOv8-Nano (yolov8n.pt)",
        device=str(DEVICE),
        version="1.0"
    )

@app.get("/predictions", response_model=List[SavedPredictionResponse], tags=["Inference"])
async def list_predictions(limit: int = 100):
    """
    Retrieve historical tree prediction records from the database.
    """
    records = get_all_predictions(limit=limit)
    return [SavedPredictionResponse(**r) for r in records]

@app.get("/history", response_model=List[SavedPredictionResponse], tags=["Inference"])
async def get_history(limit: int = 100):
    """
    Retrieve historical tree prediction records from the database.
    """
    records = get_all_predictions(limit=limit)
    return [SavedPredictionResponse(**r) for r in records]


@app.get("/review-queue", response_model=List[SavedPredictionResponse], tags=["Human Review"])
async def get_review_queue_endpoint(limit: int = 100):
    """
    Returns all predictions where review_status = 'pending'.
    Intended for the Auditor Review UI to display items awaiting human judgment.
    """
    records = get_review_queue(limit=limit)
    return [SavedPredictionResponse(**r) for r in records]


@app.patch("/predictions/{prediction_id}/review", tags=["Human Review"])
async def submit_review(prediction_id: int, body: ReviewSubmitRequest):
    """
    Accepts a human auditor review decision for a single prediction.

    - review_status must be 'approved' or 'rejected'.
    - Optional override fields (species, health, age, foliage) are stored in separate
      reviewed_* columns — the original ML prediction columns are NEVER modified.
    - A review failure returns a 422/500 error to the frontend; it does not crash silently.
    """
    try:
        overrides = {
            "species": body.species,
            "health":  body.health,
            "age":     body.age,
            "foliage": body.foliage,
        }
        submit_prediction_review(
            prediction_id=prediction_id,
            review_status=body.review_status,
            overrides=overrides,
        )
        return {
            "ok": True,
            "id": prediction_id,
            "review_status": body.review_status,
            "message": f"Review recorded for prediction id={prediction_id}."
        }
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=404, detail=str(re))
    except Exception as e:
        print(f"[ERROR] Review write failed for id={prediction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Review write failed: {str(e)}")
