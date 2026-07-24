import os
import json
import numpy as np
import torch
import torch.nn as nn
import timm
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
from backend.utils.config import DEVICE, MODEL_WEIGHTS

# Constants from Notebook 03
IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]
MODEL_NAME = 'tf_efficientnetv2_s.in1k'

# Preprocessing transforms from Notebook 03 eval_transform
eval_transform = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ToTensorV2(),
])

# Global model state loaded once
_model = None
_class_names = []
_species_to_group = {}
_common_names = {}
_high_conf_threshold = 0.70
_med_conf_threshold = 0.40

def build_model(model_name, num_classes, pretrained=False, freeze_through_block=-1, dropout_p=0.3):
    """
    Builds the model architecture exactly as in Notebook 03.
    """
    model = timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)
    if freeze_through_block >= 0:
        frozen_modules = [model.conv_stem, model.bn1] + [model.blocks[i] for i in range(freeze_through_block + 1)]
        for m in frozen_modules:
            for p in m.parameters():
                p.requires_grad = False

    if dropout_p > 0:
        in_features = model.classifier.in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=dropout_p),
            nn.Linear(in_features, num_classes)
        )
    return model

def load_species_model():
    """
    Loads model state and classification maps at startup.
    """
    global _model, _class_names, _species_to_group, _high_conf_threshold, _med_conf_threshold, _common_names
    
    weights_path = MODEL_WEIGHTS["species"]
    label_map_path = MODEL_WEIGHTS["label_map"]
    
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Trained species weights not found at: {weights_path}")
        
    print(f"Loading Species Classification model from {weights_path}...")
    checkpoint = torch.load(weights_path, map_location=DEVICE)
    
    # Extract metadata from final saved checkpoint (embedded in Notebook 03 cell 34)
    if isinstance(checkpoint, dict) and 'class_names' in checkpoint:
        _class_names = checkpoint['class_names']
        _species_to_group = checkpoint['species_to_group']
        _high_conf_threshold = checkpoint.get('high_conf_threshold', 0.70)
        _med_conf_threshold = checkpoint.get('med_conf_threshold', 0.40)
        num_classes = checkpoint['num_classes']
        state_dict = checkpoint['model_state_dict']
    else:
        # Fallback to load from separate species_label_map.json
        state_dict = checkpoint
        with open(label_map_path, 'r') as f:
            label_map = json.load(f)
        _class_names = label_map['classes']
        _species_to_group = label_map['species_to_group']
        num_classes = label_map['num_classes']

    # common_names always comes from the JSON file, independent of checkpoint path,
    # since the production checkpoint doesn't embed it and re-saving a working
    # checkpoint on demo day isn't worth the risk.
    with open(label_map_path, 'r') as f:
        label_map = json.load(f)
    _common_names = label_map.get('common_names', {})
        
    # Recreate the exact network architecture
    _model = build_model(
        model_name=MODEL_NAME,
        num_classes=num_classes,
        pretrained=False,
        freeze_through_block=-1,
        dropout_p=0.3
    )
    
    # Load parameters
    _model.load_state_dict(state_dict)
    _model.to(DEVICE)
    _model.eval()
    print("Species Classification model (EfficientNetV2-S) loaded successfully!")

    # Load calibration threshold directly from calibration.json at runtime
    calibration_path = MODEL_WEIGHTS.get("calibration")
    if calibration_path and os.path.exists(calibration_path):
        try:
            with open(calibration_path, 'r') as f:
                calibration_data = json.load(f)
            _high_conf_threshold = calibration_data.get("recommended_thresholds", {}).get("accept", 0.90)
            print(f"Loaded high_conf_threshold ({_high_conf_threshold}) from calibration.json at runtime.")
        except Exception as e:
            print(f"Warning: could not read calibration.json ({e}). Falling back to 0.90.")
            _high_conf_threshold = 0.90
    else:
        print("Warning: calibration.json path not found. Falling back to 0.90.")
        _high_conf_threshold = 0.90

# Initialize on import
load_species_model()

def predict_species(image_path: str) -> dict:
    """
    Full confidence-gated species prediction, preserving exact behavior of Notebook 03.
    """
    global _model, _class_names, _species_to_group, _high_conf_threshold, _med_conf_threshold, _common_names
    
    # 1. Load image and apply transforms exactly as in Notebook 03
    img = np.array(Image.open(image_path).convert('RGB'))
    img_tensor = eval_transform(image=img)['image'].unsqueeze(0).to(DEVICE)

    _model.eval()
    with torch.no_grad():
        outputs = _model(img_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        top_prob, top_idx = torch.max(probs, dim=0)

    top_prob = top_prob.item()
    species_pred = _class_names[top_idx.item()]
    group_pred   = _species_to_group.get(species_pred, 'unknown')

    # Format species name with common name if available, e.g., "Mango (Mangifera indica)"
    if species_pred in _common_names:
        formatted_scientific = species_pred.replace("_", " ")
        display_name = f"{_common_names[species_pred]} ({formatted_scientific})"
    else:
        display_name = species_pred

    # Top-5 list for backend display
    topk_probs, topk_idx = torch.topk(probs, k=min(5, len(probs)))
    top_predictions = []
    raw_top_predictions = []
    for idx, prob in zip(topk_idx, topk_probs):
        raw_name = _class_names[idx.item()]
        if raw_name in _common_names:
            formatted_scientific = raw_name.replace("_", " ")
            formatted_name = f"{_common_names[raw_name]} ({formatted_scientific})"
        else:
            formatted_name = raw_name
        top_predictions.append({
            "species": formatted_name,
            "confidence": round(prob.item() * 100, 2)  # percentage
        })
        raw_top_predictions.append({
            "species": raw_name,
            "confidence": round(prob.item() * 100, 2)
        })

    # Map decision levels based on thresholds
    if top_prob >= _high_conf_threshold:
        confidence_level = 'high'
        display_label = display_name
    elif top_prob >= _med_conf_threshold:
        confidence_level = 'medium'
        display_label = f'{group_pred} — uncertain species'
    else:
        confidence_level = 'low'
        display_label = 'Unknown — flagged for review'

    return {
        'species'         : species_pred,
        'species_group'   : group_pred,
        'confidence'      : round(top_prob * 100, 2),  # percentage
        'confidence_level': confidence_level,
        'display_label'   : display_label,
        'top_predictions' : top_predictions,
        'raw_top_predictions': raw_top_predictions,
    }
