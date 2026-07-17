import os
import sys
import json
import time

# Add root directory to sys.path to enable backend imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.predict import predict_tree

def run_batch():
    demo_dir = os.path.join(root_dir, "backend", "demo_candidates")
    results_path = os.path.join(demo_dir, "batch_results.json")
    
    if not os.path.exists(demo_dir):
        os.makedirs(demo_dir, exist_ok=True)
        
    # Get all image files (case-insensitive extensions)
    valid_exts = (".jpg", ".jpeg", ".png")
    all_files = os.listdir(demo_dir)
    image_files = [f for f in all_files if f.lower().endswith(valid_exts)]
    
    print(f"Starting batch run. Found {len(image_files)} image(s) in {demo_dir}.")
    
    results = []
    detector_unavailable_found = False
    
    start_batch_time = time.perf_counter()
    
    for filename in image_files:
        image_path = os.path.join(demo_dir, filename)
        
        # input_type logic:
        # Calls predict_tree(image_path) on each one, with input_type="single_tree"
        # unless the filename contains "multi" (then use whatever input_type is
        # appropriate per existing pipeline conventions -- check predict.py for how
        # input_type is normally chosen).
        # Checking backend/predict.py and backend/models/quality.py, the default
        # input_type is "single_tree", and the only other specialized check is "tree_crop"
        # in assess_quality(). Therefore, the appropriate input_type for full-frame
        # images (including those containing "multi" in the filename) is "single_tree".
        input_type = "single_tree"
        
        try:
            res = predict_tree(image_path, input_type=input_type)
            results.append({
                "filename": filename,
                "response": res
            })
            
            # Print console summary
            species = res.get("species", "N/A")
            confidence = res.get("confidence", 0.0)
            needs_review = res.get("needs_review", False)
            status = res.get("tree_detector_status", "N/A")
            
            if status == "detector_unavailable":
                detector_unavailable_found = True
                
            print(f"{filename} -> species={species}, confidence={confidence}, needs_review={needs_review}, tree_detector_status={status}")
            
        except Exception as e:
            results.append({
                "filename": filename,
                "error": str(e)
            })
            print(f"{filename} -> error: {str(e)}")
            
    total_time = time.perf_counter() - start_batch_time
    
    # Save results to batch_results.json
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n--------------------------------------------------")
    print(f"Batch run complete.")
    print(f"Processed: {len(image_files)} image(s)")
    print(f"Total time elapsed: {total_time:.2f} seconds")
    print(f"Results written to: {results_path}")
    
    if detector_unavailable_found:
        print("[WARNING] AT LEAST ONE IMAGE ENCOUNTERED tree_detector_status='detector_unavailable'!")
        print("This indicates that the detector weights are not loading correctly in this environment.")
    else:
        print("All processed images successfully completed without 'detector_unavailable'.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_batch()
