import os
import csv
import cv2
import numpy as np

# Adjust this if your actual data root differs
PROJECT_ROOT = os.getenv("PROJECT_DATA_ROOT", os.path.join(os.path.expanduser("~"), "Flocard Tree AI", "data"))

SCAN_ROOTS = [
    os.path.join(PROJECT_ROOT, "own", "single_tree"),
    os.path.join(PROJECT_ROOT, "own", "cluster"),
    os.path.join(PROJECT_ROOT, "own", "tree_crop"),
    os.path.join(PROJECT_ROOT, "combined", "standardised"),
]

def vegetation_fraction(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = np.array([25, 30, 20])
    upper_green = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    return float(np.sum(mask > 0)) / mask.size

def sky_fraction(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    top_third = img[0:h // 3, :, :]
    hsv = cv2.cvtColor(top_third, cv2.COLOR_BGR2HSV)
    mask = (hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 120)
    return float(np.sum(mask)) / mask.size

results = []

for root in SCAN_ROOTS:
    if not os.path.exists(root):
        print(f"[SKIP] Not found: {root}")
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        images = [f for f in filenames if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            continue
        species_name = os.path.basename(dirpath)
        veg_fracs, sky_fracs = [], []
        for fname in images[:15]:
            fpath = os.path.join(dirpath, fname)
            vf = vegetation_fraction(fpath)
            sf = sky_fraction(fpath)
            if vf is not None:
                veg_fracs.append(vf)
            if sf is not None:
                sky_fracs.append(sf)
        if not veg_fracs:
            continue
        avg_veg = float(np.mean(veg_fracs))
        avg_sky = float(np.mean(sky_fracs)) if sky_fracs else 0.0
        results.append({
            "folder": dirpath,
            "species": species_name,
            "n_sampled": len(veg_fracs),
            "avg_vegetation_fraction": round(avg_veg, 3),
            "avg_sky_fraction_top_third": round(avg_sky, 3),
        })
        print(f"{species_name:30s} veg={avg_veg:.2f}  sky={avg_sky:.2f}  (n={len(veg_fracs)}, path={dirpath})")

out_path = os.path.join(PROJECT_ROOT, "shot_type_report.csv")
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["folder", "species", "n_sampled", "avg_vegetation_fraction", "avg_sky_fraction_top_third"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved report to: {out_path}")
print("\nInterpretation guide:")
print("  avg_vegetation_fraction > 0.55            -> likely close-up leaf/needle shots (same pattern as Cedrus_deodara)")
print("  avg_vegetation_fraction < 0.35 AND avg_sky_fraction > 0.2 -> likely distant/whole-tree shots against sky")
print("  Species with HIGH vegetation_fraction are most at risk of failing on distant real-world test photos.")
