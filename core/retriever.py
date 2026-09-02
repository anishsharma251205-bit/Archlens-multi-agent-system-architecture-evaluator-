
import threading

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from core.knowledge_base import load_index, EMBEDDING_MODEL


# ============================================================
# SHARED RESOURCES
# ============================================================

_index = None
_chunks = None
_model = None

# Prevent multiple agent threads from loading the model
# simultaneously during first initialization.
_resource_lock = threading.Lock()


def _get_resources():
    """Lazy load index, chunks, and embedding model safely."""

    global _index, _chunks, _model

    # Fast path: resources are already loaded.
    if _index is not None and _chunks is not None and _model is not None:
        return _index, _chunks, _model

    # Slow path: first thread initializes resources.
    with _resource_lock:

        # Check again after acquiring the lock.
        if _index is None or _chunks is None or _model is None:

            print("[ArchLens] Loading RAG resources...")

            _index, _chunks = load_index()

            if _index is None:
                raise RuntimeError(
                    "RAG FAISS index failed to load."
                )

            if _chunks is None:
                raise RuntimeError(
                    "RAG knowledge-base chunks failed to load."
                )

            _model = SentenceTransformer(
                EMBEDDING_MODEL
            )

            print("[ArchLens] RAG resources loaded.")

    return _index, _chunks, _model


def retrieve(
    query: str,
    dimension: str = None,
    top_k: int = 3
) -> str:
    """
    Retrieve top_k relevant best-practice chunks.

    Args:
        query: Search query used for semantic retrieval.
        dimension: Optional dimension filter such as
                   security, performance, cost, etc.
        top_k: Number of relevant chunks to return.

    Returns:
        Formatted knowledge-base context ready to inject
        into an agent prompt.

    Raises:
        ValueError: If query is missing or invalid.
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if query is None:
        raise ValueError(
            "RAG retrieval received query=None."
        )

    if not isinstance(query, str):
        raise ValueError(
            f"RAG retrieval expected a string query, "
            f"got {type(query).__name__}."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "RAG retrieval received an empty query."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    # ========================================================
    # LOAD SHARED RESOURCES
    # ========================================================

    index, chunks, model = _get_resources()

    # ========================================================
    # EMBED QUERY
    # ========================================================

    query_vec = model.encode(
        [query],
        convert_to_numpy=True
    ).astype(np.float32)

    faiss.normalize_L2(query_vec)

    # ========================================================
    # SEARCH
    # ========================================================

    search_k = min(
        top_k * 3,
        index.ntotal
    )

    if search_k <= 0:
        return ""

    scores, indices = index.search(
        query_vec,
        search_k
    )

    # ========================================================
    # FILTER RESULTS BY DIMENSION
    # ========================================================

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        if idx >= len(chunks):
            continue

        chunk = chunks[idx]

        # Ignore malformed KB entries.
        if not isinstance(chunk, dict):
            continue

        chunk_dimension = chunk.get(
            "dimension"
        )

        chunk_text = chunk.get(
            "text"
        )

        if not isinstance(
            chunk_dimension,
            str
        ):
            continue

        if not isinstance(
            chunk_text,
            str
        ):
            continue

        if not chunk_text.strip():
            continue

        if (
            dimension
            and chunk_dimension.lower() != dimension.lower()
        ):
            continue

        results.append(
            (score, chunk)
        )

        if len(results) >= top_k:
            break

    # ========================================================
    # FALLBACK
    # ========================================================

    # If the requested dimension produced no results,
    # return the best general results instead.
    if not results:

        for score, idx in zip(
            scores[0],
            indices[0]
        ):

            if idx == -1:
                continue

            if idx >= len(chunks):
                continue

            chunk = chunks[idx]

            if not isinstance(chunk, dict):
                continue

            chunk_dimension = chunk.get(
                "dimension"
            )

            chunk_text = chunk.get(
                "text"
            )

            if not isinstance(
                chunk_dimension,
                str
            ):
                continue

            if not isinstance(
                chunk_text,
                str
            ):
                continue

            if not chunk_text.strip():
                continue

            results.append(
                (score, chunk)
            )

            if len(results) >= top_k:
                break

    # ========================================================
    # FORMAT RESULTS
    # ========================================================

    if not results:
        return ""

    formatted = (
        "RELEVANT BEST PRACTICES FROM "
        "KNOWLEDGE BASE:\n"
    )

    formatted += "=" * 50 + "\n"

    for i, (score, chunk) in enumerate(
        results,
        1
    ):

        formatted += (
            f"\n[{i}] "
            f"{chunk['dimension'].upper()} "
            f"— relevance: {score:.2f}\n"
        )

        formatted += (
            chunk["text"].strip() + "\n"
        )

    formatted += "=" * 50 + "\n"

    formatted += (
        "Use the above best practices as "
        "reference when evaluating.\n\n"
    )

    return formatted


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    result = retrieve(
        "authentication and JWT security",
        dimension="security"
    )

    print(result)

