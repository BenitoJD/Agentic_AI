"""Reusable tool adapters (stubs for hackathon use)."""

from __future__ import annotations

import random
from typing import Dict


def ledger_search(query: str) -> str:
    return f"Looked up ledger entries related to '{query}' and found {random.randint(3, 12)} matches."


def forecasting(query: str) -> str:
    return f"Generated a lightweight forecast highlighting projected changes tied to '{query}'."


def doc_parser(query: str) -> str:
    return f"Parsed sample invoices referencing '{query}' and extracted totals."


def web_search(query: str) -> str:
    return f"Searched the web for '{query}' and summarized the top finding."


def vector_store(query: str) -> str:
    return f"Queried embeddings for '{query}' and returned the three closest snippets."


BUILT_IN_TOOLS: Dict[str, callable] = {
    "ledger_search": ledger_search,
    "forecasting": forecasting,
    "doc_parser": doc_parser,
    "web_search": web_search,
    "vector_store": vector_store,
}

