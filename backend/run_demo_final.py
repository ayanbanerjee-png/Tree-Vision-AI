import os
import sys
import json
import time

# Add root directory to sys.path to enable backend imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.predict import predict_tree

def run_final_demo():
    final_dir = os.path.join(root_dir, "backend", "demo_final")
    results_path = os.path.join(final_dir, "batch_results.json")
    
    # The 7 expected files
    filenames = [
        "demo_1_clean_win.jpg",
        "demo_2_safety_gate.jpg",
        "demo_3_detector_avenue.jpg",
        "demo_4_backup_saraca.jpg",
        "demo_5_optional_qa.jpg",
        "demo_6_clean_win_coconut.jpg",
        "demo_7_clean_win_cassia.jpg"
    ]
    
    print(f"Starting final demo validation run on {len(filenames)} images...")
    
    results = []
    
    for filename in filenames:
        image_path = os.path.join(final_dir, filename)
        if not os.path.exists(image_path):
            print(f"[ERROR] Missing file: {image_path}")
            continue
            
        print(f"Running inference on {filename}...")
        start_time = time.perf_counter()
        
        try:
            res = predict_tree(image_path, input_type="single_tree")
            elapsed = time.perf_counter() - start_time
            print(f"Completed {filename} in {elapsed:.2f}s")
            
            results.append({
                "filename": filename,
                "response": res
            })
        except Exception as e:
            print(f"[ERROR] Failed on {filename}: {e}")
            results.append({
                "filename": filename,
                "error": str(e)
            })
            
    # Save results to batch_results.json
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n--------------------------------------------------")
    print(f"Final demo validation complete. Results written to: {results_path}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_final_demo()
