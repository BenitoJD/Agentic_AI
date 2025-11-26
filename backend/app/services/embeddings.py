"""Embedding helpers."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from ..config import settings


class DummyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[0.0] * 1536 for _ in texts]

    def embed_query(self, text):
        return [0.0] * 1536


def _build_ollama_embeddings() -> Embeddings | None:
    if not settings.ollama_base_url or not settings.ollama_embedding_model:
        return None

    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
    )


def _build_openai_embeddings() -> Embeddings | None:
    if not settings.openai_api_key:
        return None
    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )


def get_embeddings() -> Embeddings:
    if settings.embedding_preference == "ollama":
        ollama = _build_ollama_embeddings()
        if ollama:
            return ollama
    if settings.embedding_preference in ("ollama", "openai"):
        openai = _build_openai_embeddings()
        if openai:
            return openai
    return DummyEmbeddings()
