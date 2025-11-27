"""KPI endpoints for managing performance thresholds."""

from __future__ import annotations

from fastapi import APIRouter
from typing import Optional

from ..schemas import KPIConfig, KPIExplanation, KPIThreshold
from ..agents.performance_analyzer import _detect_kpis_from_logs
from ..services.vector_store import search_with_scores

router = APIRouter(prefix="/api/kpis", tags=["kpis"])

# In-memory storage for custom KPIs (in production, use a database)
_custom_kpis: Optional[KPIConfig] = None


@router.get("", response_model=KPIConfig)
async def get_kpis() -> KPIConfig:
    """Get current KPI configuration (custom or detected from logs)."""
    # If custom KPIs are set, return them
    if _custom_kpis:
        return _custom_kpis
    
    # Otherwise, try to detect from logs
    try:
        docs_with_scores = search_with_scores("performance metrics cpu memory network database", k=10)
        snippets = [doc.page_content.strip() for doc, _ in docs_with_scores if doc.page_content.strip()]
        
        if snippets:
            detected = _detect_kpis_from_logs(snippets, {})
            # Convert detected dict to KPIConfig
            return KPIConfig(
                cpu=KPIThreshold(
                    threshold=detected.get("cpu", {}).get("threshold", 80.0),
                    unit=detected.get("cpu", {}).get("unit", "%"),
                    detected=detected.get("cpu", {}).get("detected", False)
                ),
                memory=KPIThreshold(
                    threshold=detected.get("memory", {}).get("threshold", 85.0),
                    unit=detected.get("memory", {}).get("unit", "%"),
                    detected=detected.get("memory", {}).get("detected", False)
                ),
                network=KPIThreshold(
                    threshold=detected.get("network", {}).get("threshold", 500.0),
                    unit=detected.get("network", {}).get("unit", "ms"),
                    detected=detected.get("network", {}).get("detected", False)
                ),
                database=KPIThreshold(
                    threshold=detected.get("database", {}).get("threshold", 1000.0),
                    unit=detected.get("database", {}).get("unit", "ms"),
                    detected=detected.get("database", {}).get("detected", False)
                ),
                disk_io=KPIThreshold(
                    threshold=detected.get("disk_io", {}).get("threshold", 20.0),
                    unit=detected.get("disk_io", {}).get("unit", "%"),
                    detected=detected.get("disk_io", {}).get("detected", False)
                ),
            )
    except Exception:
        pass
    
    # Return defaults
    return KPIConfig()


@router.post("", response_model=KPIConfig)
async def update_kpis(kpi_config: KPIConfig) -> KPIConfig:
    """Update KPI thresholds."""
    global _custom_kpis
    _custom_kpis = kpi_config
    return _custom_kpis


@router.get("/explain", response_model=KPIExplanation)
async def explain_kpis() -> KPIExplanation:
    """Get explanation of current KPIs."""
    kpis = await get_kpis()
    return KPIExplanation(kpis=kpis)

