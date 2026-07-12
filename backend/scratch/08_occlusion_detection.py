# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT   = r'C:\Users\AYAN\Flocard Tree AI'
COMBINED_ROOT   = os.path.join(PROJECT_ROOT, 'data', 'combined')
MODELS_ROOT     = os.path.join(PROJECT_ROOT, 'models')

SPLIT_PATH       = os.path.join(COMBINED_ROOT, 'labels_split.csv')

os.makedirs(MODELS_ROOT, exist_ok=True)
print('Paths set successfully')

# ==========================================
# CELL 4
# ==========================================
from ultralytics import YOLO
import pandas as pd
import numpy as np
import cv2
import warnings
warnings.filterwarnings('ignore')

print('Ultralytics loaded')

# ==========================================
# CELL 6
# ==========================================
yolo_model = YOLO('yolov8n.pt')

# COCO classes that plausibly occlude a tree photo in the field
OCCLUDING_CLASSES = {
    'person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle',
    'dog', 'cat', 'horse', 'cow', 'sheep', 'bench', 'umbrella',
    'backpack', 'suitcase', 'chair',
}

print(f'YOLOv8n loaded. Watching for {len(OCCLUDING_CLASSES)} occluding object classes.')

# ==========================================
# CELL 8
# ==========================================
OCCLUSION_AREA_THRESHOLD = 0.15  # fraction of frame area; adjust after reviewing Cell 6 examples

def detect_occlusion(image_path, conf_threshold=0.4):
    try:
        results = yolo_model.predict(image_path, verbose=False, conf=conf_threshold)
    except Exception as e:
        return {'occluded': False, 'occluding_objects': [], 'error': str(e)}

    result = results[0]
    img_h, img_w = result.orig_shape
    frame_area = img_h * img_w

    occluding_objects = []
    for box in result.boxes:
        cls_name = yolo_model.names[int(box.cls[0])]
        if cls_name not in OCCLUDING_CLASSES:
            continue
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        box_area = (x2 - x1) * (y2 - y1)
        area_frac = box_area / frame_area
        occluding_objects.append({
            'class': cls_name,
            'confidence': float(box.conf[0]),
            'area_fraction': float(area_frac),
        })

    is_occluded = any(o['area_fraction'] >= OCCLUSION_AREA_THRESHOLD for o in occluding_objects)
    return {'occluded': is_occluded, 'occluding_objects': occluding_objects}

print('Occlusion detection function ready.')

# ==========================================
# CELL 10
# ==========================================
SAMPLE_SIZE = 100
RANDOM_STATE = 42

df = pd.read_csv(SPLIT_PATH)
candidates = df[df['image_quality'].isin(['clear', 'uncertain'])].copy()
candidates['use_path'] = candidates.apply(
    lambda r: r['std_path'] if isinstance(r.get('std_path'), str) and os.path.exists(r['std_path'])
              else r['image_path'],
    axis=1
)
candidates = candidates[candidates['use_path'].apply(os.path.exists)]

sample = candidates.sample(n=min(SAMPLE_SIZE, len(candidates)), random_state=RANDOM_STATE)
print(f'Checking {len(sample)} images currently labeled clear/uncertain for occlusion...')

occlusion_results = []
for _, row in sample.iterrows():
    res = detect_occlusion(row['use_path'])
    res['image_path'] = row['use_path']
    res['current_label'] = row['image_quality']
    occlusion_results.append(res)

occluded_count = sum(1 for r in occlusion_results if r['occluded'])
print(f'\nFlagged as occluded: {occluded_count} / {len(sample)}')

# ==========================================
# CELL 12
# ==========================================
flagged = [r for r in occlusion_results if r['occluded']]

for r in flagged[:15]:
    print(f"{r['image_path']}")
    print(f"  current label: {r['current_label']}")
    for obj in r['occluding_objects']:
        print(f"  -> {obj['class']} (conf {obj['confidence']:.2f}, {obj['area_fraction']:.1%} of frame)")
    print()

if not flagged:
    print('No images flagged as occluded in this sample. Consider lowering')
    print('OCCLUSION_AREA_THRESHOLD and re-running Cell 5 if this seems too strict,')
    print('or take it as a genuine (if unverified) sign occlusion is rare in this dataset.')

# ==========================================
# CELL 14
# ==========================================
import shutil

QUARANTINE_ROOT = os.path.join(PROJECT_ROOT, 'data', 'quarantine')

def quarantine_images_by_filename(folder, filenames, quarantine_root=QUARANTINE_ROOT, project_root=PROJECT_ROOT):
    rel = os.path.relpath(folder, project_root)
    dest_folder = os.path.join(quarantine_root, rel)
    os.makedirs(dest_folder, exist_ok=True)
    moved = 0
    for fname in filenames:
        src = os.path.join(folder, fname)
        if not os.path.exists(src):
            print(f'Not found, skipping: {src}')
            continue
        shutil.move(src, os.path.join(dest_folder, fname))
        print(f'Quarantined : {fname}')
        moved += 1
    return moved

# Confirmed non-tree contamination, surfaced incidentally by YOLO's person-detection
# flagging a hand as the dominant subject rather than any tree content.
ficus_path = os.path.join(PROJECT_ROOT, r"data\combined\standardised\broadleaf\Ficus_religiosa")
quarantine_images_by_filename(ficus_path, ["87.jpg"])

cedrus_path = os.path.join(PROJECT_ROOT, r"data\combined\standardised\conifer\Cedrus_deodara")
quarantine_images_by_filename(cedrus_path, ["Cedrus_deodara_0052.jpg"])

calotropis_path = os.path.join(PROJECT_ROOT, r"data\combined\standardised\shrub\Calotropis_procera")
quarantine_images_by_filename(calotropis_path, ["Calotropis_procera_0027.jpg"])

# Borderline -- plant is visibly present but marginal in frame. Not quarantined
# automatically; review data/combined/standardised/shrub/Lantana_camara/Lantana_camara_0020.jpg
# directly and quarantine manually if you decide it's not usable.
print("\nLantana_camara_0020.jpg NOT quarantined -- borderline, review manually if desired.")

# ==========================================
# CELL 15
# ==========================================
full_split_df = pd.read_csv(SPLIT_PATH)

lantana_exact_path = os.path.join(
    PROJECT_ROOT, r"data\combined\standardised\shrub\Lantana_camara\Lantana_camara_0020.jpg"
)
mask = (full_split_df['image_path'] == lantana_exact_path) | (full_split_df['std_path'] == lantana_exact_path)

if mask.sum() == 0:
    print('No matching row found -- check the exact path is correct.')
else:
    full_split_df.loc[mask, 'image_quality'] = 'occluded'
    full_split_df.to_csv(SPLIT_PATH, index=False)
    print(f'Updated {mask.sum()} row(s) to occluded.')
    print(full_split_df['image_quality'].value_counts())

# ==========================================
# CELL 17
# ==========================================
BACKUP_PATH = SPLIT_PATH.replace('.csv', '_backup_before_occlusion.csv')
if not os.path.exists(BACKUP_PATH):
    import shutil
    shutil.copy(SPLIT_PATH, BACKUP_PATH)
    print(f'Backed up to: {BACKUP_PATH}')

full_split_df = pd.read_csv(SPLIT_PATH)
occluded_paths = {r['image_path'] for r in occlusion_results if r['occluded']}

# Match against BOTH std_path and image_path as they were recorded in labels_split.csv,
# rather than recomputing use_path live -- avoids silent mismatches when a path that
# was valid at detection time (Cell 5) no longer exists later (e.g. after quarantine).
mask = full_split_df['std_path'].isin(occluded_paths) | full_split_df['image_path'].isin(occluded_paths)

# Flag any occluded_paths that didn't match ANYTHING in the current split file --
# likely quarantined since detection ran, worth knowing about rather than silently dropping.
matched_paths = set(full_split_df.loc[mask, 'std_path']) | set(full_split_df.loc[mask, 'image_path'])
unmatched = occluded_paths - matched_paths
if unmatched:
    print(f'Warning: {len(unmatched)} occluded detection(s) did not match any current row')
    print('(likely quarantined since detection ran):')
    for p in unmatched:
        print(f'  {p}')

full_split_df.loc[mask, 'image_quality'] = 'occluded'
full_split_df.to_csv(SPLIT_PATH, index=False)

print(f'\nUpdated {mask.sum()} rows to image_quality = occluded')
print(full_split_df['image_quality'].value_counts())

# ==========================================
# CELL 19
# ==========================================
print('=' * 60)
print('NOTEBOOK 08 COMPLETE — OCCLUSION DETECTION')
print('=' * 60)
print(f'Images checked (clear/uncertain sample) : {len(sample)}')
print(f'Flagged and applied as occluded          : {mask.sum()}')
print()
print('NOT implemented in this notebook -- per-tree detection/counting in')
print('cluster images. Requires manual bounding-box annotation of individual')
print('trees in a set of cluster photos, then YOLOv8 fine-tuning on that data.')
print('This is an open task, documented in docs/failure_cases.md, not a silent')
print('gap -- input_type classification for cluster images remains the current')
print('manual folder-based approach until this labeling effort happens.')
print('=' * 60)

# ==========================================
# CELL 20
# ==========================================


