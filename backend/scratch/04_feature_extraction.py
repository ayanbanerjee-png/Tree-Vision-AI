# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT      = r'C:\Users\AYAN\Flocard Tree AI'
COMBINED_ROOT      = os.path.join(PROJECT_ROOT, 'data', 'combined')
EMBEDDINGS_ROOT     = os.path.join(PROJECT_ROOT, 'data', 'embeddings')

SPLIT_PATH          = os.path.join(COMBINED_ROOT, 'labels_split.csv')
EMBEDDINGS_PATH      = os.path.join(EMBEDDINGS_ROOT, 'dinov2_small_embeddings.npz')
PROGRESS_LOG_PATH   = os.path.join(EMBEDDINGS_ROOT, 'dinov2_extraction_log.json')
PATHS_ARRAY_PATH = os.path.join(EMBEDDINGS_ROOT, 'dinov2_paths.npy')
EMB_ARRAY_PATH = os.path.join(EMBEDDINGS_ROOT, 'dinov2_embeddings.npy')

os.makedirs(EMBEDDINGS_ROOT, exist_ok=True)

print('Paths set successfully')

# ==========================================
# CELL 4
# ==========================================
import json
import time
import numpy as np
import pandas as pd
from PIL import Image

import torch
from torchvision import transforms
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

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

# Note: health / age / foliage are currently all 'uncertain' pending manual
# labeling — extraction here is independent of that and covers all single_tree
# images regardless of label status.
print(f"health label status  : {df_single['health'].value_counts().to_dict()}")

# ==========================================
# CELL 8
# ==========================================
# torch.hub download requires internet access on first run only; weights are
# cached locally afterward.
dinov2 = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')
dinov2.eval().to(device)

for p in dinov2.parameters():
    p.requires_grad = False

EMBED_DIM = dinov2.embed_dim
print(f'DINOv2-Small loaded — embedding dim : {EMBED_DIM}')

# ==========================================
# CELL 10
# ==========================================
IMG_SIZE = 224  # must be divisible by 14 (DINOv2 patch size); 224 keeps VRAM low

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

def load_image(path):
    img = Image.open(path).convert('RGB')
    return eval_transform(img)

print('Transform ready')

# ==========================================
# CELL 12
# ==========================================
BATCH_SIZE = 16
SAVE_EVERY = 200

PATHS_ARRAY_PATH = os.path.join(EMBEDDINGS_ROOT, 'dinov2_paths.npy')
EMB_ARRAY_PATH = os.path.join(EMBEDDINGS_ROOT, 'dinov2_embeddings.npy')

# Resume support
if os.path.exists(PATHS_ARRAY_PATH) and os.path.exists(EMB_ARRAY_PATH):
    saved_paths = list(np.load(PATHS_ARRAY_PATH, allow_pickle=True))
    saved_embeddings = list(np.load(EMB_ARRAY_PATH, allow_pickle=True))
    print(f'Resuming — {len(saved_paths)} embeddings already on disk.')
else:
    saved_paths = []
    saved_embeddings = []

saved_paths_set = set(saved_paths)
all_paths = df_single['use_path'].tolist()
paths_to_process = [p for p in all_paths if p not in saved_paths_set]
print(f'Remaining to extract : {len(paths_to_process)} / {len(all_paths)}')

failed_paths = []

def save_checkpoint():
    np.save(PATHS_ARRAY_PATH, np.array(saved_paths, dtype=object))
    np.save(EMB_ARRAY_PATH, np.array(saved_embeddings, dtype=np.float32))
    print(f'Checkpoint saved — {len(saved_paths)} embeddings on disk.')

images_since_checkpoint = 0

for i in tqdm(range(0, len(paths_to_process), BATCH_SIZE)):
    batch_paths = paths_to_process[i:i + BATCH_SIZE]
    batch_tensors, valid_paths = [], []

    for p in batch_paths:
        try:
            batch_tensors.append(load_image(p))
            valid_paths.append(p)
        except Exception as e:
            print(f'Skipping unreadable image: {p} ({e})')
            failed_paths.append(p)

    if not batch_tensors:
        continue

    batch = torch.stack(batch_tensors).to(device)
    with torch.no_grad():
        feats = dinov2(batch)
    feats = feats.cpu().numpy()

    for p, f in zip(valid_paths, feats):
        saved_paths.append(p)
        saved_embeddings.append(f)

    images_since_checkpoint += len(valid_paths)
    if images_since_checkpoint >= SAVE_EVERY:
        save_checkpoint()
        images_since_checkpoint = 0

save_checkpoint()
print(f'\nDone. Total embeddings on disk : {len(saved_paths)}')
if failed_paths:
    print(f'Failed to read {len(failed_paths)} images.')

# ==========================================
# CELL 14
# ==========================================
loaded_paths = np.load(PATHS_ARRAY_PATH, allow_pickle=True)
loaded_embeddings = np.load(EMB_ARRAY_PATH, allow_pickle=True)

print(f'Total embeddings   : {len(loaded_paths)}')
print(f'Embedding shape    : {loaded_embeddings.shape}')

missing = set(df_single['use_path']) - set(loaded_paths)
print(f'Missing embeddings : {len(missing)}')

# ==========================================
# CELL 16
# ==========================================
print('=' * 60)
print('NOTEBOOK 04 COMPLETE — DINOv2-Small FEATURE EXTRACTION')
print('=' * 60)
print(f'Paths array saved to      : {PATHS_ARRAY_PATH}')
print(f'Embeddings array saved to : {EMB_ARRAY_PATH}')
print()
print(f'Total images embedded : {len(loaded_paths)}')
print(f'Embedding dimension   : {loaded_embeddings.shape[1]}')
print(f'Missing / failed      : {len(missing)}')
print()
print('Note: health / age / foliage labels are currently all \'uncertain\' —')
print('manual labeling pass is a separate, still-pending task. These embeddings')
print('are ready to use once labels exist.')
print()
print('Next step : Manual labeling pass (health / age / foliage), then')
print('            Notebook 05+ — Random Forest / SVM / KNN on these embeddings')
print('=' * 60)

# ==========================================
# CELL 17
# ==========================================


