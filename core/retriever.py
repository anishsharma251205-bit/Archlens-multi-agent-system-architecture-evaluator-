import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from core.knowledge_base import load_index, EMBEDDING_MODEL

# Load once at module level — avoid reloading on every call
_index = None
_chunks = None
_model = None


def _get_resources():
    """Lazy load index, chunks, and model."""
    global _index, _chunks, _model
    if _index is None:
        _index, _chunks = load_index()
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _index, _chunks, _model


def retrieve(query: str, dimension: str = None, top_k: int = 3) -> str:
    """
    Retrieve top_k relevant best practice chunks for a given query.
    Optionally filter by dimension (security, scalability, etc.)
    Returns a formatted string ready to inject into agent prompts.
    """
    index, chunks, model = _get_resources()

    # Embed the query
    query_vec = model.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(query_vec)

    # Search
    scores, indices = index.search(query_vec, top_k * 3)

    # Filter by dimension if specified
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        if dimension and chunk["dimension"] != dimension:
            continue
        results.append((score, chunk))
        if len(results) >= top_k:
            break

    if not results:
        # Fallback: no dimension filter
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((score, chunks[idx]))
            if len(results) >= top_k:
                break

    # Format for prompt injection
    if not results:
        return ""

    formatted = "RELEVANT BEST PRACTICES FROM KNOWLEDGE BASE:\n"
    formatted += "=" * 50 + "\n"
    for i, (score, chunk) in enumerate(results, 1):
        formatted += f"\n[{i}] {chunk['dimension'].upper()} — relevance: {score:.2f}\n"
        formatted += chunk["text"] + "\n"
    formatted += "=" * 50 + "\n"
    formatted += "Use the above best practices as reference when evaluating.\n\n"

    return formatted


if __name__ == "__main__":
    # Quick test
    result = retrieve("authentication and JWT security", dimension="security")
    print(result)