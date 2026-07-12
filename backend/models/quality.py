import cv2
import numpy as np

# ── Thresholds (Preserved exactly from Notebook 02) ──────
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
    Preserved exactly from Notebook 02.
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

def analyze_image_quality(image_path: str, input_type: str = 'single_tree') -> dict:
    """
    Exposed wrapper function for FastAPI backend pipeline.
    """
    return assess_quality(image_path, input_type)
