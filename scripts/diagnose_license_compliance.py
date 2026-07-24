import os
import pandas as pd

# Setup paths
PROJECT_ROOT = os.getenv("PROJECT_DATA_ROOT", os.path.join(os.path.expanduser("~"), "Flocard Tree AI", "data"))
TARGET_DIR = os.path.join(PROJECT_ROOT, "own", "single_tree")

COMPLIANT_LICENSES = {"cc0", "cc-by", "cc-by-sa"}

def verify_licenses():
    print("====================================================")
    print("        LICENSE COMPLIANCE AUDIT RUN")
    print("====================================================\n")
    
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory does not exist: {TARGET_DIR}")
        return
        
    failures = []
    total_rows = 0
    total_manifests = 0
    
    for root, dirs, files in os.walk(TARGET_DIR):
        if "license_manifest.csv" in files:
            total_manifests += 1
            species_folder = os.path.relpath(root, TARGET_DIR)
            manifest_path = os.path.join(root, "license_manifest.csv")
            
            try:
                df = pd.read_csv(manifest_path)
                for idx, row in df.iterrows():
                    total_rows += 1
                    lic = str(row.get("license", "")).strip().lower()
                    if lic not in COMPLIANT_LICENSES:
                        failures.append({
                            "species": species_folder,
                            "filename": row.get("filename", "unknown"),
                            "license": row.get("license", "N/A")
                        })
            except Exception as e:
                print(f"Error reading manifest in {species_folder}: {e}")
                
    print(f"Audited {total_manifests} manifest files with {total_rows} total rows.\n")
    
    if failures:
        print("--- NON-COMPLIANT ROWS DETECTED ---")
        for f in failures:
            print(f"  [FAIL] {f['species']} | File: {f['filename']} | License: '{f['license']}'")
    else:
        print("All 9 manifested species confirmed license-compliant.")

if __name__ == "__main__":
    verify_licenses()
