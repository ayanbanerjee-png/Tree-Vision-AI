import sqlite3
import os
from datetime import datetime
from backend.utils.config import DB_PATH

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Enable row factory to easily convert queries into dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Create the predictions table if it doesn't already exist.
    """
    print(f"[INFO] Initializing SQLite database at: {DB_PATH}")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                timestamp TEXT,
                filename TEXT,
                species TEXT,
                raw_species TEXT,
                confidence REAL,
                species_group TEXT,
                health TEXT,
                age TEXT,
                foliage TEXT,
                image_quality TEXT,
                occlusion TEXT,
                needs_review INTEGER,
                processing_time_ms INTEGER,
                used_cropped_region INTEGER,
                tree_detector_used INTEGER,
                tree_detector_status TEXT,
                multiple_trees_detected INTEGER,
                tree_candidate_count INTEGER,
                ood_similarity REAL,
                ood_nearest_species TEXT,
                review_status TEXT DEFAULT 'pending'
            );
        """)
        conn.commit()
        print("[INFO] SQLite predictions table initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize predictions table: {e}")
    finally:
        conn.close()

# Auto-initialize on module load to ensure DB is ready immediately
init_db()

def insert_prediction(request_id: str, filename: str, response_dict: dict) -> None:
    """
    Inserts a prediction metadata record into the SQLite database.
    Catches and logs all exceptions to ensure DB failures never crash the ML pipeline response.
    """
    try:
        # Safely resolve OOD check details if nested dict exists
        ood_check = response_dict.get("ood_check") or {}
        ood_similarity = ood_check.get("similarity")
        ood_nearest_species = ood_check.get("nearest_known_species")
        
        # Convert boolean flags to integers 0/1 for SQLite compatibility
        def to_bool_int(val):
            if val is None:
                return 0
            if isinstance(val, bool):
                return 1 if val else 0
            if isinstance(val, (int, float)):
                return 1 if val > 0 else 0
            return 0

        needs_review = to_bool_int(response_dict.get("needs_review"))
        used_cropped_region = to_bool_int(response_dict.get("used_cropped_region"))
        tree_detector_used = to_bool_int(response_dict.get("tree_detector_used"))
        multiple_trees_detected = to_bool_int(response_dict.get("multiple_trees_detected"))

        timestamp = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                request_id, timestamp, filename, species, raw_species, confidence, 
                species_group, health, age, foliage, image_quality, occlusion, 
                needs_review, processing_time_ms, used_cropped_region, 
                tree_detector_used, tree_detector_status, multiple_trees_detected, 
                tree_candidate_count, ood_similarity, ood_nearest_species
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            request_id,
            timestamp,
            filename,
            response_dict.get("species"),
            response_dict.get("raw_species"),
            response_dict.get("confidence"),
            response_dict.get("species_group"),
            response_dict.get("health"),
            response_dict.get("age"),
            response_dict.get("foliage"),
            response_dict.get("image_quality"),
            response_dict.get("occlusion"),
            needs_review,
            response_dict.get("processing_time_ms"),
            used_cropped_region,
            tree_detector_used,
            response_dict.get("tree_detector_status"),
            multiple_trees_detected,
            response_dict.get("tree_candidate_count"),
            ood_similarity,
            ood_nearest_species
        ))
        conn.commit()
        conn.close()
        print(f"[INFO] Prediction metadata saved to DB for request: {request_id}")
    except Exception as e:
        print(f"[WARNING] Database write failed for request {request_id}: {e}")

def get_all_predictions(limit: int = 100) -> list:
    """
    Query the database for the most recent N predictions.
    Returns a list of dictionaries.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM predictions 
            ORDER BY id DESC 
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        # Convert Row objects to dicts, mapping SQLite integers back to boolean flags
        results = []
        for row in rows:
            r = dict(row)
            r["needs_review"] = bool(r["needs_review"])
            r["used_cropped_region"] = bool(r["used_cropped_region"])
            r["tree_detector_used"] = bool(r["tree_detector_used"])
            r["multiple_trees_detected"] = bool(r["multiple_trees_detected"])
            results.append(r)
        return results
    except Exception as e:
        print(f"[ERROR] Failed to query predictions: {e}")
        return []
