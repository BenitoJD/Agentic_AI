"""Web Search + Real-Time Info Agent - Internet search and current information."""

from __future__ import annotations

import re

import httpx
import xml.etree.ElementTree as ET

from ..schemas import AgentRequest, AgentResponse
from ..services.llm import get_llm
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


SYSTEM_PROMPT = (
    "You are Nova, an assistant that summarizes web search results and real-time information. "
    "Always mention that information came from an online search and cite sources when available."
)


def _build_history_messages(history):
    messages = []
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    return messages


def _google_news_search(query: str) -> list[str]:
    params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    try:
        resp = httpx.get("https://news.google.com/rss/search", params=params, timeout=10.0)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    snippets: list[str] = []
    for item in root.findall(".//item")[:5]:
        title_el = item.find("title")
        link_el = item.find("link")
        if title_el is not None and link_el is not None:
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            if title and link:
                snippets.append(f"{title} (Source: {link})")
    return snippets


def _duckduckgo_search(query: str) -> list[str]:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    try:
        resp = httpx.get("https://api.duckduckgo.com/", params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    snippets: list[str] = []
    abstract = data.get("AbstractText")
    if abstract:
        snippets.append(f"Abstract: {abstract}")
    for topic in data.get("RelatedTopics", [])[:5]:
        if isinstance(topic, dict):
            text = topic.get("Text")
            url = topic.get("FirstURL")
            if text and url:
                snippets.append(f"{text} (Source: {url})")
    return snippets


def _web_search(query: str) -> str:
    snippets = _google_news_search(query)
    if not snippets:
        snippets = _duckduckgo_search(query)
    if not snippets:
        return "No helpful matches were found during the web search."
    return "\n".join(snippets)


def _invoke_llm(prompt: str, history, web_results: str | None = None) -> str:
    llm = get_llm()
    if not llm:
        if web_results:
            return f"(LLM unavailable) Web search results:\n{web_results}\n\nUser prompt: {prompt}"
        return "(LLM unavailable right now.)"

    messages = [SystemMessage(content=SYSTEM_PROMPT), *_build_history_messages(history)]
    if web_results:
        messages.append(
            HumanMessage(
                content=(
                    "Summarize or answer using the following web search results. "
                    "Always mention they came from an online search.\n\n"
                    f"{web_results}"
                )
            )
        )
    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)
    content = getattr(response, "content", None)
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if content:
        return str(content)
    return str(response)


async def execute_agent(request: AgentRequest) -> AgentResponse:
    """Execute Web Search + Real-Time Info Agent."""
    query = (request.prompt or "").strip()
    lower = query.lower()

    # If the user only says something like "check internet" or gives a very short,
    # generic query, ask them to clarify what they actually want searched.
    generic_phrases = [
        "check internet",
        "check the internet",
        "access internet",
        "access the internet",
        "search the web",
        "search internet",
        "use the internet",
        "do a web search",
    ]
    if any(phrase in lower for phrase in generic_phrases):
        clarification = (
            "I can search the internet, but this request is too broad.\n\n"
            "Please tell me exactly what you want me to look up, for example:\n"
            '- "Check internet and tell me when the next men\'s Cricket World Cup is."\n'
            '- "Check internet and summarize today\'s major AI safety news."'
        )
        # Low confidence so the orchestrator may also propose follow-up questions.
        return AgentResponse(response=clarification, sources=[], confidence=0.2)

    results = _web_search(query)

    # Extract source URLs from the raw search snippets so the UI can show them.
    sources: list[str] = []
    if results:
        for line in results.splitlines():
            match = re.search(r"\(Source:\s*(.+?)\)", line)
            if match:
                url = match.group(1).strip()
                sources.append(url)
        # De-duplicate, preserve order
        sources = list(dict.fromkeys(sources))

    # Calculate confidence based on search results quality
    has_results = results and "No helpful matches" not in results
    result_count = results.count("(Source:") if results else 0

    confidence = 0.6
    if has_results:
        confidence += 0.2
    if result_count >= 3:
        confidence += 0.15
    elif result_count >= 1:
        confidence += 0.05

    confidence = min(1.0, confidence)

    result = _invoke_llm(request.prompt, request.history, web_results=results)

    return AgentResponse(response=result, sources=sources, confidence=confidence)

