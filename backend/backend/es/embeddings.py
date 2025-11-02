from sentence_transformers import SentenceTransformer
from typing import List

from backend.settings import settings

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


def generate_composite_embedding(
    description: str,
    website_text: str,
    description_weight: float = 0.7
) -> List[float]:
    """
    Generate weighted composite embedding from description and website_text.

    This combines curated description (concise, signal-rich) with detailed website content
    to capture both high-level business focus and technical/product details.

    Args:
        description: Short company description (1-2 sentences), typically curated
        website_text: Full website scraped content (may be long, contains tech details)
        description_weight: Weight for description (default 0.7 = 70% description, 30% website)

    Returns:
        Weighted average embedding vector

    Example:
        Description: "AI-powered sales automation platform"
        Website text: "Our platform integrates with Salesforce... RESTful API... developer-friendly..."
        Result: Embedding captures both "sales automation" AND "API-first developer platform"
    """
    # Truncate website_text if too long (sentence-transformers has token limits ~512 tokens)
    # ~4 chars per token = ~2000 chars max for safety
    max_website_chars = 2000
    truncated_website = website_text[:max_website_chars] if website_text else ""

    desc_embedding = generate_embedding(description or "")
    web_embedding = generate_embedding(truncated_website)

    # Calc Weighted average
    website_weight = 1.0 - description_weight
    composite = [
        (d * description_weight + w * website_weight)
        for d, w in zip(desc_embedding, web_embedding)
    ]

    return composite


def generate_composite_embeddings_batch(
    company_data: List[tuple],
    description_weight: float = 0.7
) -> List[List[float]]:
    """
    Generate composite embeddings for multiple companies in batch (more efficient).

    Args:
        company_data: List of (description, website_text) tuples
        description_weight: Weight for description (default 0.7 = 70%)

    Returns:
        List of composite embedding vectors
    """
    max_website_chars = 2000

    descriptions = [desc or "" for desc, _ in company_data]
    websites = [
        (web[:max_website_chars] if web else "")
        for _, web in company_data
    ]

    # Batch encode both (much faster than individual encodes)
    model = get_embedding_model()
    print(f"Generating embeddings for {len(descriptions)} descriptions...")
    desc_embeddings = model.encode(descriptions, convert_to_tensor=False, show_progress_bar=True)
    print(f"Generating embeddings for {len(websites)} website texts...")
    web_embeddings = model.encode(websites, convert_to_tensor=False, show_progress_bar=True)

    # Weighted average for each company
    website_weight = 1.0 - description_weight
    composites = []
    for desc_emb, web_emb in zip(desc_embeddings, web_embeddings):
        composite = [
            (d * description_weight + w * website_weight)
            for d, w in zip(desc_emb.tolist(), web_emb.tolist())
        ]
        composites.append(composite)

    return composites
