import os
import pandas as pd

# Setup paths
PROJECT_ROOT = os.getenv("PROJECT_DATA_ROOT", os.path.join(os.path.expanduser("~"), "Flocard Tree AI", "data"))
TARGET_DIR = os.path.join(PROJECT_ROOT, "own", "single_tree")

def check_manifests():
    print("====================================================")
    # Scan target directory
    print(f"Scanning: {TARGET_DIR}\n")
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory does not exist: {TARGET_DIR}")
        return
        
    manifest_present = []
    manifest_missing = []
    example_file = None
    
    for root, dirs, files in os.walk(TARGET_DIR):
        # We only check species folders (which contain image files and are leaf folders)
        images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            continue
            
        species_folder = os.path.relpath(root, TARGET_DIR)
        manifest_path = os.path.join(root, "license_manifest.csv")
        
        if os.path.exists(manifest_path):
            manifest_present.append(species_folder)
            if example_file is None:
                example_file = manifest_path
        else:
            manifest_missing.append(species_folder)
            
    print("--- 1. SPECIES FOLDERS WITH MANIFEST ---")
    if manifest_present:
        for folder in sorted(manifest_present):
            print(f"  [PRESENT] {folder}")
    else:
        print("  None")
    print()
        
    print("--- 2. SPECIES FOLDERS MISSING MANIFEST ---")
    if manifest_missing:
        for folder in sorted(manifest_missing):
            print(f"  [MISSING] {folder}")
    else:
        print("  None")
    print()

    # Show first 5 rows of one example manifest
    print("--- 3. EXAMPLE MANIFEST FIRST 5 ROWS ---")
    if example_file:
        print(f"Example File: {example_file}\n")
        try:
            df = pd.read_csv(example_file)
            print(df.head(5).to_string(index=False))
        except Exception as e:
            print(f"Error reading manifest: {e}")
    else:
        print("No manifest files were found to display an example.")

if __name__ == "__main__":
    check_manifests()
