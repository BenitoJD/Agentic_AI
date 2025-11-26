"""LLM helpers with Ollama/OpenAI fallback."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import settings

logger = logging.getLogger(__name__)


def _ollama_available(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=0.3)
        response.raise_for_status()
        return True
    except Exception as exc:  # pragma: no cover - network fallback path
        logger.debug("Ollama probe failed: %s", exc)
        return False


def _build_ollama() -> Optional[BaseChatModel]:
    if not settings.ollama_model or not settings.ollama_base_url:
        return None

    if not _ollama_available(settings.ollama_base_url):
        return None

    logger.info("Using Ollama model %s at %s", settings.ollama_model, settings.ollama_base_url)
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.temperature,
    )


def _build_openai() -> Optional[BaseChatModel]:
    if not settings.openai_api_key:
        return None

    logger.info("Using OpenAI model %s", settings.openai_model)
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.temperature,
    )


def _build_gemini() -> Optional[BaseChatModel]:
    if not settings.gemini_api_key:
        return None

    logger.info("Using Gemini model %s", settings.gemini_model)
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
    )


def get_llm() -> Optional[BaseChatModel]:
    """Return the preferred LLM, preferring Ollama when available."""
    preference = (settings.llm_preference or "auto").lower()

    if preference in ("auto", "ollama"):
        ollama_llm = _build_ollama()
        if ollama_llm:
            return ollama_llm
        if preference == "ollama":
            return None

    if preference in ("auto", "openai"):
        openai_llm = _build_openai()
        if openai_llm:
            return openai_llm
        if preference == "openai":
            return None

    if preference in ("auto", "gemini"):
        gemini_llm = _build_gemini()
        if gemini_llm:
            return gemini_llm

    return None

