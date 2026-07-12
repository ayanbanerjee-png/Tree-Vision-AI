import os
import time
import uuid
import numpy as np

# Import the inference functions from the individual models (no duplicated logic)
from backend.models.quality import analyze_image_quality
from backend.models.species import predict_species
from backend.models.embedding import extract_dinov2_embeddings
from backend.models.auxiliary import predict_auxiliary_attributes
from backend.models.occlusion import detect_occlusion
from backend.models.ood import check_species_ood
from backend.models.multiscale import generate_crop_candidates, cleanup_crops, generate_smart_crop

# Secure-by-default: inactive unless explicitly set to "true"
DEBUG_MODE = os.getenv("TREEVISION_DEBUG", "False").lower() == "true"

def predict_tree(image_path: str, input_type: str = "single_tree") -> dict:
    """
    Orchestration layer that executes the end-to-end inference pipeline exactly
    as defined in Notebook 06, updated with Notebook 08 occlusion detection.
    
    Measures processing time, generates a unique request ID, and prints
    detailed progress execution logs to the backend console.
    """
    # ── Secure-by-Default Testing Hooks ──
    if DEBUG_MODE:
        fn_lower = os.path.basename(image_path).lower()
        if "test-high" in fn_lower:
            return {
                "species": "Neem (Azadirachta indica)",
                "raw_species": "Neem (Azadirachta indica)",
                "confidence": 95.0,
                "species_group": "Meliaceae",
                "health": "Healthy",
                "age": "Mature",
                "foliage": "Full Canopy",
                "image_quality": "clear",
                "occlusion": "None",
                "needs_review": False,
                "top_predictions": [
                    {"species": "Neem (Azadirachta indica)", "confidence": 95.0},
                    {"species": "Teak (Tectona grandis)", "confidence": 3.0}
                ],
                "processing_time_ms": 10,
                "ood_check": {
                    "nearest_known_species": "Neem (Azadirachta indica)",
                    "similarity": 0.95,
                    "runner_up_species_gap": 0.92,
                    "is_recognized_species": True
                },
                "used_cropped_region": False
            }
        elif "test-medium" in fn_lower:
            return {
                "species": "Ficus — uncertain species",
                "raw_species": "Peepal (Ficus religiosa)",
                "confidence": 55.0,
                "species_group": "Ficus",
                "health": "Healthy",
                "age": "Mature",
                "foliage": "Full Canopy",
                "image_quality": "clear",
                "occlusion": "None",
                "needs_review": True,
                "top_predictions": [
                    {"species": "Peepal (Ficus religiosa)", "confidence": 55.0},
                    {"species": "Banyan (Ficus benghalensis)", "confidence": 20.0}
                ],
                "processing_time_ms": 10,
                "ood_check": {
                    "nearest_known_species": "Peepal (Ficus religiosa)",
                    "similarity": 0.58,
                    "runner_up_species_gap": 0.38,
                    "is_recognized_species": True
                },
                "used_cropped_region": False
            }
        elif "test-low" in fn_lower:
            return {
                "species": "Unknown — flagged for review",
                "raw_species": "Moringa_oleifera",
                "confidence": 32.89,
                "species_group": "Unknown",
                "health": "Healthy",
                "age": "Young (2-10yr)",
                "foliage": "Full Canopy",
                "image_quality": "clear",
                "occlusion": "None",
                "needs_review": True,
                "top_predictions": [
                    {"species": "Moringa_oleifera", "confidence": 32.89},
                    {"species": "Pinus_roxburghii", "confidence": 15.0}
                ],
                "processing_time_ms": 10,
                "ood_check": {
                    "nearest_known_species": "Moringa_oleifera",
                    "similarity": 0.32,
                    "runner_up_species_gap": 0.02,
                    "is_recognized_species": False
                },
                "used_cropped_region": False
            }

    # 1. Generate unique request ID and initialize timers
    request_id = str(uuid.uuid4())[:8]
    start_total = time.perf_counter()
    
    print(f"\n[INFO] Request ID: {request_id}")
    print("[INFO] Image received")
    
    # ── Step 1: Image Quality Assessment ──
    start_step = time.perf_counter()
    quality_result = analyze_image_quality(image_path, input_type)
    quality_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] Image Quality Assessment completed ({quality_time:.0f} ms)")
    
    # ── Step 2: DINOv2 Embedding Extraction ──
    start_step = time.perf_counter()
    embedding = extract_dinov2_embeddings(image_path)
    embedding_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] DINOv2 Embedding Extraction completed ({embedding_time:.0f} ms)")

    # ── Step 3: Out-of-Distribution (OOD) Species Detection ──
    start_step = time.perf_counter()
    ood_result = check_species_ood(embedding)
    ood_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] OOD Species Detection completed ({ood_time:.0f} ms)")
    
    # ── Step 4: Species Classification (Gated by OOD check) ──
    start_step = time.perf_counter()
    if ood_result['is_recognized_species']:
        species_result = predict_species(image_path)
    else:
        species_result = {
            'species': 'Unrecognized',
            'species_group': 'unknown',
            'confidence': round(ood_result['similarity'] * 100, 2),
            'confidence_level': 'low',
            'display_label': f"Unrecognized — not one of the trained species (closest match: {ood_result['nearest_known_species']}, {ood_result['similarity']:.2f} similarity)",
            'top_predictions': [],
        }
    species_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] Species Classification completed ({species_time:.0f} ms)")
    
    # ── Step 5: Occlusion Detection (YOLOv8) ──
    # Run YOLOv8 occlusion detection early to reuse bounding box coords for smart fallback crop
    start_step = time.perf_counter()
    occlusion_result = detect_occlusion(image_path)
    occlusion_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] Occlusion Detection completed ({occlusion_time:.0f} ms)")

    # ── Multi-Scale Crop Fallback (with YOLO-Guided Smart Crop) ──
    used_cropped_region = False
    
    # Define strict OOD thresholds for Path 2
    STRICT_SIMILARITY_THRESHOLD = 0.65
    STRICT_MARGIN_THRESHOLD = 0.15
    
    # Trigger condition: full-frame is OOD or confidence level is not high
    if (not ood_result['is_recognized_species']) or (species_result['confidence_level'] != 'high'):
        start_fallback = time.perf_counter()
        crops_evaluated_count = 0
        tmp_dir = None
        
        # Save original full-frame values to restore if fallback fails or no path is satisfied
        original_species_result = species_result
        original_ood_result = ood_result
        original_embedding = embedding
        
        try:
            print("[INFO] Gating failed (OOD or Low Confidence). Generating crop candidates...")
            
            # Obtain YOLO boxes from occlusion result
            yolo_boxes = occlusion_result.get("yolo_boxes", [])
            
            # Generate smart crop first
            smart_crop_paths = generate_smart_crop(image_path, request_id, yolo_boxes)
            
            # Generate blind crop candidates
            blind_crop_paths, tmp_dir = generate_crop_candidates(image_path, request_id)
            
            # Combine candidates list.
            # Smart crop candidate path (if any) is evaluated first.
            candidates = []
            if smart_crop_paths:
                candidates.append((smart_crop_paths[0], "smart"))
            for path in blind_crop_paths[1:]:
                candidates.append((path, "blind_scale"))
            
            # List to track qualifying candidates (is_recognized and confidence_level == 'high')
            qualifying_candidates = []
            
            # Loop through crop candidates
            for crop_path, crop_type in candidates:
                # Check time budget: hard cap of 3.0 seconds elapsed
                elapsed_fallback = time.perf_counter() - start_fallback
                if elapsed_fallback >= 3.0:
                    print(f"[WARNING] Fallback time budget exceeded ({elapsed_fallback:.2f}s). Stopping search.")
                    break
                
                crops_evaluated_count += 1
                try:
                    # a. Extract embedding
                    crop_emb = extract_dinov2_embeddings(crop_path)
                    
                    # b. Run OOD check
                    crop_ood = check_species_ood(crop_emb)
                    
                    # c. Run species classifier ONLY if OOD check passes
                    if crop_ood['is_recognized_species']:
                        crop_species = predict_species(crop_path)
                    else:
                        crop_species = {
                            'species': 'Unrecognized',
                            'species_group': 'unknown',
                            'confidence': round(crop_ood['similarity'] * 100, 2),
                            'confidence_level': 'low',
                            'display_label': f"Unrecognized — not one of the trained species (closest match: {crop_ood['nearest_known_species']}, {crop_ood['similarity']:.2f} similarity)",
                            'top_predictions': [],
                        }
                    
                    cand_info = {
                        "is_recognized": crop_ood["is_recognized_species"],
                        "confidence": crop_species["confidence"],
                        "similarity": crop_ood["similarity"],
                        "species_result": crop_species,
                        "ood_result": crop_ood,
                        "embedding": crop_emb,
                        "path": crop_path,
                        "crop_type": crop_type
                    }
                    
                    # Check if this crop is a qualifying candidate (recognized + high confidence)
                    is_qualifying = cand_info["is_recognized"] and cand_info["species_result"]["confidence_level"] == 'high'
                    
                    if is_qualifying:
                        predicted_species = cand_info["species_result"]["species"]
                        
                        # PATH 3 — Full-frame corroboration:
                        full_frame_top_species = [p['species'] for p in original_species_result.get('top_predictions', [])]
                        path3_satisfied = predicted_species in full_frame_top_species
                        
                        # PATH 2 — Strict single-crop override:
                        path2_satisfied = (
                            cand_info["similarity"] >= STRICT_SIMILARITY_THRESHOLD and 
                            crop_ood["runner_up_species_gap"] >= STRICT_MARGIN_THRESHOLD
                        )
                        
                        # PATH 1 — Agreement between two crops:
                        path1_satisfied = False
                        for prev_cand in qualifying_candidates:
                            if prev_cand["species_result"]["species"] == predicted_species:
                                path1_satisfied = True
                                break
                        
                        # Add to qualifying candidates list for future Path 1 checks
                        qualifying_candidates.append(cand_info)
                        
                        # Check if any path is satisfied
                        satisfied_path = None
                        if path3_satisfied:
                            satisfied_path = "Path 3 (full-frame corroboration)"
                        elif path2_satisfied:
                            satisfied_path = "Path 2 (strict single-crop override)"
                        elif path1_satisfied:
                            satisfied_path = "Path 1 (agreement between two crops)"
                            
                        if satisfied_path:
                            print(f"[INFO] Accepted via {satisfied_path}: species={predicted_species}, crop_type={crop_type}")
                            species_result = cand_info["species_result"]
                            ood_result = cand_info["ood_result"]
                            embedding = cand_info["embedding"]
                            used_cropped_region = True
                            break
                            
                except Exception as crop_err:
                    print(f"[WARNING] Error evaluating crop candidate '{crop_path}': {crop_err}")
            
            # If no path was satisfied, restore full-frame results
            if not used_cropped_region:
                species_result = original_species_result
                ood_result = original_ood_result
                embedding = original_embedding
                used_cropped_region = False
                
        except Exception as e:
            print(f"[WARNING] Multi-scale fallback encountered an error: {e}. Reverting to full-frame results.")
            species_result = original_species_result
            ood_result = original_ood_result
            embedding = original_embedding
            used_cropped_region = False
        finally:
            if tmp_dir:
                cleanup_crops(tmp_dir)
            elapsed = (time.perf_counter() - start_fallback) * 1000
            print(f"[INFO] Multi-scale fallback completed ({elapsed:.0f} ms, {crops_evaluated_count} crops evaluated)")

    # ── Step 6: Auxiliary Predictions (Health, Age, Foliage) ──
    start_step = time.perf_counter()
    aux_result = predict_auxiliary_attributes(embedding)
    aux_time = (time.perf_counter() - start_step) * 1000
    print(f"[INFO] Auxiliary Prediction completed ({aux_time:.0f} ms)")
    
    # ── Step 7: Confidence Gating & Review Logic ──
    start_step = time.perf_counter()
    
    # Check individual gating conditions matching Notebook 06 & 08
    quality_needs_review = quality_result['image_quality'] not in ('clear', 'partial_view')
    
    # Both audit flags and display labels read from the same confidence tiering logic in species.py
    species_needs_review = species_result['confidence_level'] != 'high'
    occlusion_needs_review = occlusion_result['needs_review']
    
    # Calculate auxiliary low-confidence flags if probability checks are supported by models
    # (FastAPI endpoints will pass this back as a unified true/false)
    aux_needs_review = False # Will default to false if models are confident
    
    # Final consolidated review flag
    needs_review = (
        quality_needs_review
        or species_needs_review
        or occlusion_needs_review
        or aux_needs_review
        or not ood_result['is_recognized_species']
    )
    
    print("[INFO] Confidence Gating completed")
    
    total_time_ms = (time.perf_counter() - start_total) * 1000
    print(f"[INFO] Total inference time ({total_time_ms:.0f} ms)")
    
    # 8. Construct and return final unified JSON response object
    # We map display_label as the primary gated prediction, and species as raw_species
    return {
        "species": species_result["display_label"],
        "raw_species": species_result["species"],
        "confidence": species_result["confidence"],
        "species_group": species_result["species_group"],
        "health": aux_result["health"],
        "age": aux_result["age"],
        "foliage": aux_result["foliage"],
        "image_quality": quality_result["image_quality"],
        "occlusion": occlusion_result["occlusion"],
        "needs_review": needs_review,
        "top_predictions": species_result["top_predictions"],
        "processing_time_ms": int(round(total_time_ms)),
        "ood_check": ood_result,
        "used_cropped_region": used_cropped_region
    }
