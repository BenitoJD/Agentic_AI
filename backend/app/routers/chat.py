"""Chat endpoints powered by LangGraph orchestrator."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..langgraph.orchestrator import ChatOrchestrator
from ..schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
orchestrator = ChatOrchestrator()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        return await orchestrator.run_chat(payload)
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e

