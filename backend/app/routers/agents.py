"""Agent endpoints for modular agent system."""

from __future__ import annotations

from fastapi import APIRouter

from ..agents import performance_analyzer
from ..schemas import AgentRequest, AgentResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/performance-analyzer", response_model=AgentResponse)
async def performance_analyzer_endpoint(request: AgentRequest) -> AgentResponse:
    """Performance Analysis Agent - Analyzes logs and metrics to identify bottlenecks."""
    return await performance_analyzer.execute_agent(request)

