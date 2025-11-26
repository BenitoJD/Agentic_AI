from typing import List, Literal, TypedDict
import logging

import httpx
import re
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from ..schemas import AgentRequest, ChatMessage, ChatRequest, ChatResponse
from ..services.agent_client import get_agent_client
from ..services.llm import get_llm
from ..config import settings


PLAN_TYPES = Literal[
    "direct",
    "rag_knowledge",
    "web_search",
    "time_location",
]


class AgentState(TypedDict, total=False):
    prompt: str
    history: List[ChatMessage]
    plan: PLAN_TYPES
    context: str
    sources: List[str]
    web_results: str
    finance_result: str
    response: str
    confidence: float
    preferred_sources: List[str]


SYSTEM_PROMPT = (
    "You are Nova, an assistant that can optionally ground answers in uploaded documents. "
    "When document snippets are available use them; when web results are available summarize them and cite origins. "
    "If no external context exists, answer from general knowledge and clarify limits when relevant."
)


# Confidence thresholds for bucketing numeric scores
# We treat anything below 0.7 as "low" so the model asks for clarification more often.
LOW_CONFIDENCE_THRESHOLD = 0.7
MEDIUM_CONFIDENCE_THRESHOLD = 0.9

PLANNER_PROMPT = (
    "Decide the best tool for the next response.\n"
    "Return ONLY one token:\n"
    "- 'rag_knowledge' if the question needs uploaded/contextual documents or knowledge base search.\n"
    "- 'web_search' if it needs fresh internet information, news, or real-time data.\n"
    "- 'time_location' if the user is asking for the current time or their (approximate) location.\n"
    "- 'direct' if the model can answer without external data or specialized tools."
)


def _llm_available() -> bool:
    return get_llm() is not None


def _build_history_messages(history: List[ChatMessage]) -> list:
    messages: list = []
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    return messages


def _invoke_llm(
    prompt: str,
    history: List[ChatMessage],
    context: str | None = None,
    web_results: str | None = None,
) -> str:
    llm = get_llm()
    if not llm:
        if context:
            return f"(LLM unavailable) Context snippets:\n{context}\n\nUser prompt: {prompt}"
        if web_results:
            return f"(LLM unavailable) Web search results:\n{web_results}\n\nUser prompt: {prompt}"
        return "(LLM unavailable right now.)"

    messages = [SystemMessage(content=SYSTEM_PROMPT), *_build_history_messages(history)]
    if context:
        messages.append(
            HumanMessage(
                content=(
                    "Use the following context snippets when helpful. "
                    "If they are irrelevant, say so.\n\n"
                    f"{context}"
                )
            )
        )
    if web_results:
        messages.append(
            HumanMessage(
                content=(
                    "Summarize or answer using the following web search results. "
                    "Always mention they came from an online search.\n\n"
                    f"{web_results}"
                )
            )
        )
    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)
    content = getattr(response, "content", None)
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if content:
        return str(content)
    return str(response)


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
    """Use the LLM planner alone to pick between rag_knowledge, web_search, and direct."""
    prompt = state.get("prompt", "")
    llm = get_llm()
    if not llm:
        # Fallback when no LLM is available: just answer directly.
        state["plan"] = "direct"
        return state

    history = _build_history_messages(state.get("history", []))
    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        *history[-4:],  # only last few turns
        HumanMessage(content=f"User query: {prompt}"),
    ]
    decision_raw = llm.invoke(messages)
    decision = str(getattr(decision_raw, "content", decision_raw)).strip().lower()

    token: PLAN_TYPES | None = None
    agent_keywords = {
        "rag_knowledge": ["rag_knowledge", "rag", "knowledge", "document", "file", "upload"],
        "web_search": ["web_search", "web", "search", "latest", "news", "online"],
        "time_location": ["time_location", "time location", "time & location"],
        "direct": "direct",
    }

    for agent_type, keywords in agent_keywords.items():
        if isinstance(keywords, list):
            if any(kw in decision for kw in keywords):
                token = agent_type
                break
        elif keywords in decision:
            token = agent_type
            break

    # If the user explicitly asks to access the internet or real-time data,
    # force the web_search plan regardless of the planner's token.
    prompt_lower = prompt.lower()
    if any(
        phrase in prompt_lower
        for phrase in (
            "access the internet",
            "access internet",
            "access the web",
            "real-time data",
            "real time data",
            "use the internet",
        )
    ):
        token = "web_search"

    # If the user asks about the current time or location, prefer the time_location tool.
    if any(
        phrase in prompt_lower
        for phrase in (
            "what time is it",
            "current time",
            "time now",
            "what's the time",
            "where am i",
            "my location",
            "current location",
        )
    ):
        token = "time_location"

    state["plan"] = token or "direct"
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


# Agent functions that call HTTP endpoints
async def _rag_knowledge_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("rag-knowledge", state)


async def _code_review_repo_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("code-review-repo", state)


async def _task_executor_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("task-executor", state)


async def _web_search_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("web-search", state)


async def _data_analysis_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("data-analysis", state)


async def _email_ticket_triage_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("email-ticket-triage", state)


async def _meeting_summarizer_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("meeting-summarizer", state)


async def _reasoning_reflection_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("reasoning-reflection", state)


async def _autonomous_research_agent(state: AgentState) -> AgentState:
    return await _call_agent_via_http("autonomous-research", state)


def _direct_agent(state: AgentState) -> AgentState:
    """Direct agent - uses LLM without external tools."""
    prompt = state.get("prompt", "")
    history = state.get("history", [])
    result = _invoke_llm(prompt, history)
    state["response"] = result
    state["context"] = ""
    state["sources"] = []
    state["confidence"] = 0.8  # Default confidence for direct responses
    return state


def _google_news_search(query: str) -> list[str]:
    import xml.etree.ElementTree as ET

    params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    try:
        resp = httpx.get("https://news.google.com/rss/search", params=params, timeout=5.0)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    snippets: list[str] = []
    for item in root.findall(".//item")[:5]:
        title_el = item.find("title")
        link_el = item.find("link")
        if title_el is not None and link_el is not None:
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            if title and link:
                snippets.append(f"{title} (Source: {link})")
    return snippets


def _duckduckgo_search(query: str) -> list[str]:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    try:
        resp = httpx.get("https://api.duckduckgo.com/", params=params, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    snippets: list[str] = []
    abstract = data.get("AbstractText")
    if abstract:
        snippets.append(f"Abstract: {abstract}")
    for topic in data.get("RelatedTopics", [])[:5]:
        if isinstance(topic, dict):
            text = topic.get("Text")
            url = topic.get("FirstURL")
            if text and url:
                snippets.append(f"{text} (Source: {url})")
    return snippets


def _web_search(query: str) -> str:
    snippets = _google_news_search(query)
    if not snippets:
        snippets = _duckduckgo_search(query)
    if not snippets:
        return "No helpful matches were found during the web search."
    return "\n".join(snippets)


def _web_agent(state: AgentState) -> AgentState:
    query = state.get("prompt", "")
    results = _web_search(query)
    state["web_results"] = results
    state["context"] = ""
    state["sources"] = []
    state["response"] = _invoke_llm(state.get("prompt", ""), state.get("history", []), web_results=results)
    return state


def _finance_agent(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "")
    result = _financial_calculator(prompt)
    state["finance_result"] = result
    state["context"] = ""
    state["sources"] = []
    state["response"] = result
    return state


def _employee_agent(state: AgentState) -> AgentState:
    query = state.get("prompt", "")
    records = search_employees(query)
    summary = format_employees(records)
    state["context"] = ""
    state["sources"] = []
    state["response"] = summary
    return state


def _bank_ops_agent(state: AgentState) -> AgentState:
    email = state.get("prompt", "")
    intent = _guess_intent(email)
    department = _route_department(intent, email)
    resolution = _suggest_resolution(intent)
    summary = (
        "Banking Ops Summary:\n"
        f"- Detected intent: {intent}\n"
        f"- Suggested department: {department}\n"
        f"- Proposed resolution: {resolution}\n"
        f"- Email excerpt: {email[:400]}{'...' if len(email) > 400 else ''}"
    )
    state["response"] = summary
    return state


def _fraud_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    amount_match = re.search(r"\$?([0-9]+(?:\.[0-9]+)?)", text)
    amount = amount_match.group(1) if amount_match else "unknown"
    risk_reason = _detect_fraud_pattern(text)
    notes = (
        "Fraud Assessment:\n"
        f"- Flagged amount: ${amount}\n"
        f"- Risk rationale: {risk_reason}\n"
        "- Recommended actions:\n"
        "  1. Temporarily hold the transaction/card.\n"
        "  2. Notify the customer for confirmation.\n"
        "  3. Create an investigation case with provided details.\n"
    )
    state["response"] = notes
    return state


def _loan_processing_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    income = _extract_currency(text, "income")
    credit_score = _extract_number(text, "credit")
    debt = _extract_currency(text, "debt")
    eligibility = _predict_loan_eligibility(income, credit_score, debt)
    summary = (
        "Loan Processing Summary:\n"
        f"- Income detected: {income or 'not found'}\n"
        f"- Credit score: {credit_score or 'not found'}\n"
        f"- Debt/obligations: {debt or 'not found'}\n"
        f"- Eligibility: {eligibility}\n"
    )
    state["response"] = summary
    return state


def _kyc_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    documents = _detect_documents(text)
    issues = _detect_kyc_issues(text)
    summary = (
        "KYC/AML Review:\n"
        f"- Documents referenced: {', '.join(documents) if documents else 'None detected'}\n"
        f"- Potential inconsistencies: {issues or 'None spotted'}\n"
        "- Next steps: request missing documents, verify ID numbers, and escalate if discrepancies persist."
    )
    state["response"] = summary
    return state


def _advisory_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    holdings = _parse_portfolio(text)
    suggestions = _advise_portfolio(holdings)
    summary = "Financial Advisory Report:\n"
    if holdings:
        summary += "- Current allocation:\n" + "\n".join(
            f"  - {symbol}: {weight}%" for symbol, weight in holdings.items()
        )
    else:
        summary += "- No structured allocation detected; treating input as free-form request.\n"
    summary += f"\n- Suggestions: {suggestions}"
    state["response"] = summary
    return state


# Retail & E-Commerce Agents
def _inventory_forecast_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Analyze inventory data and predict stockouts. Suggest reorder quantities. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Inventory Forecast:\n{result}"
    return state


def _complaint_triage_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    category = _classify_complaint(text)
    response_draft = _draft_complaint_response(category, text)
    state["response"] = f"Complaint Triage:\n- Category: {category}\n- Draft Response:\n{response_draft}"
    return state


def _catalog_optimize_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Enhance product descriptions, detect duplicates, suggest SEO-optimized titles. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Catalog Optimization:\n{result}"
    return state


def _price_comparison_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Compare competitor prices and suggest discount levels. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Price Comparison & Recommendation:\n{result}"
    return state


# Telecom & Network Agents
def _network_issue_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Analyze network logs, map errors, suggest root cause. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Network Issue Classification:\n{result}"
    return state


def _outage_prediction_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Detect patterns and early signals for potential outages. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Outage Prediction:\n{result}"
    return state


def _call_summary_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Convert call transcript to structured ticket with sentiment and urgency scoring. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Call Summary:\n{result}"
    return state


# Healthcare & Pharma Agents
def _claim_summarizer_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Read insurance claim form, extract diagnosis codes, flag inconsistencies. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Insurance Claim Summary:\n{result}"
    return state


def _medical_organizer_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Summarize discharge notes and classify by department. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Medical Document Organization:\n{result}"
    return state


def _pharma_research_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Perform literature review, compare drugs, summarize clinical trials. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Pharma Research:\n{result}"
    return state


# Manufacturing Agents
def _quality_defect_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Read QC reports and cluster defect patterns. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Quality Defect Analysis:\n{result}"
    return state


def _maintenance_prediction_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Detect frequent machine failures and suggest service windows. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Maintenance Prediction:\n{result}"
    return state


def _supplier_scorecard_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Rate vendors using delivery performance, delays, defects. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Supplier Scorecard:\n{result}"
    return state


# IT Services Agents
def _ticket_analysis_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Analyze incident description, identify root cause, suggest fix scripts. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Ticket Analysis:\n{result}"
    return state


def _code_review_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Find vulnerabilities and suggest patches. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Code Review & Bug Fix:\n{result}"
    return state


def _test_automation_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Generate Playwright/Selenium tests and create assertions. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Test Automation:\n{result}"
    return state


def _api_integration_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Read Postman collections, generate client SDK, create test cases. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"API Integration:\n{result}"
    return state


def _meeting_summarizer_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Extract decisions, action items, and assign owners. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Meeting Summary:\n{result}"
    return state


def _knowledge_base_agent(state: AgentState) -> AgentState:
    # Use RAG for knowledge base queries
    docs = search(state.get("prompt", ""), k=5)
    snippets: list[str] = []
    sources: list[str] = []
    for doc in docs:
        content = doc.page_content.strip()
        if not content:
            continue
        snippets.append(content)
        sources.append(doc.metadata.get("filename") or "KB Document")
    if snippets:
        context = "\n\n---\n\n".join(snippets)
        result = _invoke_llm(state.get("prompt", ""), state.get("history", []), context=context)
        state["sources"] = list(dict.fromkeys(sources))
    else:
        result = _invoke_llm(
            f"Answer from knowledge base or create structured SOP. Input: {state.get('prompt', '')}",
            state.get("history", []),
        )
        state["sources"] = []
    state["response"] = f"Knowledge Base Response:\n{result}"
    return state


# Enterprise Ops Agents
def _invoice_processing_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Process invoice with OCR, match PO, flag fraud. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Invoice Processing:\n{result}"
    return state


def _procurement_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Compare vendors and summarize contracts. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Procurement Assistant:\n{result}"
    return state


def _hr_query_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Answer leave policy questions and explain salary slips. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"HR Employee Query:\n{result}"
    return state


def _contract_summary_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Extract legal clauses and flag risks. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Contract Summary:\n{result}"
    return state


def _compliance_auditor_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Read policies and flag violations. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Compliance Audit:\n{result}"
    return state


# Developer Productivity Agents
def _repo_analyst_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Understand repo structure and create onboarding docs. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Repository Analysis:\n{result}"
    return state


def _migration_advisor_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Advise on migrations: .NET to .NET Core, Python 2 to 3, Angular to React. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Migration Advisor:\n{result}"
    return state


def _sql_optimization_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Rewrite slow queries and suggest indexes. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"SQL Optimization:\n{result}"
    return state


def _architecture_mapping_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Read microservice repos and generate architecture diagrams. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Architecture Mapping:\n{result}"
    return state


# Data & Analytics Agents
def _data_quality_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Detect missing values, duplicates, outliers. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Data Quality Report:\n{result}"
    return state


def _dashboard_generator_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Turn CSV data into insights and auto-build charts. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Dashboard Generator:\n{result}"
    return state


def _forecasting_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Forecast revenue, sales, demand. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Forecasting:\n{result}"
    return state


# Personal & Productivity Agents
def _life_assistant_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Help with reminders, summaries, plans. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Life Assistant:\n{result}"
    return state


def _career_assistant_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Rewrite resume, create roadmap, generate interview questions. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Career Assistant:\n{result}"
    return state


def _learning_assistant_agent(state: AgentState) -> AgentState:
    text = state.get("prompt", "")
    result = _invoke_llm(
        f"Create study notes, flashcards, MCQs. Input: {text}",
        state.get("history", []),
    )
    state["response"] = f"Learning Assistant:\n{result}"
    return state


def _time_location_agent(state: AgentState) -> AgentState:
    """Get current time and location information."""
    from datetime import datetime
    import time
    
    response_parts = []
    timezone = ""
    location_str = ""
    
    # Try to get time and location from worldtimeapi.org
    try:
        time_resp = httpx.get("https://worldtimeapi.org/api/ip", timeout=10.0)
        if time_resp.status_code == 200:
            time_data = time_resp.json()
            current_time = time_data.get("datetime", "")
            timezone = time_data.get("timezone", "")
            
            if current_time:
                try:
                    dt = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    response_parts.append(f"- Time: {formatted_time}")
                except Exception:
                    response_parts.append(f"- Time: {current_time}")
            
            if timezone:
                response_parts.append(f"- Timezone: {timezone}")
                # Extract location from timezone (e.g., "America/New_York" -> "New York, America")
                if "/" in timezone:
                    parts = timezone.split("/")
                    location_str = f"{parts[-1].replace('_', ' ')}, {parts[0]}" if len(parts) > 1 else timezone
                    response_parts.append(f"- Location: {location_str}")
    except Exception:
        pass  # Fallback to local time
    
    # Fallback to local time if API failed
    if not response_parts:
        try:
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            timezone_name = time.tzname[0] if time.tzname else "Local"
            response_parts.append(f"- Time: {formatted_time}")
            response_parts.append(f"- Timezone: {timezone_name}")
        except Exception:
            response_parts.append("- Time: Unable to determine")
    
    # Try to get detailed location from IP geolocation
    prompt_lower = state.get("prompt", "").lower()
    if "location" in prompt_lower or "where" in prompt_lower:
        try:
            ip_resp = httpx.get("https://ipapi.co/json/", timeout=10.0)
            if ip_resp.status_code == 200:
                ip_data = ip_resp.json()
                city = ip_data.get("city", "")
                region = ip_data.get("region", "")
                country = ip_data.get("country_name", "")
                if city or region or country:
                    detailed_location = ", ".join(filter(None, [city, region, country]))
                    response_parts.append(f"- Detailed Location: {detailed_location}")
        except Exception:
            pass  # Fallback to timezone-based location
    
    state["response"] = "Current Time & Location:\n" + "\n".join(response_parts) if response_parts else "Unable to fetch time and location information."
    state["context"] = ""
    state["sources"] = []
    return state


def _financial_calculator(prompt: str) -> str:
    """
    A simple expression evaluator for common financial calculations.
    Supports keywords: ROI, CAGR, compound interest, loan payment.
    """

    lower = prompt.lower()
    try:
        if "roi" in lower or "return on investment" in lower:
            # Expect format "roi initial=... final=..."
            import re

            initial_match = re.search(r"initial(?:ly)?\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            final_match = re.search(r"final(?:ly)?\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            if initial_match and final_match:
                initial = float(initial_match.group(1))
                final = float(final_match.group(1))
                if initial == 0:
                    return "Initial value cannot be zero for ROI."
                roi = ((final - initial) / initial) * 100
                return f"ROI is {roi:.2f}% based on initial {initial} and final {final}."
            return "Please provide both initial and final values for ROI."

        if "cagr" in lower:
            import re

            start_match = re.search(r"start(?:ing)?\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            end_match = re.search(r"end\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            years_match = re.search(r"(?:years|year)\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            if start_match and end_match and years_match:
                start = float(start_match.group(1))
                end = float(end_match.group(1))
                years = float(years_match.group(1))
                if start <= 0 or years <= 0:
                    return "Start value and years must be greater than zero."
                cagr = ((end / start) ** (1 / years) - 1) * 100
                return f"CAGR is {cagr:.2f}% over {years} years."
            return "Please provide start value, end value, and number of years for CAGR."

        if "compound" in lower and "interest" in lower:
            import re

            principal_match = re.search(r"principal\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            rate_match = re.search(r"rate\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            times_match = re.search(r"(?:times|frequency)\s*=?\s*([0-9]+)", lower)
            years_match = re.search(r"(?:years|year)\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            if principal_match and rate_match and times_match and years_match:
                principal = float(principal_match.group(1))
                rate = float(rate_match.group(1)) / 100
                times = float(times_match.group(1))
                years = float(years_match.group(1))
                amount = principal * (1 + rate / times) ** (times * years)
                return f"Compound interest amount is {amount:.2f} after {years} years."
            return "Please provide principal, rate, compounding frequency, and years."

        if "loan" in lower or "mortgage" in lower or "payment" in lower:
            import re

            principal_match = re.search(r"(?:loan|principal)\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            rate_match = re.search(r"rate\s*=?\s*([0-9]+(?:\.[0-9]+)?)", lower)
            term_match = re.search(r"(?:months|years)\s*=?\s*([0-9]+)", lower)
            term_unit = "years" if "years" in lower else "months"

            if principal_match and rate_match and term_match:
                principal = float(principal_match.group(1))
                rate = float(rate_match.group(1)) / 100
                periods = int(term_match.group(1))
                monthly_rate = rate / 12
                if term_unit == "years":
                    periods *= 12
                if monthly_rate == 0:
                    payment = principal / periods
                else:
                    payment = principal * (monthly_rate * (1 + monthly_rate) ** periods) / ((1 + monthly_rate) ** periods - 1)
                return f"Estimated monthly payment is {payment:.2f}."
            return "Please provide loan amount, interest rate, and term (months or years)."

        # Fallback: rely on LLM to explain we can't compute it.
        return "I couldn't parse the financial calculation. Please provide a clearer format."
    except Exception as exc:  # pragma: no cover - defensive
        return f"Financial calculator encountered an error: {exc}"


def _guess_intent(text: str) -> str:
    lower = text.lower()
    if "card" in lower or "debit" in lower or "credit" in lower:
        return "Card issue"
    if "wire" in lower or "transfer" in lower:
        return "Wire transfer support"
    if "statement" in lower or "balance" in lower:
        return "Statement inquiry"
    if "account close" in lower or "closure" in lower:
        return "Account closure request"
    return "General banking inquiry"


def _route_department(intent: str, text: str) -> str:
    lower = text.lower()
    if "card" in lower or "fraud" in lower:
        return "Card Operations"
    if "loan" in lower or "mortgage" in lower:
        return "Lending"
    if "wire" in lower or "transfer" in lower:
        return "Payments"
    if "statement" in lower or "balance" in lower:
        return "Customer Support"
    if "complaint" in lower:
        return "Customer Advocacy"
    return "General Support"


def _suggest_resolution(intent: str) -> str:
    mapping = {
        "Card issue": "Verify identity, reissue card if necessary, and monitor for fraud.",
        "Wire transfer support": "Confirm transfer details, verify authorization, and provide tracking status.",
        "Statement inquiry": "Send the requested statement securely and explain recent transactions if needed.",
        "Account closure request": "Authenticate customer, ensure no pending items, and confirm closure timeline.",
    }
    return mapping.get(intent, "Review the case details and follow SOP to resolve the issue.")


def _detect_fraud_pattern(text: str) -> str:
    lower = text.lower()
    if "multiple" in lower and "location" in lower:
        return "Multiple-location usage detected."
    if "large" in lower or "high value" in lower:
        return "High-value transaction outside normal pattern."
    if "midnight" in lower or "late night" in lower:
        return "Off-hours transaction flagged."
    if "unknown merchant" in lower:
        return "Unrecognized merchant usage."
    return "Behavior deviates from historical spending."


def _extract_currency(text: str, label: str) -> str | None:
    pattern = re.compile(rf"{label}[^0-9]*\$?([0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        raw = match.group(1).replace(",", "")
        value = float(raw)
        return f"${value:,.0f}"
    return None


def _extract_number(text: str, label: str) -> str | None:
    pattern = re.compile(rf"{label}[^0-9]*([0-9]{{3,4}})", re.IGNORECASE)
    match = pattern.search(text)
    return match.group(1) if match else None


def _predict_loan_eligibility(income: str | None, credit_score: str | None, debt: str | None) -> str:
    income_value = _parse_number(income)
    credit_value = int(credit_score) if credit_score and credit_score.isdigit() else None
    debt_value = _parse_number(debt)

    if income_value is None or credit_value is None:
        return "Insufficient data - need income and credit score."

    debt_to_income = (debt_value / income_value) if (debt_value and income_value) else 0
    if credit_value >= 720 and income_value >= 60000 and debt_to_income < 0.35:
        return "Likely eligible for prime products."
    if credit_value >= 650 and income_value >= 40000 and debt_to_income < 0.45:
        return "Eligible with conditions (manual review)."
    return "Low eligibility - suggest improving credit or reducing debt."


def _parse_number(value: str | None) -> float | None:
    if not value:
        return None
    digits = re.sub(r"[^\d.]", "", value)
    try:
        return float(digits)
    except ValueError:
        return None


def _detect_documents(text: str) -> list[str]:
    docs = []
    lower = text.lower()
    mapping = {
        "passport": "Passport",
        "driver": "Driver License",
        "license": "Driver License",
        "id card": "Government ID",
        "utility": "Utility Bill",
        "statement": "Bank Statement",
    }
    for key, value in mapping.items():
        if key in lower:
            docs.append(value)
    return sorted(set(docs))


def _detect_kyc_issues(text: str) -> str | None:
    lower = text.lower()
    issues = []
    if "expired" in lower:
        issues.append("Provided ID appears expired.")
    if "mismatch" in lower or "different" in lower:
        issues.append("Name/address mismatch detected.")
    if "missing" in lower:
        issues.append("Customer indicates missing documents.")
    if not issues:
        return None
    return " ".join(issues)


def _parse_portfolio(text: str) -> dict[str, float]:
    holdings: dict[str, float] = {}
    for symbol, weight in re.findall(r"([A-Z]{1,5})\s+(\d{1,3})%", text):
        holdings[symbol] = float(weight)
    return holdings


def _advise_portfolio(holdings: dict[str, float]) -> str:
    if not holdings:
        return (
            "Consider providing a structured breakdown (ticker + percentage) so I can offer targeted allocation advice."
        )
    total = sum(holdings.values())
    advice_parts: list[str] = []
    if total and abs(total - 100) > 5:
        advice_parts.append("Rebalance so total allocation is closer to 100%.")
    equity = sum(weight for symbol, weight in holdings.items() if symbol not in {"BND", "AGG"})
    fixed_income = total - equity
    if equity > 70:
        advice_parts.append("Equity overweight; consider shifting 10-15% into bonds or cash.")
    elif fixed_income > 40:
        advice_parts.append("Portfolio is defensively positioned; ensure equity exposure matches growth goals.")
    if "CASH" not in holdings and total >= 95:
        advice_parts.append("Keep 5% cash buffer for opportunities or expenses.")
    if not advice_parts:
        advice_parts.append("Allocation looks balanced. Continue periodic reviews and automatic rebalancing.")
    return " ".join(advice_parts)


def _classify_complaint(text: str) -> str:
    lower = text.lower()
    if any(kw in lower for kw in ("refund", "money back", "return payment")):
        return "Refund"
    if any(kw in lower for kw in ("delivery", "shipping", "late", "not received")):
        return "Delivery"
    if any(kw in lower for kw in ("damaged", "broken", "defective", "cracked")):
        return "Damaged"
    if any(kw in lower for kw in ("quality", "poor quality", "not as described", "defect")):
        return "Quality"
    return "General"


def _draft_complaint_response(category: str, text: str) -> str:
    templates = {
        "Refund": "We apologize for the inconvenience. We'll process your refund within 5-7 business days.",
        "Delivery": "We're sorry for the delivery delay. We'll investigate and provide an update within 24 hours.",
        "Damaged": "We apologize for the damaged item. We'll send a replacement immediately.",
        "Quality": "Thank you for the feedback. We'll review this and improve our quality control.",
    }
    return templates.get(category, "We'll investigate your concern and respond promptly.")


def _route_plan(state: AgentState) -> str:
    plan = state.get("plan", "direct")
    routing_map = {
        "rag_knowledge": "rag_knowledge",
        "web_search": "web_search",
        "time_location": "time_location",
    }
    return routing_map.get(plan, "direct")


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", _plan)

    # Core agents we keep
    graph.add_node("rag_knowledge_agent", _rag_knowledge_agent)
    graph.add_node("web_search_agent", _web_search_agent)
    graph.add_node("time_location_agent", _time_location_agent)
    graph.add_node("direct_agent", _direct_agent)

    graph.set_entry_point("plan")
    graph.add_conditional_edges(
        "plan",
        _route_plan,
        {
            "rag_knowledge": "rag_knowledge_agent",
            "web_search": "web_search_agent",
            "time_location": "time_location_agent",
            "direct": "direct_agent",
        },
    )
    
    # After any agent finishes, we are done for this turn.
    # The planner will be re-run on the next user message if needed.
    all_agents = [
        "rag_knowledge_agent",
        "web_search_agent",
        "time_location_agent",
        "direct_agent",
    ]
    for agent in all_agents:
        graph.add_edge(agent, END)

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
            "plan": "direct",
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

