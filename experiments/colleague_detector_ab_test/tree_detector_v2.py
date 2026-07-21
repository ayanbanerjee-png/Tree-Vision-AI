import os
from ultralytics import YOLO
from backend.utils.config import WEIGHTS_DIR

COLLEAGUE_DETECTOR_WEIGHTS = "candidate_detector_colleague.pt"

_colleague_detector_model = None

def load_colleague_detector_model():
    """
    Load the colleague's single-class tree detector model.
    """
    global _colleague_detector_model
    weights_path = os.path.join(WEIGHTS_DIR, COLLEAGUE_DETECTOR_WEIGHTS)
    print(f"Loading colleague tree detector from {weights_path}...")
    try:
        _colleague_detector_model = YOLO(weights_path)
        print("Colleague tree detector loaded successfully!")
    except Exception as e:
        print(f"ERROR: Failed to load colleague tree detector from {weights_path}: {e}")
        _colleague_detector_model = None

# Initialize on import
load_colleague_detector_model()

def detect_and_crop_v2(image_path: str, request_id: str, conf_threshold: float = 0.35,
                       crops_base_dir: str = "/tmp/tree_detector_crops",
                       padding_frac: float = 0.05) -> dict:
    """
    Runs the colleague's single-class tree detector (class 0 'tree'),
    selects the primary tree using the 'largest box by area' rule,
    and crops that box using the standard 5% padding logic.

    Returns a dict with:
      status: 'auto_selected' | 'no_tree_detected' | 'detector_unavailable'
      crop_box: [x1, y1, x2, y2] or None
      cropped_image_path: path to the saved cropped image file, or None
      detected_tree_count: total number of boxes found above the threshold
      all_boxes: list of all detected boxes for logging
    """
    global _colleague_detector_model

    if _colleague_detector_model is None:
        return {
            "status": "detector_unavailable",
            "crop_box": None,
            "cropped_image_path": None,
            "detected_tree_count": 0,
            "all_boxes": [],
        }

    try:
        results = _colleague_detector_model.predict(image_path, conf=conf_threshold, verbose=False)
    except Exception as e:
        print(f"Error in colleague tree detector prediction: {e}")
        return {
            "status": "detector_unavailable",
            "crop_box": None,
            "cropped_image_path": None,
            "detected_tree_count": 0,
            "all_boxes": [],
            "error": str(e),
        }

    result = results[0]
    all_boxes = []

    for box in result.boxes:
        cls_idx = int(box.cls[0])
        cls_name = _colleague_detector_model.names[cls_idx]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])

        all_boxes.append({
            "class": cls_name,
            "confidence": conf,
            "box": [float(x1), float(y1), float(x2), float(y2)],
        })

    detected_tree_count = len(all_boxes)

    if detected_tree_count == 0:
        return {
            "status": "no_tree_detected",
            "crop_box": None,
            "cropped_image_path": None,
            "detected_tree_count": 0,
            "all_boxes": [],
        }

    # Find the largest box by area
    largest_idx = 0
    largest_area = 0.0
    for idx, b in enumerate(all_boxes):
        box_coords = b["box"]
        w = box_coords[2] - box_coords[0]
        h = box_coords[3] - box_coords[1]
        area = w * h
        if area > largest_area:
            largest_area = area
            largest_idx = idx

    selected = all_boxes[largest_idx]
    crop_box = selected["box"]

    # Crop the box using standard PIL cropping and 5% padding
    from PIL import Image
    import os as _os

    try:
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

        return {
            "status": "auto_selected",
            "crop_box": crop_box,
            "cropped_image_path": out_path,
            "detected_tree_count": detected_tree_count,
            "all_boxes": all_boxes,
        }
    except Exception as crop_err:
        print(f"[WARNING] Failed to crop tree in colleague detector path: {crop_err}")
        return {
            "status": "detector_unavailable",
            "crop_box": crop_box,
            "cropped_image_path": None,
            "detected_tree_count": detected_tree_count,
            "all_boxes": all_boxes,
            "error": str(crop_err)
        }

def cleanup_tree_crop_v2(request_id: str, crops_base_dir: str = "/tmp/tree_detector_crops"):
    """Removes the per-request crop folder."""
    import shutil as _shutil
    request_dir = os.path.join(crops_base_dir, request_id)
    if os.path.isdir(request_dir):
        _shutil.rmtree(request_dir, ignore_errors=True)
