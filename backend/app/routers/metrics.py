"""Metrics endpoints exposing demo application performance data."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..data.demo_metrics import (
    Application,
    ApplicationDetails,
    get_application_details,
    list_applications,
)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/applications", response_model=list[Application])
async def list_demo_applications() -> list[Application]:
    """List demo applications with their latest summary metrics."""
    return list_applications()


@router.get("/applications/{app_id}", response_model=ApplicationDetails)
async def get_demo_application(app_id: str) -> ApplicationDetails:
    """Get detailed metrics for a specific application."""
    detail = get_application_details(app_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Application not found")
    return detail


