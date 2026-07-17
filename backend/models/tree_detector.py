import os
from ultralytics import YOLO
from backend.utils.config import WEIGHTS_DIR

# Trained locally per docs/assumptions.md -- 4-class tree target detector
# (StreetScouting + tree-detection-7fajo, see assumptions doc for full
# dataset/licensing provenance).
TREE_DETECTOR_WEIGHTS = "tree_target_detector_best.pt"

# Confidence threshold for accepting a detection at all
DETECTOR_CONF_THRESHOLD = 0.35

# Below this fraction of frame area, a target_tree box is considered "distant"
# -- matches the crop_area_ratio logic from the original detector design doc.
DISTANT_CROP_AREA_RATIO = 0.08

# Global YOLO model loaded once during startup, same pattern as occlusion.py
_tree_detector_model = None


def load_tree_detector_model():
    """
    Load the trained 4-class tree detector (target_tree / tree_canopy /
    tree_trunk / partial_tree). Loads once during startup.
    """
    global _tree_detector_model
    weights_path = os.path.join(WEIGHTS_DIR, TREE_DETECTOR_WEIGHTS)

    print(f"Loading tree target detector from {weights_path}...")
    try:
        _tree_detector_model = YOLO(weights_path)
        print("Tree target detector loaded successfully!")
    except Exception as e:
        print(f"ERROR: Failed to load tree target detector from {weights_path}: {e}")
        print("Tree detection step will be SKIPPED -- pipeline will fall back to "
              "running the species classifier on the full, uncropped image, "
              "same as before this detector existed.")
        _tree_detector_model = None


# Initialize model on import, same pattern as occlusion.py
load_tree_detector_model()


def detect_target_tree(image_path: str, conf_threshold: float = DETECTOR_CONF_THRESHOLD) -> dict:
    """
    Runs the tree target detector on an image and decides what the rest of
    the pipeline should do next. Mirrors the review-rule design from the
    original detector planning doc.

    Returns a dict with:
      status: one of
          "auto_selected"       -- exactly one target_tree found, safe to crop and continue
          "needs_user_selection" -- multiple target_tree candidates, ambiguous
          "no_tree_detected"    -- nothing found above threshold
          "detector_unavailable" -- model failed to load; caller should fall
                                     back to running the classifier on the
                                     full original image, unchanged
      crop_box: [x1, y1, x2, y2] of the selected target_tree, or None
      image_context: "distant_tree" | "normal" | None
      detected_tree_count: int (count of target_tree-class boxes only)
      all_boxes: list of every tree-related box found (any of the 4 classes),
                 for logging / potential future use (e.g. surfacing
                 tree_canopy count to the user in a "multi-tree scene" message)
    """
    global _tree_detector_model

    if _tree_detector_model is None:
        return {
            "status": "detector_unavailable",
            "crop_box": None,
            "image_context": None,
            "detected_tree_count": 0,
            "all_boxes": [],
        }

    try:
        results = _tree_detector_model.predict(image_path, verbose=False, conf=conf_threshold)
    except Exception as e:
        print(f"Error in tree detector prediction: {e}")
        return {
            "status": "detector_unavailable",
            "crop_box": None,
            "image_context": None,
            "detected_tree_count": 0,
            "all_boxes": [],
            "error": str(e),
        }

    result = results[0]
    img_h, img_w = result.orig_shape
    frame_area = img_h * img_w

    all_boxes = []
    target_tree_boxes = []

    for box in result.boxes:
        cls_idx = int(box.cls[0])
        cls_name = _tree_detector_model.names[cls_idx]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])

        box_info = {
            "class": cls_name,
            "confidence": conf,
            "box": [float(x1), float(y1), float(x2), float(y2)],
        }
        all_boxes.append(box_info)

        if cls_name == "target_tree":
            target_tree_boxes.append(box_info)

    detected_tree_count = len(target_tree_boxes)

    if detected_tree_count == 0:
        return {
            "status": "no_tree_detected",
            "crop_box": None,
            "image_context": None,
            "detected_tree_count": 0,
            "all_boxes": all_boxes,
        }

    if detected_tree_count > 1:
        return {
            "status": "needs_user_selection",
            "crop_box": None,
            "image_context": None,
            "detected_tree_count": detected_tree_count,
            "all_boxes": all_boxes,
        }

    # Exactly one target_tree -- auto-select it
    selected = target_tree_boxes[0]
    x1, y1, x2, y2 = selected["box"]
    crop_area = (x2 - x1) * (y2 - y1)
    crop_area_ratio = crop_area / frame_area if frame_area > 0 else 0

    image_context = "distant_tree" if crop_area_ratio < DISTANT_CROP_AREA_RATIO else "normal"

    return {
        "status": "auto_selected",
        "crop_box": [x1, y1, x2, y2],
        "image_context": image_context,
        "detected_tree_count": 1,
        "all_boxes": all_boxes,
    }


def crop_target_tree_and_save(image_path: str, crop_box: list, request_id: str,
                                crops_base_dir: str = "/tmp/tree_detector_crops",
                                padding_frac: float = 0.05) -> str:
    """
    Crops the target_tree region out of the original image and saves it to a
    new file, so the rest of the pipeline (which expects a file path) can run
    on the cropped region unchanged.

    A small padding margin is added around the box (default 5% of box size)
    since a perfectly tight crop can cut off edge details the classifier
    relies on (bark texture at the trunk base, leaf tips, etc.).

    Returns the path to the saved crop. Caller is responsible for deleting
    this file (and the per-request folder) once done -- see cleanup_tree_crop().
    """
    from PIL import Image
    import os as _os

    os.makedirs(crops_base_dir, exist_ok=True)
    request_dir = _os.path.join(crops_base_dir, request_id)
    os.makedirs(request_dir, exist_ok=True)

    img = Image.open(image_path)
    img_w, img_h = img.size

    x1, y1, x2, y2 = crop_box
    box_w, box_h = x2 - x1, y2 - y1
    pad_x, pad_y = box_w * padding_frac, box_h * padding_frac

    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(img_w, x2 + pad_x)
    y2 = min(img_h, y2 + pad_y)

    cropped = img.crop((int(x1), int(y1), int(x2), int(y2)))
    out_path = _os.path.join(request_dir, "target_tree_crop.jpg")
    cropped.convert("RGB").save(out_path, quality=95)

    return out_path


def cleanup_tree_crop(request_id: str, crops_base_dir: str = "/tmp/tree_detector_crops"):
    """Removes the per-request crop folder created by crop_target_tree_and_save()."""
    import shutil as _shutil
    request_dir = os.path.join(crops_base_dir, request_id)
    if os.path.isdir(request_dir):
        _shutil.rmtree(request_dir, ignore_errors=True)
