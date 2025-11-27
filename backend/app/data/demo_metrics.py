from __future__ import annotations

"""Demo performance metrics used to power the dashboard and analysis during hackathons."""

from datetime import datetime, timedelta
from typing import Dict, List, Literal

from pydantic import BaseModel


class TimePoint(BaseModel):
    timestamp: str
    value: float


Criticality = Literal["critical", "warning", "healthy"]


class Application(BaseModel):
    id: str
    name: str
    status: Criticality
    responseTime: float
    errorRate: float
    throughput: float
    lastChecked: str
    description: str


class ApplicationDetails(Application):
    metrics: Dict[str, List[TimePoint]]  # responseTime, errorRate, throughput


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


APPLICATIONS: List[Application] = [
    Application(
        id="1",
        name="Payment Processing API",
        status="critical",
        responseTime=2450,
        errorRate=8.5,
        throughput=1250,
        lastChecked=_now_iso(),
        description="Core payment processing service handling all transaction requests",
    ),
    Application(
        id="2",
        name="User Authentication Service",
        status="warning",
        responseTime=850,
        errorRate=2.1,
        throughput=5400,
        lastChecked=_now_iso(),
        description="Authentication and authorization service for all applications",
    ),
    Application(
        id="3",
        name="Inventory Management",
        status="critical",
        responseTime=3200,
        errorRate=12.3,
        throughput=800,
        lastChecked=_now_iso(),
        description="Real-time inventory tracking and management system",
    ),
    Application(
        id="4",
        name="Analytics Dashboard",
        status="healthy",
        responseTime=320,
        errorRate=0.3,
        throughput=2100,
        lastChecked=_now_iso(),
        description="Business intelligence and reporting dashboard",
    ),
    Application(
        id="5",
        name="Email Notification Service",
        status="warning",
        responseTime=1100,
        errorRate=3.8,
        throughput=3200,
        lastChecked=_now_iso(),
        description="Handles all email notifications and communications",
    ),
    Application(
        id="6",
        name="Search Engine API",
        status="healthy",
        responseTime=180,
        errorRate=0.5,
        throughput=8500,
        lastChecked=_now_iso(),
        description="Full-text search service across all products",
    ),
]


def _generate_series(base: float, variance: float, count: int = 24) -> List[TimePoint]:
    """Generate a simple synthetic time series around a base value."""
    now = datetime.utcnow()
    points: List[TimePoint] = []
    for i in range(count):
        ts = now - timedelta(hours=(count - i))
        # small deterministic wiggle so charts look alive but repeatable
        offset = ((i % 5) - 2) * variance * 0.08
        points.append(
            TimePoint(
                timestamp=ts.isoformat(),
                value=max(0.0, base + offset),
            )
        )
    return points


def list_applications() -> List[Application]:
    """Return all demo applications (used for /api/metrics/applications)."""
    return APPLICATIONS


def get_application(app_id: str) -> Application | None:
    return next((a for a in APPLICATIONS if a.id == app_id), None)


def get_application_details(app_id: str) -> ApplicationDetails | None:
    app = get_application(app_id)
    if not app:
        return None

    return ApplicationDetails(
        **app.dict(),
        metrics={
            "responseTime": _generate_series(app.responseTime, app.responseTime * 0.3),
            "errorRate": _generate_series(app.errorRate, app.errorRate * 0.4),
            "throughput": _generate_series(app.throughput, app.throughput * 0.2),
        },
    )


