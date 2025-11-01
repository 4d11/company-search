from sentence_transformers import SentenceTransformer
from typing import List

from backend.settings import settings

# Global model instance (lazy-loaded)
_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get or initialize the embedding model.
    Using all-MiniLM-L6-v2: fast, lightweight, produces 384-dimensional embeddings.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate a vector embedding for a single text string.

    Args:
        text: The text to generate an embedding for

    Returns:
        A list of floats representing the embedding vector
    """
    if not text or text.strip() == "":
        # Return zero vector for empty text
        return [0.0] * settings.embedding_dimensions

    model = get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings for a batch of texts.
    More efficient than calling generate_embedding multiple times.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        A list of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]
