import torch
from torchvision import transforms
from PIL import Image
import numpy as np
from backend.utils.config import DEVICE

# Constants matching Notebook 04
IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# Transforms exactly as defined in Notebook 04
eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

# Global model state loaded once
_dinov2_model = None

def load_dinov2_model():
    """
    Load DINOv2 model architecture and weights from Torch Hub.
    """
    global _dinov2_model
    print("Loading DINOv2-Small model (dinov2_vits14)...")
    try:
        # Load dinov2_vits14 from PyTorch Hub
        _dinov2_model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14', trust_repo=True)
        _dinov2_model.eval().to(DEVICE)
        
        # Freeze parameters exactly as in Notebook 04
        for p in _dinov2_model.parameters():
            p.requires_grad = False
            
        print("DINOv2 model loaded successfully!")
    except Exception as e:
        print(f"Error loading DINOv2 model: {e}")
        raise e

# Initialize model on import
load_dinov2_model()

def load_image(path):
    """
    Loads and converts image to RGB and applies eval_transform.
    Preserved exactly from Notebook 04.
    """
    img = Image.open(path).convert('RGB')
    return eval_transform(img)

def extract_dinov2_embeddings(image_path: str) -> np.ndarray:
    """
    Extract a 384-dimensional DINOv2 embedding vector from the image.
    Preserves the exact inference flow of Notebook 04.
    """
    global _dinov2_model
    try:
        # 1. Load and transform image
        img_tensor = load_image(image_path).unsqueeze(0).to(DEVICE)
        
        # 2. Extract features without gradient calculation
        with torch.no_grad():
            features = _dinov2_model(img_tensor)
            
        # 3. Move features to CPU and convert to NumPy array
        embedding = features.cpu().numpy()[0]
        return embedding
        
    except Exception as e:
        print(f"Error extracting DINOv2 embedding: {e}")
        # Return 384-dimensional zero vector as safe fallback
        return np.zeros(384, dtype=np.float32)
