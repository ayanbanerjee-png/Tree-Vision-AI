# ==========================================
# CELL 2
# ==========================================
import os

PROJECT_ROOT     = r'C:\Users\AYAN\Flocard Tree AI'
COMBINED_ROOT     = os.path.join(PROJECT_ROOT, 'data', 'combined')
EMBEDDINGS_ROOT    = os.path.join(PROJECT_ROOT, 'data', 'embeddings')
MODELS_ROOT       = os.path.join(PROJECT_ROOT, 'models')

SPLIT_PATH         = os.path.join(COMBINED_ROOT, 'labels_split.csv')
PATHS_ARRAY_PATH   = os.path.join(EMBEDDINGS_ROOT, 'dinov2_paths.npy')
EMB_ARRAY_PATH     = os.path.join(EMBEDDINGS_ROOT, 'dinov2_embeddings.npy')

os.makedirs(MODELS_ROOT, exist_ok=True)
print('Paths set successfully')

# ==========================================
# CELL 4
# ==========================================
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

RANDOM_STATE = 42
print('Libraries loaded')

# ==========================================
# CELL 6
# ==========================================
emb_paths = np.load(PATHS_ARRAY_PATH, allow_pickle=True)
emb_vectors = np.load(EMB_ARRAY_PATH, allow_pickle=True)
path_to_embedding = {p: v for p, v in zip(emb_paths, emb_vectors)}
print(f'Loaded {len(path_to_embedding)} embeddings.')

df = pd.read_csv(SPLIT_PATH)
df_single = df[df['input_type'] == 'single_tree'].copy()
df_single['use_path'] = df_single.apply(
    lambda r: r['std_path'] if isinstance(r.get('std_path'), str) and os.path.exists(r['std_path'])
              else r['image_path'],
    axis=1
)
df_single['has_embedding'] = df_single['use_path'].isin(path_to_embedding)
df_single = df_single[df_single['has_embedding']].reset_index(drop=True)

print(f'single_tree images with embeddings : {len(df_single)}')
for col in ['health', 'age', 'foliage']:
    real = (df_single[col] != 'Uncertain').sum()
    print(f'  {col:8s} — real labels: {real}')

# ==========================================
# CELL 8
# ==========================================
def build_dataset(df, label_col):
    confident = df[df[label_col] != 'Uncertain'].copy()
    X = np.stack([path_to_embedding[p] for p in confident['use_path']])
    y = confident[label_col].values
    return X, y, confident

def train_and_report(model, X, y, label_col, test_size=0.25):
    class_counts = pd.Series(y).value_counts()
    can_stratify = (class_counts.min() >= 2) and (len(y) * test_size >= len(class_counts))

    if can_stratify:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
        )
    else:
        print('Warning: cannot stratify (a class has <2 examples) — using plain random split.')
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=RANDOM_STATE
        )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f'\n{label_col.upper()} — class distribution (full set):')
    print(class_counts)
    print(f'\nTrain size: {len(X_train)}  |  Test size: {len(X_test)}')
    print('\nClassification report (test set):')
    print(classification_report(y_test, y_pred, zero_division=0))

    return model, X_test, y_test, y_pred

print('Helper functions defined.')

# ==========================================
# CELL 10
# ==========================================
X_health, y_health, health_df = build_dataset(df_single, 'health')
print(f'Health dataset: {len(X_health)} images')

rf_health = RandomForestClassifier(
    n_estimators=200, max_depth=None, class_weight='balanced', random_state=RANDOM_STATE
)
rf_health, X_test_h, y_test_h, y_pred_h = train_and_report(rf_health, X_health, y_health, 'health')

RF_HEALTH_PATH = os.path.join(MODELS_ROOT, 'rf_health.pkl')
joblib.dump(rf_health, RF_HEALTH_PATH)
print(f'\nModel saved to: {RF_HEALTH_PATH}')

# Note: Damaged has only 1 example total. With this little data, its precision/recall
# on the test set is not a meaningful measurement -- it either lands in train or test,
# and either way the model cannot learn or be validated on a single example.
# This is a data-volume limitation, not a modeling bug. See docs/failure_cases.md.

# ==========================================
# CELL 12
# ==========================================
X_foliage, y_foliage, foliage_df = build_dataset(df_single, 'foliage')
print(f'Foliage dataset: {len(X_foliage)} images')

svm_foliage = SVC(kernel='rbf', C=1.0, class_weight='balanced', probability=True, random_state=RANDOM_STATE)
svm_foliage, X_test_f, y_test_f, y_pred_f = train_and_report(svm_foliage, X_foliage, y_foliage, 'foliage')

SVM_FOLIAGE_PATH = os.path.join(MODELS_ROOT, 'svm_foliage.pkl')
joblib.dump(svm_foliage, SVM_FOLIAGE_PATH)
print(f'\nModel saved to: {SVM_FOLIAGE_PATH}')

# Note: Partial Foliage has only 5 examples, and Leafless has 0 -- the schema's
# 'Leafless' category is entirely absent from this seed/propagation round. This
# classifier cannot predict Leafless at all until real examples are labeled.

# ==========================================
# CELL 14
# ==========================================
X_age, y_age, age_df = build_dataset(df_single, 'age')
print(f'Age dataset: {len(X_age)} images')

knn_age = KNeighborsClassifier(n_neighbors=5, weights='distance', metric='cosine')
knn_age, X_test_a, y_test_a, y_pred_a = train_and_report(knn_age, X_age, y_age, 'age')

KNN_AGE_PATH = os.path.join(MODELS_ROOT, 'knn_age.pkl')
joblib.dump(knn_age, KNN_AGE_PATH)
print(f'\nModel saved to: {KNN_AGE_PATH}')

# Note: age is the hardest category by design -- no scale reference exists in a
# single 2D photo (see docs/assumptions.md, 'age estimation' discussion). Read
# this classifier's accuracy as a coarse visual proxy, not a precise measurement.

# ==========================================
# CELL 16
# ==========================================
print('=' * 60)
print('NOTEBOOK 05 COMPLETE — AUXILIARY CLASSIFIERS')
print('=' * 60)
print(f'Health  (Random Forest) : {len(X_health)} labeled images -> {RF_HEALTH_PATH}')
print(f'Foliage (SVM)           : {len(X_foliage)} labeled images -> {SVM_FOLIAGE_PATH}')
print(f'Age     (KNN)           : {len(X_age)} labeled images -> {KNN_AGE_PATH}')
print()
print('Known limitations (see docs/failure_cases.md):')
print('  - Health: Damaged class has only 1 example -- not validly measurable')
print('  - Foliage: Leafless class has 0 examples -- classifier cannot predict it')
print('  - Age: no scale reference in single photos -- coarse proxy, not precise')
print()
print('Next step: expand labeled set (more seed labeling + propagation rounds)')
print('           to cover missing/thin classes before treating these as final.')
print('=' * 60)

# ==========================================
# CELL 18
# ==========================================
## Cell 9 — Honest Evaluation: Train on Propagated Only, Test on Manual Labels Only

MANUAL_LABELS_PATH = os.path.join(COMBINED_ROOT, 'manual_labels.csv')
PROPAGATED_LABELS_PATH = os.path.join(COMBINED_ROOT, 'propagated_labels.csv')

manual_labels_df = pd.read_csv(MANUAL_LABELS_PATH)
propagated_labels_df = pd.read_csv(PROPAGATED_LABELS_PATH)

manual_paths = set(manual_labels_df['std_path'])
propagated_paths = set(propagated_labels_df['std_path'])

print(f'Manual (real ground truth)  : {len(manual_paths)} images')
print(f'Propagated (embedding-based): {len(propagated_paths)} images')

def honest_eval(label_col, model_class, model_kwargs):
    # Train ONLY on propagated labels (excluding this category's Uncertain rows)
    train_df = propagated_labels_df[propagated_labels_df[label_col] != 'Uncertain'].copy()
    train_df = train_df[train_df['std_path'].isin(propagated_paths)]

    # Test ONLY on manual labels (excluding Uncertain), never used in training
    test_df = manual_labels_df[manual_labels_df[label_col] != 'Uncertain'].copy()

    X_train = np.stack([path_to_embedding[p] for p in train_df['std_path']])
    y_train = train_df[label_col].values
    X_test = np.stack([path_to_embedding[p] for p in test_df['std_path']])
    y_test = test_df[label_col].values

    print(f'\n{"=" * 50}')
    print(f'{label_col.upper()} — honest evaluation')
    print(f'{"=" * 50}')
    print(f'Train (propagated only) : {len(X_train)}  |  classes: {pd.Series(y_train).value_counts().to_dict()}')
    print(f'Test  (manual only)     : {len(X_test)}  |  classes: {pd.Series(y_test).value_counts().to_dict()}')

    model = model_class(**model_kwargs)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print('\nClassification report (test = real human labels):')
    print(classification_report(y_test, y_pred, zero_division=0))
    return model

_ = honest_eval('health', RandomForestClassifier,
                {'n_estimators': 200, 'class_weight': 'balanced', 'random_state': RANDOM_STATE})
_ = honest_eval('foliage', SVC,
                {'kernel': 'rbf', 'C': 1.0, 'class_weight': 'balanced', 'random_state': RANDOM_STATE})
_ = honest_eval('age', KNeighborsClassifier,
                {'n_neighbors': 5, 'weights': 'distance', 'metric': 'cosine'})

# ==========================================
# CELL 19
# ==========================================


