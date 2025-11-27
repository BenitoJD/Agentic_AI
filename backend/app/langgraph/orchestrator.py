from typing import List, Literal, TypedDict
import logging

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from ..schemas import AgentRequest, ChatMessage, ChatRequest, ChatResponse
from ..services.agent_client import get_agent_client
from ..services.llm import get_llm


PLAN_TYPES = Literal[
    "performance_analysis",
]


class AgentState(TypedDict, total=False):
    prompt: str
    history: List[ChatMessage]
    plan: PLAN_TYPES
    context: str
    sources: List[str]
    response: str
    confidence: float
    preferred_sources: List[str]


SYSTEM_PROMPT = (
    "You are a performance engineering assistant that analyzes logs and metrics to identify application bottlenecks. "
    "You help performance engineers quickly diagnose performance issues by interpreting log files and metrics data."
)


# Confidence thresholds for bucketing numeric scores
# We treat anything below 0.7 as "low" so the model asks for clarification more often.
LOW_CONFIDENCE_THRESHOLD = 0.7
MEDIUM_CONFIDENCE_THRESHOLD = 0.9

def _build_history_messages(history: List[ChatMessage]) -> list:
    messages: list = []
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    return messages




def _compute_confidence_level(score: float | None) -> str | None:
    """Map a numeric confidence score into a coarse label."""
    if score is None:
        return None
    if score < LOW_CONFIDENCE_THRESHOLD:
        return "low"
    if score < MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "high"


async def _build_follow_up_questions(
    prompt: str,
    history: List[ChatMessage],
    max_questions: int = 3,
) -> list[str]:
    """
    Ask the LLM for a few short clarifying questions to improve answer quality.

    The helper is intentionally defensive: if anything fails, it simply returns an empty list.
    """
    llm = get_llm()
    if not llm:
        return []

    try:
        messages = [
            SystemMessage(
                content=(
                    "You are helping improve answer quality by asking clarifying questions.\n"
                    "Given the user's last query and recent conversation, generate "
                    f"{max_questions} SHORT clarifying questions that would help you answer better.\n"
                    "Return ONLY the list of questions, one per line, without numbering or extra text."
                )
            ),
            *_build_history_messages(history)[-4:],
            HumanMessage(content=f"User query: {prompt}"),
        ]
        result = llm.invoke(messages)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        else:
            text = str(content or "")

        # Split into non-empty lines and take up to max_questions
        questions = [line.strip(" -\t") for line in text.splitlines()]
        questions = [q for q in questions if q]
        return questions[:max_questions]
    except Exception:
        # If generating follow-ups fails for any reason, just fall back gracefully.
        return []


def _plan(state: AgentState) -> AgentState:
    """Route all queries to performance analysis."""
    state["plan"] = "performance_analysis"
    return state


async def _call_agent_via_http(agent_name: str, state: AgentState) -> AgentState:
    """Call an agent via HTTP and update state with response."""
    client = get_agent_client()
    request = AgentRequest(
        prompt=state.get("prompt", ""),
        history=state.get("history", []),
        context=state.get("context"),
        metadata={"preferred_sources": state.get("preferred_sources", [])},
    )
    try:
        response = await client.call_agent(agent_name, request)
        state["response"] = response.response
        state["sources"] = response.sources
        state["confidence"] = response.confidence
    except httpx.HTTPError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"HTTP error calling agent {agent_name}: {e}", exc_info=True)
        error_msg = f"Error calling agent {agent_name}"
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json().get("detail", str(e))
                error_msg = f"{error_msg}: {error_detail}"
            except Exception:
                error_msg = f"{error_msg}: {e.response.text if hasattr(e.response, 'text') else str(e)}"
        state["response"] = error_msg
        state["sources"] = []
        state["confidence"] = 0.0
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error calling agent {agent_name}: {e}", exc_info=True)
        state["response"] = f"Error calling agent {agent_name}: {str(e)}"
        state["sources"] = []
        state["confidence"] = 0.0
    state["context"] = ""
    return state


# Performance analysis agent
async def _performance_analysis_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("performance-analyzer", state)


def _route_plan(state: AgentState) -> str:
    plan = state.get("plan", "performance_analysis")
    return "performance_analysis"


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", _plan)
    graph.add_node("performance_analysis_agent", _performance_analysis_agent)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "performance_analysis_agent")
    graph.add_edge("performance_analysis_agent", END)

    return graph.compile()


class ChatOrchestrator:
    def __init__(self) -> None:
        self.graph = _build_graph()

    @staticmethod
    def _initial_state(request: ChatRequest) -> AgentState:
        metadata = getattr(request, "metadata", None) or {}
        preferred_sources = metadata.get("lastSources") or []
        return {
            "prompt": request.message,
            "history": request.history or [],
            "plan": "performance_analysis",
            "context": "",
            "sources": [],
            "response": "",
            "confidence": 0.8,
            "preferred_sources": preferred_sources,
        }

    async def run_chat(self, request: ChatRequest) -> ChatResponse:
        final_state = await self.graph.ainvoke(self._initial_state(request))

        response_text = final_state.get("response", "") or ""
        sources = final_state.get("sources", []) or []
        confidence = final_state.get("confidence")

        # Derive coarse confidence band from numeric score (if any)
        confidence_level = _compute_confidence_level(confidence)

        # Treat very short or ambiguous prompts as low confidence, to force clarifications.
        prompt_text = request.message.strip()
        word_count = len(prompt_text.split())
        if word_count <= 2:
            confidence_level = "low"

        follow_up_questions: list[str] = []
        # When confidence is low, try to enrich the response with follow-up questions
        if confidence is not None and confidence_level == "low":
            follow_up_questions = await _build_follow_up_questions(
                prompt=final_state.get("prompt", request.message),
                history=final_state.get("history", request.history or []),
            )

        return ChatResponse(
            response=response_text,
            sources=sources,
            confidence=confidence,
            confidence_level=confidence_level,
            follow_up_questions=follow_up_questions,
        )

