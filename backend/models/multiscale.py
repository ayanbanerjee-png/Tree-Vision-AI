import os
import shutil
import cv2
import numpy as np
from PIL import Image
from backend.utils.config import TEMP_DIR

def find_vegetation_crop(image_path, padding_frac=0.15, min_area_frac=0.03, min_size=100):
    """
    Finds a vegetation-colored region likely to be tree canopy (not ground
    vegetation like grass/hedges) using HSV color segmentation, and returns a
    tight crop around it (with padding). Non-ML alternative to YOLO tree
    localization, since COCO has no usable tree class.
    Returns None if no significant, canopy-like vegetation region is found.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return None
    h, w = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lower_green = np.array([25, 30, 20])
    upper_green = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Filter to contours large enough to matter, then score each candidate
    # instead of blindly picking the single largest area. Ground vegetation
    # (grass, hedges, lawns) tends to be wide/short and sits low in the frame.
    # Tree canopies tend to be taller-than-wide (or roughly square) and sit
    # higher in the frame. Score candidates to prefer canopy-like shapes.
    candidates_scored = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < (min_area_frac * w * h):
            continue
        x, y, cw, ch = cv2.boundingRect(c)
        if cw == 0 or ch == 0:
            continue
        aspect_ratio = ch / cw  # >1 means taller than wide
        vertical_center_frac = (y + ch / 2) / h  # 0 = top of frame, 1 = bottom
        # Score: reward tall/square shapes and upper-frame position, penalize
        # wide/flat shapes low in the frame (likely grass/hedge/ground cover).
        shape_score = min(aspect_ratio, 2.0)  # cap so extremely tall thin slivers don't dominate
        position_score = max(0.0, 1.0 - vertical_center_frac)  # higher = closer to top
        combined_score = (area / (w * h)) * (0.4 + 0.4 * shape_score + 0.2 * position_score)
        candidates_scored.append((combined_score, x, y, cw, ch))

    if not candidates_scored:
        return None

    candidates_scored.sort(key=lambda t: t[0], reverse=True)
    _, x, y, cw, ch = candidates_scored[0]

    # Resolution floor — skip if resulting crop would be too small (consistent
    # with the existing blind-crop resolution floor).
    if cw < min_size or ch < min_size:
        return None

    # Aspect ratio sanity check — if the best candidate is still very wide and
    # short (e.g. > 2.2:1 width:height), it's more likely ground vegetation
    # or a hedge than a canopy; discard rather than risk a bad crop.
    if cw / ch > 2.2:
        return None

    pad_x = int(cw * padding_frac)
    pad_y = int(ch * padding_frac)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(w, x + cw + pad_x)
    y1 = min(h, y + ch + pad_y)

    img_pil = Image.open(image_path).convert('RGB')
    crop = img_pil.crop((x0, y0, x1, y1))
    return crop

def generate_crop_candidates(image_path, request_id, scales=(0.6, 0.4, 0.25), target_ar=0.6, min_size=100):
    """
    Generates a bounded set of portrait-ish crop candidates for street-view tree photos.
    - First center-crops the image to a portrait-ish aspect ratio (target_ar).
    - Then slides horizontally at each scale to produce up to 3 crops (left, center, right).
    - Scales largest-scale-first to enable early stopping.
    - Enforces resolution floor of 100x100px.
    - Saves crops under backend/temp/crops_{request_id}/.
    """
    img = Image.open(image_path).convert('RGB')
    w, h = img.size

    # 1. Determine the center-cropped portrait size
    if w / h > target_ar:
        # Image is wider than target aspect ratio (landscape/wide)
        # Keep height, crop width
        pw = int(h * target_ar)
        ph = h
        px = (w - pw) // 2
        py = 0
    else:
        # Image is taller than target aspect ratio (very tall portrait)
        # Keep width, crop height
        pw = w
        ph = int(w / target_ar)
        px = 0
        py = (h - ph) // 2

    portrait_img = img.crop((px, py, px + pw, py + ph))

    # Create a request-specific temporary folder under TEMP_DIR
    tmp_dir = os.path.join(TEMP_DIR, f"crops_{request_id}")
    os.makedirs(tmp_dir, exist_ok=True)

    # Always include the original full image first
    candidates = [image_path]

    # Try to find a vegetation crop first
    try:
        veg_img = find_vegetation_crop(image_path)
        if veg_img is not None:
            veg_path = os.path.join(tmp_dir, "veg_crop.jpg")
            veg_img.save(veg_path, quality=92)
            candidates.append(veg_path)
            print(f"[INFO] Vegetation-guided crop succeeded and added as candidate: {veg_path}")
    except Exception as veg_err:
        print(f"[WARNING] Error generating vegetation-guided crop: {veg_err}")

    # Generate crops for each scale, largest first
    for scale in scales:
        cw, ch = int(pw * scale), int(ph * scale)
        
        # Enforce resolution floor
        if cw < min_size or ch < min_size:
            continue
            
        # Define horizontal sliding positions: Left, Center, Right
        x_positions = [0, (pw - cw) // 2, pw - cw]
        y = (ph - ch) // 2  # Keep vertically centered
        
        # Extract unique crops
        seen_x = set()
        for x in x_positions:
            if x in seen_x:
                continue
            seen_x.add(x)
            
            crop = portrait_img.crop((x, y, x + cw, y + ch))
            crop_path = os.path.join(tmp_dir, f"crop_{scale}_{x}_{y}.jpg")
            crop.save(crop_path, quality=92)
            candidates.append(crop_path)

    return candidates, tmp_dir

def cleanup_crops(tmp_dir):
    """
    Safely deletes the temporary folder and all files inside.
    """
    if tmp_dir and os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

def generate_smart_crop(image_path, request_id, yolo_boxes, padding_pct=0.12):
    """
    If exactly one tree bounding box is present, crops the region with padding and returns its path.
    Otherwise returns an empty list.
    """
    if len(yolo_boxes) != 1:
        return []

    try:
        img = Image.open(image_path).convert('RGB')
        w, h = img.size
        
        x1, y1, x2, y2 = yolo_boxes[0]
        bw = x2 - x1
        bh = y2 - y1
        
        pad_w = bw * padding_pct
        pad_h = bh * padding_pct
        
        new_x1 = max(0, int(round(x1 - pad_w)))
        new_y1 = max(0, int(round(y1 - pad_h)))
        new_x2 = min(w, int(round(x2 + pad_w)))
        new_y2 = min(h, int(round(y2 + pad_h)))
        
        # Verify crop size is reasonable
        if (new_x2 - new_x1) < 100 or (new_y2 - new_y1) < 100:
            return []

        tmp_dir = os.path.join(TEMP_DIR, f"crops_{request_id}")
        os.makedirs(tmp_dir, exist_ok=True)
        
        crop_path = os.path.join(tmp_dir, "smart_crop.jpg")
        crop = img.crop((new_x1, new_y1, new_x2, new_y2))
        crop.save(crop_path, quality=92)
        
        return [crop_path]
    except Exception as e:
        print(f"[WARNING] Error generating smart crop: {e}")
        return []
