"""Pydantic schemas shared across the API."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    stream: bool = True
    metadata: Optional[dict] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0",
    )
    confidence_level: Optional[Literal["low", "medium", "high"]] = Field(
        default=None,
        description="Binned confidence label derived from the numeric confidence score.",
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Optional follow-up questions presented to the user when confidence is low.",
    )


class StreamDelta(BaseModel):
    event: Literal["status", "trace", "token", "final"]
    payload: dict


class AgentRequest(BaseModel):
    """Request schema for agent endpoints."""
    prompt: str
    history: List[ChatMessage] = Field(default_factory=list)
    context: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response schema for agent endpoints."""
    response: str
    sources: List[str] = Field(default_factory=list)
    metadata: Optional[dict] = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")


class BottleneckReport(BaseModel):
    """Schema for individual bottleneck findings."""
    bottleneck_type: Literal["cpu", "memory", "network", "database", "disk_io", "application", "other"] = Field(
        description="Type of bottleneck identified"
    )
    severity: Literal["critical", "high", "medium", "low"] = Field(
        description="Severity level of the bottleneck"
    )
    description: str = Field(description="Description of the bottleneck")
    evidence: List[str] = Field(
        default_factory=list,
        description="Specific evidence from logs/metrics supporting this finding"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations to resolve the bottleneck"
    )


class PerformanceAnalysisResponse(BaseModel):
    """Extended response schema for performance analysis with structured bottleneck reports."""
    response: str
    sources: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0"
    )
    bottlenecks: List[BottleneckReport] = Field(
        default_factory=list,
        description="Structured bottleneck findings"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Additional metadata about the analysis"
    )


class KPIThreshold(BaseModel):
    """Schema for individual KPI threshold."""
    threshold: float = Field(description="Threshold value for this KPI")
    unit: str = Field(description="Unit of measurement (%, ms, s, etc.)")
    detected: bool = Field(default=False, description="Whether this was detected from logs")


class KPIConfig(BaseModel):
    """Schema for KPI configuration."""
    cpu: KPIThreshold = Field(default_factory=lambda: KPIThreshold(threshold=80.0, unit="%"))
    memory: KPIThreshold = Field(default_factory=lambda: KPIThreshold(threshold=85.0, unit="%"))
    network: KPIThreshold = Field(default_factory=lambda: KPIThreshold(threshold=500.0, unit="ms"))
    database: KPIThreshold = Field(default_factory=lambda: KPIThreshold(threshold=1000.0, unit="ms"))
    disk_io: KPIThreshold = Field(default_factory=lambda: KPIThreshold(threshold=20.0, unit="%"))


class KPIExplanation(BaseModel):
    """Schema for KPI explanation response."""
    kpis: KPIConfig
    explanations: dict[str, str] = Field(
        default_factory=lambda: {
            "cpu": "CPU usage threshold. Values above this indicate CPU bottlenecks.",
            "memory": "Memory usage threshold. Values above this indicate memory bottlenecks.",
            "network": "Network latency threshold. Values above this indicate network bottlenecks.",
            "database": "Database query time threshold. Values above this indicate database bottlenecks.",
            "disk_io": "Disk I/O wait threshold. Values above this indicate disk I/O bottlenecks.",
        },
        description="Explanations of what each KPI means"
    )


