import os
from ultralytics import YOLO
from backend.utils.config import WEIGHTS_DIR

# Thresholds from Notebook 08
OCCLUSION_AREA_THRESHOLD = 0.15  # fraction of frame area

# COCO classes considered for occlusion from Notebook 08
OCCLUDING_CLASSES = {
    'person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle',
    'dog', 'cat', 'horse', 'cow', 'sheep', 'bench', 'umbrella',
    'backpack', 'suitcase', 'chair',
}

# Global YOLO model loaded once during startup
_yolo_model = None

def load_yolo_model():
    """
    Load YOLOv8 model architecture and weights.
    Loads once during startup.
    """
    global _yolo_model
    weights_path = os.path.join(WEIGHTS_DIR, "yolov8n.pt")
    
    print(f"Loading YOLOv8 model from {weights_path}...")
    try:
        # Load local yolov8n.pt weights
        _yolo_model = YOLO(weights_path)
        print("YOLOv8 occlusion model loaded successfully!")
    except Exception as e:
        print(f"Warning: Failed to load YOLOv8 from local path ({e}). Falling back to network download.")
        # Fallback to auto-download if local loading fails
        _yolo_model = YOLO("yolov8n.pt")

# Initialize model on import
load_yolo_model()

def detect_occlusion(image_path: str, conf_threshold: float = 0.4) -> dict:
    """
    Detect image occlusion using YOLOv8, preserving the exact behavior of Notebook 08.
    """
    global _yolo_model
    
    try:
        # Run inference using the loaded model instance
        results = _yolo_model.predict(image_path, verbose=False, conf=conf_threshold)
    except Exception as e:
        print(f"Error in YOLOv8 occlusion prediction: {e}")
        return {
            "occlusion": "None",
            "detected_objects": [],
            "needs_review": False,
            "error": str(e)
        }

    result = results[0]
    img_h, img_w = result.orig_shape
    frame_area = img_h * img_w

    detected_objects = []
    yolo_boxes = []
    for box in result.boxes:
        cls_idx = int(box.cls[0])
        cls_name = _yolo_model.names[cls_idx]
        
        # If potted plant, collect as potential tree box candidate
        if cls_name == 'potted plant':
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            yolo_boxes.append([float(x1), float(y1), float(x2), float(y2)])
            
        # Keep only classes defined in OCCLUDING_CLASSES
        if cls_name not in OCCLUDING_CLASSES:
            continue
            
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        box_area = (x2 - x1) * (y2 - y1)
        area_frac = box_area / frame_area
        
        detected_objects.append({
            'class': cls_name,
            'confidence': float(box.conf[0]),
            'area_fraction': float(area_frac),
        })

    # Evaluate occlusion flags matching Notebook 08 logic
    is_occluded = any(o['area_fraction'] >= OCCLUSION_AREA_THRESHOLD for o in detected_objects)
    
    # Map to requested "None | Partial | Heavy" labels and review status
    if is_occluded:
        occlusion_label = "Heavy"
        needs_review = True
    elif len(detected_objects) > 0:
        occlusion_label = "Partial"
        needs_review = False
    else:
        occlusion_label = "None"
        needs_review = False

    return {
        "occlusion": occlusion_label,
        "detected_objects": detected_objects,
        "needs_review": needs_review,
        "yolo_boxes": yolo_boxes
    }
