"""Application-level performance analysis endpoints powered by the performance_analyzer agent."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents import performance_analyzer
from ..data.demo_metrics import get_application_details
from ..schemas import AgentRequest, BottleneckReport, PerformanceAnalysisResponse

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class ApplicationAnalysisRequest(BaseModel):
  """Optional extra parameters for app analysis (reserved for future use)."""


@router.post(
    "/applications/{app_id}",
    response_model=PerformanceAnalysisResponse,
)
async def analyze_application(app_id: str, _: ApplicationAnalysisRequest | None = None) -> PerformanceAnalysisResponse:
    """Run the performance analyzer LLM for a specific demo application."""
    detail = get_application_details(app_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Application not found")

    # Build a concise metrics summary as prior context
    summary_lines = [
        f"Application: {detail.name}",
        f"Status: {detail.status}",
        f"Current response time: {detail.responseTime} ms",
        f"Current error rate: {detail.errorRate} %",
        f"Current throughput: {detail.throughput} req/s",
    ]

    prompt = (
        "Analyze the performance metrics for this application and identify the top bottlenecks. "
        "Focus on CPU, memory, network, database, disk I/O, and application-level issues. "
        "Return a concise executive summary and a bulleted list of bottlenecks with severity and key evidence."
    )

    agent_request = AgentRequest(
        prompt=prompt,
        history=[],
        metadata={
            "kpis": None,
        },
    )

    # We call the generic performance analyzer and then wrap its response.
    agent_response = await performance_analyzer.execute_agent(agent_request)

    # For now we don't attempt to fully parse the text into structured bottlenecks;
    # we just return the raw text and an empty bottlenecks list (the frontend already
    # knows how to render free-form summaries).
    return PerformanceAnalysisResponse(
        response=(
            "Context:\n"
            + "\n".join(summary_lines)
            + "\n\nAnalysis:\n"
            + agent_response.response
        ),
        sources=agent_response.sources,
        confidence=agent_response.confidence,
        bottlenecks=[],
        metadata=agent_response.metadata,
    )


