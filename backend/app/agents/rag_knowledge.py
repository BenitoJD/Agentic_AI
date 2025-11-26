"""RAG Knowledge Agent - Document search and Q&A from uploaded documents."""

from __future__ import annotations

from ..schemas import AgentRequest, AgentResponse
from ..services.llm import get_llm
from ..services.vector_store import search, search_with_scores, list_files
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


SYSTEM_PROMPT = (
    "You are Nova, an assistant that grounds answers in uploaded documents. "
    "When document snippets are available, use them. If they are irrelevant, say so."
)


def _build_history_messages(history):
    messages = []
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    return messages


def _invoke_llm(prompt: str, history, context: str | None = None) -> str:
    llm = get_llm()
    if not llm:
        if context:
            return f"(LLM unavailable) Context snippets:\n{context}\n\nUser prompt: {prompt}"
        return "(LLM unavailable right now.)"

    messages = [SystemMessage(content=SYSTEM_PROMPT), *_build_history_messages(history)]
    if context:
        messages.append(
            HumanMessage(
                content=(
                    "Use the following context snippets when helpful. "
                    "If they are irrelevant, say so.\n\n"
                    f"{context}"
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
    """Execute RAG Knowledge Agent - searches documents and answers questions."""
    try:
        # Special case: user asking what documents/PDFs are indexed.
        base_query = (request.prompt or "").strip()
        lower = base_query.lower()
        list_intent_phrases = [
            "what pdfs do we have",
            "what pdf do we have",
            "what documents do we have",
            "what docs do we have",
            "what files do we have",
            "which documents have i uploaded",
            "which files have i uploaded",
            "list my documents",
            "list my files",
        ]
        if any(phrase in lower for phrase in list_intent_phrases):
            indexed = list_files()
            if not indexed:
                return AgentResponse(
                    response=(
                        "I don’t see any indexed documents yet.\n\n"
                        "You can upload PDFs and other files from the Uploads page, and I’ll use them for answers."
                    ),
                    sources=[],
                    confidence=0.9,
                )

            lines = ["Here are the documents I currently have indexed:\n"]
            for item in indexed:
                filename = item.get("filename") or "Unknown"
                chunks = item.get("chunks", 0)
                lines.append(f"- {filename} (about {chunks} chunks)")
            summary = "\n".join(lines)
            return AgentResponse(
                response=summary,
                sources=[item.get("filename") or "Unknown" for item in indexed],
                confidence=0.95,
            )

        # Build a conversation-aware retrieval query using recent history
        last_user = None
        last_assistant = None
        if request.history:
            for msg in reversed(request.history):
                if not last_user and msg.role == "user":
                    last_user = msg
                elif not last_assistant and msg.role == "assistant":
                    last_assistant = msg
                if last_user and last_assistant:
                    break
        retrieval_parts = []
        if last_user:
            retrieval_parts.append(f"Previous user question: {last_user.content}")
        if last_assistant:
            retrieval_parts.append(f"My last answer: {last_assistant.content}")
        retrieval_parts.append(f"Current question: {base_query}")
        retrieval_query = "\n".join(retrieval_parts)

        # Search with scores for confidence calculation
        docs_with_scores = search_with_scores(retrieval_query, k=8)
        snippets: list[str] = []
        sources: list[str] = []
        scores: list[float] = []

        preferred_sources = set()
        if request.metadata and isinstance(request.metadata, dict):
            preferred = request.metadata.get("preferred_sources") or []
            if isinstance(preferred, list):
                preferred_sources = {str(name) for name in preferred}

        # If we have preferred sources from the previous turn, try to keep only those docs.
        if preferred_sources:
            filtered = []
            for doc, score in docs_with_scores:
                filename = doc.metadata.get("filename") or "Uploaded document"
                if filename in preferred_sources:
                    filtered.append((doc, score))
            if filtered:
                docs_with_scores = filtered

        for doc, score in docs_with_scores:
            content = doc.page_content.strip()
            if not content:
                continue
            snippets.append(content)
            sources.append(doc.metadata.get("filename") or "Uploaded document")
            # Convert distance to similarity (lower distance = higher similarity)
            # Chroma returns distance, so we normalize to 0-1 range
            # Handle negative scores or very large scores
            similarity = max(0.0, min(1.0, 1.0 - abs(score)))
            scores.append(similarity)

        if not snippets:
            # Fallback to direct answer if no documents are available
            result = _invoke_llm(request.prompt, request.history)
            # Low confidence when no documents found
            return AgentResponse(response=result, sources=[], confidence=0.3)

        # Calculate confidence based on average similarity and number of results
        avg_similarity = sum(scores) / len(scores) if scores else 0.0
        # Boost confidence if we have multiple relevant documents
        doc_count_factor = min(1.0, len(snippets) / 3.0)  # Max boost at 3+ docs
        confidence = min(1.0, avg_similarity * 0.7 + doc_count_factor * 0.3)

        context = "\n\n---\n\n".join(snippets)
        result = _invoke_llm(request.prompt, request.history, context=context)
        unique_sources = list(dict.fromkeys(sources))  # preserve order, remove dupes
        
        return AgentResponse(response=result, sources=unique_sources, confidence=confidence)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in RAG knowledge agent: {e}", exc_info=True)
        # Return error response with low confidence
        return AgentResponse(
            response=f"I encountered an error while searching documents: {str(e)}. Please try again or rephrase your question.",
            sources=[],
            confidence=0.1
        )

