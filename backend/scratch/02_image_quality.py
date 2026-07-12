# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT  = r'C:\Users\AYAN\Flocard Tree AI'
COMBINED_ROOT = os.path.join(PROJECT_ROOT, 'data', 'combined')
MODELS_ROOT   = os.path.join(PROJECT_ROOT, 'models')

LABELS_PATH   = os.path.join(COMBINED_ROOT, 'labels.csv')
SPLIT_PATH    = os.path.join(COMBINED_ROOT, 'labels_split.csv')

print('Paths set successfully')
print(f'Labels CSV : {LABELS_PATH}')

# ==========================================
# CELL 4
# ==========================================
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.figsize'] = (14, 5)
plt.rcParams['font.size'] = 11

print('Libraries imported')

# ==========================================
# CELL 6
# ==========================================
# ── Thresholds ────────────────────────────────────────────
BLUR_THRESHOLD       = 100.0   # Laplacian variance below this = blurry
DARK_THRESHOLD       = 40.0    # Mean brightness below this = low-light
BRIGHT_THRESHOLD     = 220.0   # Mean brightness above this = overexposed
CONTRAST_THRESHOLD   = 30.0    # Std deviation below this = low contrast


def compute_blur_score(gray):
    """
    Laplacian variance — higher = sharper image.
    Low value means the image is blurry.
    """
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def compute_brightness(gray):
    """
    Mean pixel brightness — 0 (black) to 255 (white).
    """
    return float(np.mean(gray))


def compute_contrast(gray):
    """
    Standard deviation of pixel values.
    Low = low contrast (washed out or dark flat image).
    """
    return float(np.std(gray))


def assess_quality(image_path, input_type='single_tree'):
    """
    Assess image quality and return label + metrics.

    Returns dict with:
        image_quality : label string
        blur_score    : Laplacian variance
        brightness    : mean pixel value
        contrast      : std of pixel values
        confidence    : high / medium / low
    """
    try:
        # Load image
        img  = cv2.imread(image_path)
        if img is None:
            return {
                'image_quality': 'uncertain',
                'blur_score'   : 0.0,
                'brightness'   : 0.0,
                'contrast'     : 0.0,
                'confidence'   : 'low'
            }

        gray       = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = compute_blur_score(gray)
        brightness = compute_brightness(gray)
        contrast   = compute_contrast(gray)

        # Tree crop — always partial view
        if input_type == 'tree_crop':
            return {
                'image_quality': 'partial_view',
                'blur_score'   : blur_score,
                'brightness'   : brightness,
                'contrast'     : contrast,
                'confidence'   : 'high'
            }

        # Low-light check
        if brightness < DARK_THRESHOLD:
            confidence = 'high' if brightness < 25 else 'medium'
            return {
                'image_quality': 'low_light',
                'blur_score'   : blur_score,
                'brightness'   : brightness,
                'contrast'     : contrast,
                'confidence'   : confidence
            }

        # Overexposed check
        if brightness > BRIGHT_THRESHOLD:
            confidence = 'high' if brightness > 235 else 'medium'
            return {
                'image_quality': 'overexposed',
                'blur_score'   : blur_score,
                'brightness'   : brightness,
                'contrast'     : contrast,
                'confidence'   : confidence
            }

        # Blurry check
        if blur_score < BLUR_THRESHOLD:
            confidence = 'high' if blur_score < 50 else 'medium'
            return {
                'image_quality': 'blurry',
                'blur_score'   : blur_score,
                'brightness'   : brightness,
                'contrast'     : contrast,
                'confidence'   : confidence
            }

        # Low contrast check
        if contrast < CONTRAST_THRESHOLD:
            return {
                'image_quality': 'uncertain',
                'blur_score'   : blur_score,
                'brightness'   : brightness,
                'contrast'     : contrast,
                'confidence'   : 'low'
            }

        # Clear image
        confidence = 'high' if blur_score > 200 else 'medium'
        return {
            'image_quality': 'clear',
            'blur_score'   : blur_score,
            'brightness'   : brightness,
            'contrast'     : contrast,
            'confidence'   : confidence
        }

    except Exception as e:
        return {
            'image_quality': 'uncertain',
            'blur_score'   : 0.0,
            'brightness'   : 0.0,
            'contrast'     : 0.0,
            'confidence'   : 'low'
        }


print('Quality detection functions loaded')
print(f'Thresholds:')
print(f'  Blur threshold       : {BLUR_THRESHOLD} (Laplacian variance)')
print(f'  Dark threshold       : {DARK_THRESHOLD} (mean brightness)')
print(f'  Bright threshold     : {BRIGHT_THRESHOLD} (mean brightness)')
print(f'  Contrast threshold   : {CONTRAST_THRESHOLD} (std deviation)')

# ==========================================
# CELL 8
# ==========================================
# Load labels
df = pd.read_csv(LABELS_PATH)
print(f'Loaded {len(df)} records from labels.csv')

# Test on 5 sample images
sample = df.sample(5, random_state=42)

print('\nSample quality assessments:')
print('='*70)

fig, axes = plt.subplots(1, 5, figsize=(18, 4))
fig.suptitle('Sample Image Quality Assessment', fontsize=13, fontweight='bold')

for i, (_, row) in enumerate(sample.iterrows()):
    result = assess_quality(row['image_path'], row['input_type'])

    print(f"Image : {row['filename']}")
    print(f"  Quality    : {result['image_quality']}")
    print(f"  Blur score : {result['blur_score']:.2f}")
    print(f"  Brightness : {result['brightness']:.2f}")
    print(f"  Contrast   : {result['contrast']:.2f}")
    print(f"  Confidence : {result['confidence']}")
    print()

    try:
        img = Image.open(row['image_path']).convert('RGB')
        axes[i].imshow(img)
        axes[i].set_title(
            f"{result['image_quality']}\n"
            f"blur:{result['blur_score']:.0f} "
            f"bright:{result['brightness']:.0f}",
            fontsize=8
        )
    except:
        pass
    axes[i].axis('off')

plt.tight_layout()
plt.show()
print('='*70)

# ==========================================
# CELL 10
# ==========================================
print(f'Running quality detection on {len(df)} images...')
print('This may take a few minutes...')

quality_labels  = []
blur_scores     = []
brightness_vals = []
contrast_vals   = []
confidences     = []

for _, row in tqdm(df.iterrows(), total=len(df), desc='Quality detection'):
    result = assess_quality(row['image_path'], row['input_type'])
    quality_labels.append(result['image_quality'])
    blur_scores.append(result['blur_score'])
    brightness_vals.append(result['brightness'])
    contrast_vals.append(result['contrast'])
    confidences.append(result['confidence'])

df['image_quality']  = quality_labels
df['blur_score']     = blur_scores
df['brightness']     = brightness_vals
df['contrast']       = contrast_vals
df['quality_conf']   = confidences

print('\nQuality detection complete')
print('='*50)
print('Quality label distribution:')
for label, count in df['image_quality'].value_counts().items():
    pct = count / len(df) * 100
    print(f'  {label:<20} : {count:>5} ({pct:.1f}%)')
print('='*50)

# ==========================================
# CELL 12
# ==========================================
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Quality label distribution
quality_counts = df['image_quality'].value_counts()
colors = ['seagreen','coral','steelblue','mediumpurple','goldenrod','gray']
axes[0].bar(quality_counts.index, quality_counts.values,
            color=colors[:len(quality_counts)])
axes[0].set_title('Image Quality Distribution')
axes[0].set_ylabel('Count')
axes[0].tick_params(axis='x', rotation=20)
for i, v in enumerate(quality_counts.values):
    axes[0].text(i, v + 2, str(v), ha='center', fontsize=9)

# Blur score distribution
axes[1].hist(df['blur_score'].clip(0, 1000), bins=50,
             color='steelblue', edgecolor='white')
axes[1].axvline(BLUR_THRESHOLD, color='red', linestyle='--',
                label=f'Blur threshold ({BLUR_THRESHOLD})')
axes[1].set_title('Blur Score Distribution (Laplacian)')
axes[1].set_xlabel('Laplacian Variance')
axes[1].legend()

# Brightness distribution
axes[2].hist(df['brightness'], bins=50, color='goldenrod', edgecolor='white')
axes[2].axvline(DARK_THRESHOLD,   color='blue',  linestyle='--',
                label=f'Dark ({DARK_THRESHOLD})')
axes[2].axvline(BRIGHT_THRESHOLD, color='red',   linestyle='--',
                label=f'Bright ({BRIGHT_THRESHOLD})')
axes[2].set_title('Brightness Distribution')
axes[2].set_xlabel('Mean Pixel Value')
axes[2].legend()

plt.tight_layout()
plt.show()

# ==========================================
# CELL 14
# ==========================================
quality_labels_unique = df['image_quality'].unique()
n_cols = 4
n_rows = len(quality_labels_unique)

fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, n_rows * 3))
fig.suptitle('Sample Images per Quality Label', fontsize=13, fontweight='bold')

if n_rows == 1:
    axes = [axes]

for row_idx, label in enumerate(sorted(quality_labels_unique)):
    subset = df[df['image_quality'] == label]
    sample = subset.sample(min(n_cols, len(subset)), random_state=42)

    for col_idx in range(n_cols):
        ax = axes[row_idx][col_idx]
        if col_idx < len(sample):
            try:
                img = Image.open(sample.iloc[col_idx]['image_path']).convert('RGB')
                ax.imshow(img)
                blur = sample.iloc[col_idx]['blur_score']
                bright = sample.iloc[col_idx]['brightness']
                ax.set_title(f'blur:{blur:.0f} bright:{bright:.0f}', fontsize=7)
                if col_idx == 0:
                    ax.set_ylabel(label, fontsize=9, rotation=0,
                                  labelpad=70, va='center')
            except:
                pass
        ax.axis('off')

plt.tight_layout()
plt.show()

# ==========================================
# CELL 16
# ==========================================
single_df = df[df['input_type'] == 'single_tree']

quality_by_group = single_df.groupby(['species_group', 'image_quality']).size().unstack(fill_value=0)

quality_by_group.plot(kind='bar', figsize=(14, 5), colormap='Set2', edgecolor='white')
plt.title('Image Quality Distribution per Species Group')
plt.ylabel('Count')
plt.xlabel('Species Group')
plt.xticks(rotation=15)
plt.legend(loc='upper right', fontsize=9)
plt.tight_layout()
plt.show()

print('Quality breakdown per species group:')
print(quality_by_group.to_string())

# ==========================================
# CELL 18
# ==========================================
print('='*50)
print('CONFIDENCE DISTRIBUTION')
print('='*50)

for conf, count in df['quality_conf'].value_counts().items():
    pct = count / len(df) * 100
    print(f'  {conf:<10} : {count:>5} ({pct:.1f}%)')

print()
print('Confidence meaning:')
print('  high   : clear signal — blur/brightness far from threshold')
print('  medium : near threshold — borderline case')
print('  low    : uncertain — review recommended')
print('='*50)

# ==========================================
# CELL 20
# ==========================================
# Save updated labels.csv with quality labels filled
df.to_csv(LABELS_PATH, index=False)

# Also update labels_split.csv
df_split = pd.read_csv(SPLIT_PATH)
quality_map = df.set_index('image_path')[['image_quality','blur_score',
                                           'brightness','contrast','quality_conf']]
df_split = df_split.join(quality_map, on='image_path', rsuffix='_new')

# Update quality columns
for col in ['image_quality','blur_score','brightness','contrast','quality_conf']:
    if col+'_new' in df_split.columns:
        df_split[col] = df_split[col+'_new']
        df_split.drop(columns=[col+'_new'], inplace=True)

df_split.to_csv(SPLIT_PATH, index=False)

print('='*50)
print('LABELS UPDATED WITH QUALITY')
print('='*50)
print(f'labels.csv updated      : {LABELS_PATH}')
print(f'labels_split.csv updated: {SPLIT_PATH}')
print()
print('Quality label summary:')
for label, count in df['image_quality'].value_counts().items():
    print(f'  {label:<20} : {count}')
print('='*50)

# ==========================================
# CELL 22
# ==========================================
# Images that need human review attention
flagged = df[
    (df['image_quality'].isin(['blurry', 'low_light', 'overexposed', 'uncertain'])) &
    (df['quality_conf'] == 'high')
]

print('='*60)
print('FLAGGED IMAGES — POOR QUALITY (HIGH CONFIDENCE)')
print('='*60)
print(f'Total flagged : {len(flagged)}')
print()

if len(flagged) > 0:
    print('Breakdown:')
    for label, count in flagged['image_quality'].value_counts().items():
        print(f'  {label:<20} : {count}')
    print()
    print('These images will still be used for training')
    print('but will be flagged in the review interface')
    print('so approvers know to re-capture if possible')
else:
    print('No high-confidence poor quality images found')

print('='*60)

# ==========================================
# CELL 24
# ==========================================
print('='*60)
print('IMAGE QUALITY DETECTION COMPLETE')
print('='*60)
print(f'Total images assessed : {len(df)}')
print()
print('Quality distribution:')
for label, count in df['image_quality'].value_counts().items():
    pct = count / len(df) * 100
    bar = '█' * int(pct / 2)
    print(f'  {label:<15} : {count:>5} ({pct:>5.1f}%) {bar}')
print()
print('Metrics saved to labels.csv and labels_split.csv:')
print('  image_quality  : quality label')
print('  blur_score     : Laplacian variance')
print('  brightness     : mean pixel value')
print('  contrast       : std deviation')
print('  quality_conf   : confidence level')
print()
print('Next step : Notebook 03 — Species Classification')
print('='*60)

# ==========================================
# CELL 25
# ==========================================


# ==========================================
# CELL 26
# ==========================================


# ==========================================
# CELL 27
# ==========================================


