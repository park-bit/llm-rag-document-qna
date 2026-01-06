
from sentence_transformers import SentenceTransformer
import numpy as np
import os


MODEL_NAME = os.getenv("SENTENCE_TRANSFORMER", "all-MiniLM-L6-v2")

_model = None

def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(text: str) -> np.ndarray:
    """
    Returns a 1D float32 numpy array for the given text.
    """
    model = _load_model()
    vec = model.encode(text, show_progress_bar=False)
    return np.asarray(vec, dtype="float32")
