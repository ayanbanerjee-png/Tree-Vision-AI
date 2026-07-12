# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT      = r'C:\Users\AYAN\Flocard Tree AI'
MODELS_ROOT        = os.path.join(PROJECT_ROOT, 'models')
EMBEDDINGS_ROOT     = os.path.join(PROJECT_ROOT, 'data', 'embeddings')

SPECIES_MODEL_PATH  = os.path.join(MODELS_ROOT, 'efficientnet_species_lr_dropout_nofreeze_cleaned.pth')
LABEL_MAP_PATH      = os.path.join(MODELS_ROOT, 'species_label_map.json')
RF_HEALTH_PATH       = os.path.join(MODELS_ROOT, 'rf_health.pkl')
SVM_FOLIAGE_PATH     = os.path.join(MODELS_ROOT, 'svm_foliage.pkl')
KNN_AGE_PATH         = os.path.join(MODELS_ROOT, 'knn_age.pkl')

print('Paths set successfully')
print('NOTE: verify SPECIES_MODEL_PATH matches your actual backed-up Run A checkpoint filename.')

# ==========================================
# CELL 4
# ==========================================
import json
import numpy as np
import cv2
import joblib
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import timm
import warnings
warnings.filterwarnings('ignore')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')

# ==========================================
# CELL 6
# ==========================================
BLUR_THRESHOLD     = 100.0
DARK_THRESHOLD     = 40.0
BRIGHT_THRESHOLD   = 220.0
CONTRAST_THRESHOLD = 30.0

def compute_blur_score(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def compute_brightness(gray):
    return float(np.mean(gray))

def compute_contrast(gray):
    return float(np.std(gray))

def assess_quality(image_path, input_type='single_tree'):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {'image_quality': 'uncertain', 'blur_score': 0.0,
                     'brightness': 0.0, 'contrast': 0.0, 'confidence': 'low'}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = compute_blur_score(gray)
        brightness = compute_brightness(gray)
        contrast = compute_contrast(gray)

        if input_type == 'tree_crop':
            return {'image_quality': 'partial_view', 'blur_score': blur_score,
                     'brightness': brightness, 'contrast': contrast, 'confidence': 'high'}

        if brightness < DARK_THRESHOLD:
            confidence = 'high' if brightness < 25 else 'medium'
            return {'image_quality': 'low_light', 'blur_score': blur_score,
                     'brightness': brightness, 'contrast': contrast, 'confidence': confidence}

        if brightness > BRIGHT_THRESHOLD:
            confidence = 'high' if brightness > 235 else 'medium'
            return {'image_quality': 'overexposed', 'blur_score': blur_score,
                     'brightness': brightness, 'contrast': contrast, 'confidence': confidence}

        if blur_score < BLUR_THRESHOLD:
            confidence = 'high' if blur_score < 50 else 'medium'
            return {'image_quality': 'blurry', 'blur_score': blur_score,
                     'brightness': brightness, 'contrast': contrast, 'confidence': confidence}

        if contrast < CONTRAST_THRESHOLD:
            return {'image_quality': 'uncertain', 'blur_score': blur_score,
                     'brightness': brightness, 'contrast': contrast, 'confidence': 'low'}

        confidence = 'high' if blur_score > 200 else 'medium'
        return {'image_quality': 'clear', 'blur_score': blur_score,
                 'brightness': brightness, 'contrast': contrast, 'confidence': confidence}

    except Exception:
        return {'image_quality': 'uncertain', 'blur_score': 0.0,
                 'brightness': 0.0, 'contrast': 0.0, 'confidence': 'low'}

print('Quality assessment function loaded (matches notebook 02 exactly)')

# ==========================================
# CELL 8
# ==========================================
checkpoint = torch.load(SPECIES_MODEL_PATH, map_location=device)

class_names = checkpoint['class_names']
species_to_group = checkpoint['species_to_group']
NUM_CLASSES = checkpoint['num_classes']
idx_to_species = dict(enumerate(class_names))

IMG_SIZE = checkpoint.get('img_size', 224)
IMAGENET_MEAN = checkpoint.get('imagenet_mean', [0.485, 0.456, 0.406])
IMAGENET_STD = checkpoint.get('imagenet_std', [0.229, 0.224, 0.225])

HIGH_CONF_THRESHOLD = checkpoint.get('high_conf_threshold', 0.70)
MED_CONF_THRESHOLD = checkpoint.get('med_conf_threshold', 0.40)

print(f'Loaded checkpoint — {NUM_CLASSES} species classes')
print(f'Val acc: {checkpoint.get("val_acc")}  |  Test acc: {checkpoint.get("test_acc")}')

# Build base model, then replace the classifier head to match the Dropout+Linear
# structure used in training (Run A: dropout 0.3)
species_model = timm.create_model('tf_efficientnetv2_s.in1k', pretrained=False, num_classes=NUM_CLASSES)
in_features = species_model.classifier.in_features
species_model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(in_features, NUM_CLASSES)
)

species_model.load_state_dict(checkpoint['model_state_dict'])
species_model.eval().to(device)

species_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

print('Species classifier loaded — architecture matches training config')

# ==========================================
# CELL 10
# ==========================================
dinov2 = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')
dinov2.eval().to(device)
for p in dinov2.parameters():
    p.requires_grad = False

dinov2_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

print('DINOv2-Small loaded')

# ==========================================
# CELL 12
# ==========================================
rf_health = joblib.load(RF_HEALTH_PATH)
svm_foliage = joblib.load(SVM_FOLIAGE_PATH)
knn_age = joblib.load(KNN_AGE_PATH)

print('Auxiliary classifiers loaded: Random Forest (health), SVM (foliage), KNN (age)')

# ==========================================
# CELL 14
# ==========================================
AUX_CONFIDENCE_THRESHOLD = 0.5

def predict_tree(image_path, input_type='single_tree'):
    result = {'image_path': image_path}
    # ── 1. Image quality ──
    quality = assess_quality(image_path, input_type=input_type)
    result['quality'] = quality
    # ── 2. Species (confidence-gated) ──
    img = Image.open(image_path).convert('RGB')
    species_input = species_transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = species_model(species_input)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    top_idx = int(np.argmax(probs))
    top_conf = float(probs[top_idx])
    top_species = idx_to_species[top_idx]
    top_group = species_to_group[top_species]

    if top_conf >= HIGH_CONF_THRESHOLD:
        result['species'] = {'label': top_species, 'group': top_group,
                              'confidence': top_conf, 'tier': 'exact_species'}
    elif top_conf >= MED_CONF_THRESHOLD:
        result['species'] = {'label': top_group, 'confidence': top_conf, 'tier': 'group_only',
                              'note': f'Species uncertain (best guess was {top_species}) -- showing group-level result only.'}
    else:
        result['species'] = {'label': 'unknown', 'confidence': top_conf, 'tier': 'unknown',
                              'note': 'Confidence too low for any species suggestion -- manual review required.'}
    # ── 3. DINOv2 embedding (shared input for health/foliage/age) ──
    emb_input = dinov2_transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = dinov2(emb_input).cpu().numpy()
    # ── 4. Health / Foliage / Age ──
    for name, model in [('health', rf_health), ('foliage', svm_foliage), ('age', knn_age)]:
        pred = model.predict(embedding)[0]
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(embedding)[0]
            conf = float(np.max(proba))
        else:
            conf = None
        entry = {'label': pred, 'confidence': conf}
        if conf is not None and conf < AUX_CONFIDENCE_THRESHOLD:
            entry['needs_review'] = True
        result[name] = entry
    # ── 5. Overall review flag ──
    needs_review = (
        quality['image_quality'] in ('blurry', 'low_light', 'overexposed', 'uncertain')
        or result['species']['tier'] != 'exact_species'
        or any(result[c].get('needs_review') for c in ['health', 'foliage', 'age'])
    )
    result['needs_review'] = needs_review
    return result

print('predict_tree() ready.')

# ==========================================
# CELL 15
# ==========================================
import os
sample_folder = r'C:\Users\AYAN\Flocard Tree AI\data\combined\standardised\broadleaf\Terminalia_arjuna'
print(os.listdir(sample_folder)[:5])

# ==========================================
# CELL 17
# ==========================================
import json as _json

SAMPLE_IMAGES = [
    r'C:\Users\AYAN\Flocard Tree AI\data\combined\standardised\broadleaf\Terminalia_arjuna\1.jpg',
]

for path in SAMPLE_IMAGES:
    result = predict_tree(path)
    print('=' * 60)
    print(path)
    print('=' * 60)
    print(_json.dumps(result, indent=2, default=str))
    print()

if not SAMPLE_IMAGES:
    print('Add real image paths to SAMPLE_IMAGES above to test end to end.')

# ==========================================
# CELL 19
# ==========================================
print('=' * 60)
print('NOTEBOOK 06 COMPLETE — END-TO-END INFERENCE PIPELINE')
print('=' * 60)
print('predict_tree(image_path) combines:')
print('  1. Rule-based image quality check (notebook 02 thresholds)')
print('  2. Species classification, confidence-gated (notebook 03, Run A checkpoint)')
print('  3. DINOv2-Small embedding extraction (notebook 04)')
print('  4. Health (RF) / Foliage (SVM) / Age (KNN) prediction (notebook 05)')
print()
print('Every output field includes a confidence value; low-confidence fields are')
print('flagged needs_review rather than presented as certain, per the project\'s')
print('human-in-the-loop design principle.')
print()
print('Known limitations carried forward -- see docs/failure_cases.md:')
print('  - Health: reliable for Healthy, weak for Stressed/Damaged (too few examples)')
print('  - Foliage: reliable for Full Canopy/Evergreen, cannot predict Partial/Leafless')
print('  - Age: real but modest signal (62% honest accuracy), coarse proxy only')
print()
print('Next step : Notebook 07 -- YOLOv8 cluster/input-type detection')
print('=' * 60)

# ==========================================
# CELL 20
# ==========================================


