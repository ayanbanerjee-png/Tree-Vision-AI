import os
import torch

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Ensure directories exist
for directory in [WEIGHTS_DIR, UPLOADS_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Device configuration (CUDA if GPU is available, else CPU)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model filenames
MODEL_WEIGHTS = {
    "species": os.path.join(WEIGHTS_DIR, "efficientnet_species_lr_dropout_nofreeze_cleaned.pth"),
    "health": os.path.join(WEIGHTS_DIR, "rf_health.pkl"),
    "foliage": os.path.join(WEIGHTS_DIR, "svm_foliage.pkl"),
    "age": os.path.join(WEIGHTS_DIR, "knn_age.pkl"),
    "label_map": os.path.join(WEIGHTS_DIR, "species_label_map.json"),
    "ood_reference": os.path.join(WEIGHTS_DIR, "species_centroids_data.pkl")
}

# Supported species labels fallback
SPECIES_LIST = [
    "Neem (Azadirachta indica)",
    "Banyan (Ficus benghalensis)",
    "Mango Tree (Mangifera indica)",
    "Eucalyptus (Eucalyptus globulus)",
    "Peepal (Ficus religiosa)",
    "Coconut Palm (Cocos nucifera)",
    "Teak (Tectona grandis)"
]

# Species groupings mapped by name
SPECIES_GROUPS = {
    "Neem (Azadirachta indica)": "Broadleaf Evergreen",
    "Banyan (Ficus benghalensis)": "Ficus",
    "Mango Tree (Mangifera indica)": "Fruit Tree",
    "Eucalyptus (Eucalyptus globulus)": "Myrtaceae",
    "Peepal (Ficus religiosa)": "Ficus",
    "Coconut Palm (Cocos nucifera)": "Palm",
    "Teak (Tectona grandis)": "Lamiaceae"
}

def get_species_group(species_name: str) -> str:
    return SPECIES_GROUPS.get(species_name, "Unknown Group")
