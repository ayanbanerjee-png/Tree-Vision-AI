# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT  = r'C:\Users\AYAN\Flocard Tree AI'
COMBINED_ROOT = os.path.join(PROJECT_ROOT, 'data', 'combined')
MODELS_ROOT   = os.path.join(PROJECT_ROOT, 'models')

SPLIT_PATH      = os.path.join(COMBINED_ROOT, 'labels_split.csv')
MODEL_SAVE_PATH = os.path.join(MODELS_ROOT, 'efficientnet_species.pth')
LABEL_MAP_PATH  = os.path.join(MODELS_ROOT, 'species_label_map.json')

os.makedirs(MODELS_ROOT, exist_ok=True)

print('Paths set successfully')

# ==========================================
# CELL 4
# ==========================================
import os
import json
import time
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import timm

import albumentations as A
from albumentations.pytorch import ToTensorV2

from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, top_k_accuracy_score)
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.figsize'] = (12, 6)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device : {device}')
if torch.cuda.is_available():
    print(f'GPU          : {torch.cuda.get_device_name(0)}')

# ==========================================
# CELL 6
# ==========================================
df = pd.read_csv(SPLIT_PATH)
print(f'Total records in labels_split.csv : {len(df)}')

df_single = df[df['input_type'] == 'single_tree'].copy()
df_single['use_path'] = df_single.apply(
    lambda r: r['std_path'] if isinstance(r.get('std_path'), str) and os.path.exists(r['std_path'])
              else r['image_path'],
    axis=1
)
print(f'single_tree records : {len(df_single)}')

# ==========================================
# CELL 8
# ==========================================
label_encoder = LabelEncoder()
label_encoder.fit(df_single['species_exact'])
num_classes = len(label_encoder.classes_)
print(f'Number of species classes : {num_classes}')

species_to_group = (
    df_single[['species_exact', 'species_group']]
    .drop_duplicates()
    .set_index('species_exact')['species_group']
    .to_dict()
)

label_map = {
    'classes'          : label_encoder.classes_.tolist(),
    'species_to_group' : species_to_group,
    'num_classes'      : num_classes,
}
with open(LABEL_MAP_PATH, 'w') as f:
    json.dump(label_map, f, indent=2)
print('Label map saved')

# ==========================================
# CELL 10
# ==========================================
IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

train_transform = A.Compose([
    A.RandomResizedCrop(size=(IMG_SIZE, IMG_SIZE), scale=(0.7, 1.0), p=1.0),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
    A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=15, p=0.4),
    A.Rotate(limit=20, p=0.4),
    A.GaussianBlur(blur_limit=(3, 5), p=0.15),
    A.CoarseDropout(num_holes_range=(1, 4), hole_height_range=(0.05, 0.15),
                     hole_width_range=(0.05, 0.15), p=0.3),
    A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ToTensorV2(),
])

eval_transform = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ToTensorV2(),
])

class TreeSpeciesDataset(Dataset):
    def __init__(self, dataframe, label_encoder, transform):
        self.df = dataframe.reset_index(drop=True)
        self.encoder = label_encoder
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = np.array(Image.open(row['use_path']).convert('RGB'))
        img = self.transform(image=img)['image']
        label = self.encoder.transform([row['species_exact']])[0]
        return img, label

print('Dataset class and transforms defined')

# ==========================================
# CELL 11
# ==========================================
BATCH_SIZE = 32

train_df = df_single[df_single['split'] == 'train']
val_df   = df_single[df_single['split'] == 'val']
test_df  = df_single[df_single['split'] == 'test']

train_dataset = TreeSpeciesDataset(train_df, label_encoder, train_transform)
val_dataset   = TreeSpeciesDataset(val_df,   label_encoder, eval_transform)
test_dataset  = TreeSpeciesDataset(test_df,  label_encoder, eval_transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                           num_workers=0, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False,
                           num_workers=0, pin_memory=True)
test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False,
                           num_workers=0, pin_memory=True)

print(f'Train batches : {len(train_loader)} ({len(train_dataset)} images)')
print(f'Val batches   : {len(val_loader)} ({len(val_dataset)} images)')
print(f'Test batches  : {len(test_loader)} ({len(test_dataset)} images)')

# ==========================================
# CELL 13
# ==========================================
MODEL_NAME = 'tf_efficientnetv2_s.in1k'

def build_model(model_name, num_classes, pretrained=True, freeze_through_block=-1, dropout_p=0.3):
    """
    freeze_through_block: freezes conv_stem, bn1, and blocks[0..freeze_through_block] inclusive.
    Set to -1 to leave the whole backbone trainable.
    dropout_p: dropout probability inserted before the final classifier layer. Set to 0.0 to disable.
    """
    try:
        model = timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)
        print(f'Loaded {model_name} with pretrained ImageNet weights')
    except Exception as e:
        model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        print(f'Pretrained weights unavailable — using random init: {type(e).__name__}: {e}')

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

# ---- LR + dropout ONLY, freezing OFF ----
model = build_model(MODEL_NAME, num_classes, pretrained=True, freeze_through_block=-1, dropout_p=0.3)

model = model.to(device)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
frozen_params = total_params - trainable_params

print(f'Total parameters     : {total_params:,}')
print(f'Frozen parameters    : {frozen_params:,} ({frozen_params/total_params*100:.1f}%)')
print(f'Trainable parameters : {trainable_params:,} ({trainable_params/total_params*100:.1f}%)')

# ==========================================
# CELL 15
# ==========================================
EPOCHS        = 20
LEARNING_RATE = 1e-4
WEIGHT_DECAY  = 1e-4

criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()),
                         lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
scaler = torch.amp.GradScaler('cuda') if torch.cuda.is_available() else None

print(f'Epochs: {EPOCHS} | LR: {LEARNING_RATE} | Weight decay: {WEIGHT_DECAY}')

# ==========================================
# CELL 17
# ==========================================
import copy

PATIENCE = 5
best_val_acc = 0.0
best_model_state = None
best_epoch = 0
epochs_no_improve = 0

history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

print('Starting training...')
print('='*60)

for epoch in range(EPOCHS):
    start_time = time.time()

    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        train_correct += (preds == labels).sum().item()
        train_total += labels.size(0)

    train_loss = train_loss / train_total
    train_acc  = train_correct / train_total

    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            val_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            val_correct += (preds == labels).sum().item()
            val_total += labels.size(0)

    val_loss = val_loss / val_total
    val_acc  = val_correct / val_total

    scheduler.step()

    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)

    elapsed = time.time() - start_time
    marker = ''

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_epoch = epoch + 1
        best_model_state = copy.deepcopy(model.state_dict())
        epochs_no_improve = 0
        marker = '<- best so far, saved'
        torch.save({
            'model_state_dict': best_model_state,
            'epoch'           : best_epoch,
            'val_acc'         : best_val_acc,
        }, MODEL_SAVE_PATH)
    else:
        epochs_no_improve += 1

    print(f'Epoch {epoch+1:2d}/{EPOCHS} | train_loss: {train_loss:.4f} train_acc: {train_acc:.4f} '
          f'| val_loss: {val_loss:.4f} val_acc: {val_acc:.4f} | {elapsed:.1f}s {marker}')

    if epochs_no_improve >= PATIENCE:
        print(f'\nEarly stopping triggered — no improvement for {PATIENCE} epochs.')
        break

print('='*60)
print(f'Training complete')
print(f'Best validation accuracy : {best_val_acc:.4f} (epoch {best_epoch})')
print(f'Best model saved to      : {MODEL_SAVE_PATH}')

model.load_state_dict(best_model_state)

# ==========================================
# CELL 19
# ==========================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

epochs_range = range(1, len(history['train_loss']) + 1)

axes[0].plot(epochs_range, history['train_loss'], label='Train Loss', color='steelblue')
axes[0].plot(epochs_range, history['val_loss'],   label='Val Loss',   color='coral')
axes[0].set_title('Loss over Epochs')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].legend()

axes[1].plot(epochs_range, history['train_acc'], label='Train Accuracy', color='steelblue')
axes[1].plot(epochs_range, history['val_acc'],   label='Val Accuracy',   color='coral')
axes[1].axhline(best_val_acc, color='green', linestyle='--', alpha=0.5,
                label=f'Best val acc ({best_val_acc:.3f})')
axes[1].set_title('Accuracy over Epochs')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].legend()

plt.tight_layout()
plt.show()

# ==========================================
# CELL 21
# ==========================================
# Load best checkpoint
checkpoint = torch.load(MODEL_SAVE_PATH, map_location=device, weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

print(f'Loaded best model from epoch {checkpoint["epoch"]}')
print(f'Validation accuracy at save time : {checkpoint["val_acc"]:.4f}')

# Run inference on test set
all_preds  = []
all_labels = []
all_probs  = []

with torch.no_grad():
    for imgs, labels in tqdm(test_loader, desc='Testing'):
        imgs = imgs.to(device)
        outputs = model(imgs)
        probs = torch.softmax(outputs, dim=1)
        _, preds = torch.max(outputs, 1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.numpy())
        all_probs.extend(probs.cpu().numpy())

all_preds  = np.array(all_preds)
all_labels = np.array(all_labels)
all_probs  = np.array(all_probs)

test_acc  = accuracy_score(all_labels, all_preds)
top3_acc  = top_k_accuracy_score(all_labels, all_probs, k=3, labels=range(num_classes))

print('='*60)
print('TEST SET RESULTS')
print('='*60)
print(f'Test accuracy (top-1) : {test_acc:.4f}')
print(f'Test accuracy (top-3) : {top3_acc:.4f}')
print(f'Test set size         : {len(all_labels)} images')
print('='*60)

# ==========================================
# CELL 23
# ==========================================
species_names = label_encoder.classes_

report = classification_report(
    all_labels, all_preds,
    target_names=species_names,
    zero_division=0
)
print('='*60)
print('PER-SPECIES CLASSIFICATION REPORT')
print('='*60)
print(report)

# ==========================================
# CELL 25
# ==========================================
cm = confusion_matrix(all_labels, all_preds)

fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=species_names, yticklabels=species_names,
            cbar_kws={'label': 'Count'}, ax=ax)
ax.set_xlabel('Predicted Species')
ax.set_ylabel('True Species')
ax.set_title('Confusion Matrix — Species Classification (Test Set)')
plt.xticks(rotation=90, fontsize=8)
plt.yticks(rotation=0, fontsize=8)
plt.tight_layout()
plt.show()

# Identify most confused species pairs
print('Most confused species pairs (off-diagonal, count >= 2):')
confused_pairs = []
for i in range(len(cm)):
    for j in range(len(cm)):
        if i != j and cm[i][j] >= 2:
            confused_pairs.append((species_names[i], species_names[j], cm[i][j]))

confused_pairs.sort(key=lambda x: -x[2])
for true_sp, pred_sp, count in confused_pairs[:10]:
    print(f'  True: {true_sp:<25} -> Predicted: {pred_sp:<25} ({count} times)')

# ==========================================
# CELL 26
# ==========================================
import os
import json

# ── Folder for diagnostic outputs ────────────────────────────
DIAGNOSTICS_DIR = os.path.join(MODELS_ROOT, 'diagnostics', 'run_lr_dropout_nofreeze_cleaned')
os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)

# ── 1. Save training history as CSV ──────────────────────────
history_df = pd.DataFrame({
    'epoch'      : list(range(1, len(history['train_loss']) + 1)),
    'train_loss' : history['train_loss'],
    'train_acc'  : history['train_acc'],
    'val_loss'   : history['val_loss'],
    'val_acc'    : history['val_acc'],
})
history_csv_path = os.path.join(DIAGNOSTICS_DIR, 'training_history.csv')
history_df.to_csv(history_csv_path, index=False)
print(f'Training history saved : {history_csv_path}')

# ── 2. Save loss/accuracy curves as PNG ──────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

epochs_range = range(1, len(history['train_loss']) + 1)

axes[0].plot(epochs_range, history['train_loss'], label='Train Loss', color='steelblue')
axes[0].plot(epochs_range, history['val_loss'],   label='Val Loss',   color='coral')
axes[0].set_title('Loss over Epochs')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(epochs_range, history['train_acc'], label='Train Acc', color='steelblue')
axes[1].plot(epochs_range, history['val_acc'],   label='Val Acc',   color='coral')
axes[1].set_title('Accuracy over Epochs')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
curves_path = os.path.join(DIAGNOSTICS_DIR, 'loss_accuracy_curves.png')
plt.savefig(curves_path, dpi=150, bbox_inches='tight')
plt.show()
print(f'Loss/accuracy curves saved : {curves_path}')

# ── 3. Save confusion matrix as PNG ──────────────────────────
cm = confusion_matrix(all_labels, all_preds)

fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=species_names, yticklabels=species_names,
            cbar_kws={'label': 'Count'}, ax=ax)
ax.set_xlabel('Predicted Species')
ax.set_ylabel('True Species')
ax.set_title('Confusion Matrix — Species Classification (Test Set)')
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.tight_layout()

cm_png_path = os.path.join(DIAGNOSTICS_DIR, 'confusion_matrix.png')
plt.savefig(cm_png_path, dpi=150, bbox_inches='tight')
plt.show()
print(f'Confusion matrix image saved : {cm_png_path}')

# ── 4. Save confusion matrix as CSV (raw counts) ─────────────
cm_df = pd.DataFrame(cm, index=species_names, columns=species_names)
cm_csv_path = os.path.join(DIAGNOSTICS_DIR, 'confusion_matrix.csv')
cm_df.to_csv(cm_csv_path)
print(f'Confusion matrix CSV saved   : {cm_csv_path}')

# ── 5. Save classification report as CSV ─────────────────────
report_dict = classification_report(
    all_labels, all_preds,
    target_names=species_names,
    zero_division=0,
    output_dict=True
)
report_df = pd.DataFrame(report_dict).transpose()
report_csv_path = os.path.join(DIAGNOSTICS_DIR, 'classification_report.csv')
report_df.to_csv(report_csv_path)
print(f'Classification report CSV saved : {report_csv_path}')

# ── 6. Save a small run summary JSON ──────────────────────────
run_summary = {
    'best_val_acc'   : float(max(history['val_acc'])),
    'best_val_epoch' : int(np.argmax(history['val_acc']) + 1),
    'final_train_acc': float(history['train_acc'][-1]),
    'final_val_acc'  : float(history['val_acc'][-1]),
    'test_acc_top1'  : float(test_acc),
    'test_acc_top3'  : float(top3_acc),
    'num_classes'    : int(num_classes),
    'pretrained_used': model_name if 'model_name' in dir() else 'unknown',
}
summary_path = os.path.join(DIAGNOSTICS_DIR, 'run_summary.json')
with open(summary_path, 'w') as f:
    json.dump(run_summary, f, indent=2)
print(f'Run summary saved            : {summary_path}')

print(f'\nAll diagnostics saved to: {DIAGNOSTICS_DIR}')

# ==========================================
# CELL 28
# ==========================================
# Confidence thresholds — matches the design decision in the markdown above
HIGH_CONF_THRESHOLD = 0.70   # Show exact species + group
MED_CONF_THRESHOLD  = 0.40   # Show group only, flag uncertain species
# Below MED_CONF_THRESHOLD -> unknown, flag for manual review


def predict_species(image_path, model, label_encoder, species_to_group,
                     transform, device):
    """
    Full confidence-gated species prediction.
    Returns a dict matching the report's label schema:
    species (exact or group fallback), species_group, confidence, confidence_level.
    """
    img = np.array(Image.open(image_path).convert('RGB'))
    img_tensor = transform(image=img)['image'].unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        outputs = model(img_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        top_prob, top_idx = torch.max(probs, dim=0)

    top_prob = top_prob.item()
    species_pred = label_encoder.inverse_transform([top_idx.item()])[0]
    group_pred   = species_to_group.get(species_pred, 'unknown')

    # Top-3 for transparency / review context
    top3_probs, top3_idx = torch.topk(probs, k=min(3, len(probs)))
    top3 = [
        (label_encoder.inverse_transform([idx.item()])[0], prob.item())
        for idx, prob in zip(top3_idx, top3_probs)
    ]

    if top_prob >= HIGH_CONF_THRESHOLD:
        return {
            'species'         : species_pred,
            'species_group'   : group_pred,
            'confidence'      : round(top_prob, 4),
            'confidence_level': 'high',
            'display_label'   : species_pred,
            'top3'            : top3,
        }
    elif top_prob >= MED_CONF_THRESHOLD:
        return {
            'species'         : species_pred,
            'species_group'   : group_pred,
            'confidence'      : round(top_prob, 4),
            'confidence_level': 'medium',
            'display_label'   : f'{group_pred} (uncertain species)',
            'top3'            : top3,
        }
    else:
        return {
            'species'         : 'unknown',
            'species_group'   : 'unknown',
            'confidence'      : round(top_prob, 4),
            'confidence_level': 'low',
            'display_label'   : 'unknown — flag for manual review',
            'top3'            : top3,
        }


print('Confidence-gated prediction function ready')
print(f'High confidence threshold   : {HIGH_CONF_THRESHOLD}')
print(f'Medium confidence threshold : {MED_CONF_THRESHOLD}')

# ==========================================
# CELL 30
# ==========================================
sample_test = test_df.sample(min(8, len(test_df)), random_state=42)

fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

for i, (_, row) in enumerate(sample_test.iterrows()):
    result = predict_species(row['use_path'], model, label_encoder,
                              species_to_group, eval_transform, device)

    img = Image.open(row['use_path']).convert('RGB')
    axes[i].imshow(img)

    correct = '✓' if result['species'] == row['species_exact'] else '✗'
    title = (f"True: {row['species_exact']}\n"
             f"Pred: {result['display_label']}\n"
             f"Conf: {result['confidence']:.2f} ({result['confidence_level']}) {correct}")
    axes[i].set_title(title, fontsize=8)
    axes[i].axis('off')

plt.tight_layout()
plt.show()

# ==========================================
# CELL 32
# ==========================================
df_crop = df[df['input_type'] == 'tree_crop'].copy()

if len(df_crop) > 0 and 'species_exact' in df_crop.columns:
    # Tree crop images don't carry a reliable species_exact label by design
    # (notebook 01 sets them to 'unknown') — so this is a qualitative spot check,
    # not a quantitative accuracy number
    print('='*60)
    print('TREE CROP ROBUSTNESS — QUALITATIVE SPOT CHECK')
    print('='*60)
    print('Tree crop images have no ground-truth species label (set to "unknown"')
    print('in notebook 01), since crops were synthetically generated without')
    print('tracking their source species. This section shows predictions only —')
    print('not accuracy — to visually sanity-check behaviour on partial views.\n')

    sample_crop = df_crop.sample(min(8, len(df_crop)), random_state=42)
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()

    conf_levels = []
    for i, (_, row) in enumerate(sample_crop.iterrows()):
        result = predict_species(row['image_path'], model, label_encoder,
                                  species_to_group, eval_transform, device)
        conf_levels.append(result['confidence_level'])

        img = Image.open(row['image_path']).convert('RGB')
        axes[i].imshow(img)
        axes[i].set_title(
            f"Pred: {result['display_label']}\nConf: {result['confidence']:.2f} ({result['confidence_level']})",
            fontsize=8
        )
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()

    print(f'\nConfidence level distribution on this sample: {pd.Series(conf_levels).value_counts().to_dict()}')
    print('\nExpectation: tree crops should show LOWER confidence on average than')
    print('full single-tree test images — confirming the model correctly expresses')
    print('more uncertainty on partial views rather than confidently guessing wrong.')
else:
    print('No tree_crop images found — skipping robustness check')

# ==========================================
# CELL 34
# ==========================================
# Re-save the checkpoint with label encoder classes embedded for easy reuse
final_checkpoint = {
    'model_state_dict' : model.state_dict(),
    'num_classes'       : num_classes,
    'class_names'       : label_encoder.classes_.tolist(),
    'species_to_group'  : species_to_group,
    'val_acc'           : best_val_acc,
    'test_acc'          : test_acc,
    'test_top3_acc'     : top3_acc,
    'high_conf_threshold': HIGH_CONF_THRESHOLD,
    'med_conf_threshold' : MED_CONF_THRESHOLD,
    'img_size'          : IMG_SIZE,
    'imagenet_mean'     : IMAGENET_MEAN,
    'imagenet_std'      : IMAGENET_STD,
}
torch.save(final_checkpoint, MODEL_SAVE_PATH)

print('='*60)
print('NOTEBOOK 03 COMPLETE — SPECIES CLASSIFICATION')
print('='*60)
print(f'Model saved to        : {MODEL_SAVE_PATH}')
print(f'Label map saved to    : {LABEL_MAP_PATH}')
print()
print(f'Validation accuracy   : {best_val_acc:.4f}')
print(f'Test accuracy (top-1) : {test_acc:.4f}')
print(f'Test accuracy (top-3) : {top3_acc:.4f}')
print()
print('Confidence-gated output design:')
print(f'  >= {HIGH_CONF_THRESHOLD}      -> exact species + group shown')
print(f'  {MED_CONF_THRESHOLD}-{HIGH_CONF_THRESHOLD}    -> species group only, species flagged uncertain')
print(f'  < {MED_CONF_THRESHOLD}      -> unknown, flagged for manual review')
print()
print('Next step : Notebook 04 — Feature Extraction with DINOv2-Small')
print('='*60)

# ==========================================
# CELL 35
# ==========================================
import shutil
shutil.copy(
    r'C:\Users\AYAN\Flocard Tree AI\models\efficientnet_species.pth',
    r'C:\Users\AYAN\Flocard Tree AI\models\efficientnet_species_lr_dropout_nofreeze_cleaned.pth'
)
print('Backed up: LR+dropout, no freezing, cleaned data (val 0.6438, test 0.6055)')

# ==========================================
# CELL 36
# ==========================================
import pandas as pd
df = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'combined', 'labels.csv'))
print(df.columns.tolist())
print(df.head())

# ==========================================
# CELL 37
# ==========================================
print(df['health'].value_counts())
print(df['age'].value_counts())
print(df['foliage'].value_counts())

# ==========================================
# CELL 38
# ==========================================
import os
for f in os.listdir(r'C:\Users\AYAN\Flocard Tree AI\models'):
    print(f)

# ==========================================
# CELL 39
# ==========================================


