import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
KB_DIR = BASE_DIR / "data" / "best_practices"
INDEX_DIR = BASE_DIR / "data" / "faiss_index"
INDEX_PATH = INDEX_DIR / "index.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.pkl"

# Embedding model — runs locally, no API needed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_documents() -> list[dict]:
    """Load all best practice text files and split into chunks."""
    chunks = []
    for filepath in KB_DIR.glob("*.txt"):
        dimension = filepath.stem  # filename = dimension name
        text = filepath.read_text(encoding="utf-8")

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]

        for i, para in enumerate(paragraphs):
            chunks.append({
                "id": f"{dimension}_{i}",
                "dimension": dimension,
                "text": para,
                "source": filepath.name,
            })

    print(f"Loaded {len(chunks)} chunks from knowledge base")
    return chunks


def build_index(force_rebuild: bool = False):
    """Build FAISS index from knowledge base documents."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if INDEX_PATH.exists() and CHUNKS_PATH.exists() and not force_rebuild:
        print("FAISS index already exists — skipping rebuild")
        return

    print("Building FAISS index...")
    chunks = load_documents()

    # Load HuggingFace embedding model
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine on normalized vecs
    index.add(embeddings)

    # Save index and chunks
    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print(f"FAISS index built — {index.ntotal} vectors, dimension {dimension}")


def load_index():
    """Load FAISS index and chunks from disk."""
    if not INDEX_PATH.exists():
        build_index()

    index = faiss.read_index(str(INDEX_PATH))
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    return index, chunks


if __name__ == "__main__":
    build_index(force_rebuild=True)
    print("Knowledge base ready.")