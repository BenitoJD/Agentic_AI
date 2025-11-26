from __future__ import annotations

import os
import uuid
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from ..config import settings
from .embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    embeddings = get_embeddings()
    return Chroma(
        embedding_function=embeddings,
        persist_directory=settings.vector_store_path,
        collection_name=settings.vector_collection,
    )


def ingest_text(text: str, metadata: dict | None = None) -> int:
    os.makedirs(settings.vector_store_path, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = [Document(page_content=chunk, metadata=metadata or {}) for chunk in splitter.split_text(text)]

    store = get_store()
    store.add_documents(docs, ids=[str(uuid.uuid4()) for _ in docs])
    store.persist()
    return len(docs)


def search(query: str, k: int = 4) -> list[Document]:
    try:
        store = get_store()
        return store.similarity_search(query, k=k)
    except Exception:
        return []


def search_with_scores(query: str, k: int = 4) -> list[tuple[Document, float]]:
    """Search with similarity scores."""
    try:
        store = get_store()
        results = store.similarity_search_with_score(query, k=k)
        # Ensure we return a list of tuples
        return [(doc, float(score)) for doc, score in results]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error in search_with_scores: {e}", exc_info=True)
        return []


def list_files() -> list[dict]:
    """
    Return a summary of files currently stored in the vector database.

    Each entry contains:
    - filename: name of the uploaded file
    - chunks: number of chunks stored for that filename
    """
    try:
        store = get_store()
        # Access underlying Chroma collection to inspect metadatas
        collection = store._collection  # type: ignore[attr-defined]
        data = collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", []) or []

        counts: dict[str, int] = {}
        for meta in metadatas:
            if not isinstance(meta, dict):
                continue
            filename = meta.get("filename") or "Unknown"
            counts[filename] = counts.get(filename, 0) + 1

        return [
            {"filename": filename, "chunks": chunks}
            for filename, chunks in sorted(counts.items(), key=lambda x: x[0].lower())
        ]
    except Exception:
        return []