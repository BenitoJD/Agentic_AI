"""Agent endpoints for modular agent system."""

from __future__ import annotations

from fastapi import APIRouter

from ..agents import rag_knowledge, web_search
from ..schemas import AgentRequest, AgentResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/rag-knowledge", response_model=AgentResponse)
async def rag_knowledge_endpoint(request: AgentRequest) -> AgentResponse:
  """RAG Knowledge Agent - Document search and Q&A from uploaded documents."""
  return await rag_knowledge.execute_agent(request)


@router.post("/web-search", response_model=AgentResponse)
async def web_search_endpoint(request: AgentRequest) -> AgentResponse:
  """Web Search Agent - Internet search and current information."""
  return await web_search.execute_agent(request)

