import os
import pickle
import numpy as np

from backend.utils.config import MODEL_WEIGHTS

OOD_THRESHOLD = 0.50
OOD_MARGIN = 0.05
OOD_K = 5

_EMBEDDINGS = None
_EMBEDDINGS_NORM = None
_PATHS = None
_PATH_TO_SPECIES = None


def load_ood_reference_data():
    global _EMBEDDINGS, _EMBEDDINGS_NORM, _PATHS, _PATH_TO_SPECIES

    data_path = MODEL_WEIGHTS.get("ood_reference")
    if not data_path or not os.path.exists(data_path):
        raise FileNotFoundError(
            f"OOD reference data not found at: {data_path}. "
            "Expected a pickle with keys 'embeddings', 'paths', 'path_to_species'."
        )

    print(f"[INFO] Loading OOD reference embeddings from {data_path}...")
    with open(data_path, "rb") as f:
        data = pickle.load(f)

    _EMBEDDINGS = np.asarray(data["embeddings"], dtype=np.float32)
    _PATHS = list(data["paths"])
    _PATH_TO_SPECIES = data["path_to_species"]

    norms = np.linalg.norm(_EMBEDDINGS, axis=1, keepdims=True) + 1e-8
    _EMBEDDINGS_NORM = _EMBEDDINGS / norms

    n_species = len(set(_PATH_TO_SPECIES.values()))
    print(f"[INFO] OOD reference loaded: {len(_PATHS)} embeddings across {n_species} species")


load_ood_reference_data()


def check_species_ood(embedding: np.ndarray,
                       threshold: float = OOD_THRESHOLD,
                       margin: float = OOD_MARGIN,
                       k: int = OOD_K) -> dict:
    global _EMBEDDINGS_NORM, _PATHS, _PATH_TO_SPECIES

    if _EMBEDDINGS_NORM is None:
        raise RuntimeError("OOD reference data not loaded.")

    emb = np.asarray(embedding, dtype=np.float32).reshape(-1)
    emb_norm = emb / (np.linalg.norm(emb) + 1e-8)

    sims = _EMBEDDINGS_NORM @ emb_norm

    top_k_idx = np.argsort(sims)[-k:][::-1]
    top_k_sims = sims[top_k_idx]
    top_k_paths = [_PATHS[i] for i in top_k_idx]
    top_k_species = [_PATH_TO_SPECIES.get(p, "unknown") for p in top_k_paths]

    best_species = top_k_species[0]
    best_sim = float(top_k_sims[0])

    runner_up_sim = 0.0
    for sp, sim in zip(top_k_species[1:], top_k_sims[1:]):
        if sp != best_species:
            runner_up_sim = float(sim)
            break

    gap = best_sim - runner_up_sim
    is_recognized = (best_sim >= threshold) and (gap >= margin)

    return {
        "nearest_known_species": best_species,
        "similarity": round(best_sim, 4),
        "runner_up_species_gap": round(gap, 4),
        "is_recognized_species": is_recognized,
    }
