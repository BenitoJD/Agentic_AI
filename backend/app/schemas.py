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


