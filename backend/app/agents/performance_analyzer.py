"""Performance Analysis Agent - Analyzes logs and metrics to identify bottlenecks."""

from __future__ import annotations

import json
import re
from typing import Any

from ..schemas import AgentRequest, AgentResponse
from ..services.llm import get_llm
from ..services.vector_store import search_with_scores, list_files
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


SYSTEM_PROMPT = (
    "You are a performance engineering specialist that analyzes logs and metrics data to identify application bottlenecks. "
    "You excel at detecting patterns in performance data including:\n"
    "- CPU bottlenecks (high CPU usage, CPU-bound operations)\n"
    "- Memory bottlenecks (memory leaks, high memory usage, OOM errors)\n"
    "- Network bottlenecks (slow network calls, timeouts, connection issues)\n"
    "- Database bottlenecks (slow queries, connection pool exhaustion, lock contention)\n"
    "- Disk I/O bottlenecks (slow disk operations, high I/O wait)\n"
    "- Application-level bottlenecks (slow API endpoints, inefficient algorithms)\n\n"
    "IMPORTANT: Always start your response with a concise EXECUTIVE SUMMARY (1-2 sentences max) that provides:\n"
    "- Total number of bottlenecks found\n"
    "- Top critical issue identified\n"
    "- Overall system health assessment (healthy/at-risk/critical)\n\n"
    "After the executive summary, provide a BULLETED LIST of bottlenecks with only essential info:\n"
    "- Format: [Type] [Severity] - [Brief description] - [Key metric/evidence]\n"
    "- Keep each bottleneck to one line\n"
    "- Focus on actionable insights only\n"
    "Do not provide detailed analysis sections - keep it concise and scannable for human review."
)


def _build_history_messages(history):
    messages = []
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    return messages


def _parse_log_file(text: str) -> dict[str, Any]:
    """Extract structured information from log files."""
    lines = text.split("\n")
    parsed = {
        "total_lines": len(lines),
        "error_count": 0,
        "warning_count": 0,
        "error_messages": [],
        "performance_indicators": [],
        "timestamps": [],
    }
    
    # Common log patterns
    error_patterns = [
        r"(?i)error",
        r"(?i)exception",
        r"(?i)failed",
        r"(?i)fatal",
        r"(?i)critical",
    ]
    
    perf_patterns = [
        r"(?i)(?:latency|response time|duration|elapsed|took)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(?:ms|s|sec)",
        r"(?i)(?:cpu|memory|ram|disk)\s*(?:usage|utilization)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
        r"(?i)(?:throughput|requests?/s|qps)\s*[:=]\s*(\d+(?:\.\d+)?)",
        r"(?i)(?:timeout|timed out)",
        r"(?i)(?:slow|sluggish|performance)",
    ]
    
    timestamp_pattern = r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}"
    
    for line in lines:
        line_lower = line.lower()
        
        # Count errors
        if any(re.search(pattern, line) for pattern in error_patterns):
            parsed["error_count"] += 1
            if len(parsed["error_messages"]) < 10:  # Keep first 10 errors
                parsed["error_messages"].append(line.strip()[:200])
        
        # Count warnings
        if "warning" in line_lower or "warn" in line_lower:
            parsed["warning_count"] += 1
        
        # Extract performance indicators
        for pattern in perf_patterns:
            match = re.search(pattern, line)
            if match:
                parsed["performance_indicators"].append(line.strip()[:200])
                break
        
        # Extract timestamps
        if re.search(timestamp_pattern, line):
            ts_match = re.search(timestamp_pattern, line)
            if ts_match and len(parsed["timestamps"]) < 5:
                parsed["timestamps"].append(ts_match.group())
    
    return parsed


def _parse_json_metrics(text: str) -> dict[str, Any]:
    """Extract structured information from JSON metrics."""
    parsed = {
        "metrics": {},
        "data_points": 0,
        "time_series": False,
    }
    
    try:
        data = json.loads(text)
        
        if isinstance(data, list):
            parsed["data_points"] = len(data)
            if len(data) > 0 and isinstance(data[0], dict):
                parsed["metrics"] = data[0]
        elif isinstance(data, dict):
            parsed["data_points"] = 1
            parsed["metrics"] = data
            
            # Check for time series data
            if "timestamp" in data or "time" in data:
                parsed["time_series"] = True
    except json.JSONDecodeError:
        # Try to extract JSON-like structures from text
        json_objects = re.findall(r"\{[^{}]*\}", text)
        if json_objects:
            try:
                data = json.loads(json_objects[0])
                parsed["metrics"] = data
                parsed["data_points"] = len(json_objects)
            except json.JSONDecodeError:
                pass
    
    return parsed


def _parse_csv_metrics(text: str) -> dict[str, Any]:
    """Extract structured information from CSV metrics."""
    lines = text.split("\n")
    parsed = {
        "rows": len([l for l in lines if l.strip()]),
        "columns": [],
        "numeric_columns": [],
    }
    
    if lines:
        # Try to parse header
        header = lines[0].split(",")
        parsed["columns"] = [col.strip() for col in header]
        
        # Sample a few rows to identify numeric columns
        sample_rows = lines[1:min(6, len(lines))]
        for row in sample_rows:
            values = row.split(",")
            for i, val in enumerate(values):
                if i < len(parsed["columns"]):
                    try:
                        float(val.strip())
                        if parsed["columns"][i] not in parsed["numeric_columns"]:
                            parsed["numeric_columns"].append(parsed["columns"][i])
                    except ValueError:
                        pass
    
    return parsed


def _detect_kpis_from_logs(snippets: list[str], parsed_data: dict[str, Any]) -> dict[str, Any]:
    """Detect KPI thresholds from log and metrics data."""
    kpis = {
        "cpu": {"threshold": 80.0, "unit": "%", "detected": False},
        "memory": {"threshold": 85.0, "unit": "%", "detected": False},
        "network": {"threshold": 500.0, "unit": "ms", "detected": False},
        "database": {"threshold": 1000.0, "unit": "ms", "detected": False},
        "disk_io": {"threshold": 20.0, "unit": "%", "detected": False},
    }
    
    cpu_values = []
    memory_values = []
    network_values = []
    db_values = []
    disk_values = []
    
    # Patterns for extracting metrics
    cpu_patterns = [
        r"(?i)(?:cpu|processor)\s*(?:usage|utilization|load)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
        r"(?i)(?:cpu)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
    ]
    
    memory_patterns = [
        r"(?i)(?:memory|ram|mem)\s*(?:usage|utilization|used)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
        r"(?i)(?:memory)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
    ]
    
    network_patterns = [
        r"(?i)(?:latency|response\s*time|network\s*delay)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(?:ms|milliseconds?)",
        r"(?i)(?:duration|elapsed|took)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(?:ms|milliseconds?)",
    ]
    
    db_patterns = [
        r"(?i)(?:query\s*time|db\s*time|database\s*time|sql\s*time)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(?:ms|s|sec|milliseconds?|seconds?)",
        r"(?i)(?:execution\s*time)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(?:ms|s|sec)",
    ]
    
    disk_patterns = [
        r"(?i)(?:disk|i/o|io)\s*(?:usage|utilization|wait)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
        r"(?i)(?:iowait)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%",
    ]
    
    # Extract values from all snippets
    all_text = "\n".join(snippets)
    
    for pattern in cpu_patterns:
        matches = re.findall(pattern, all_text)
        for match in matches:
            try:
                cpu_values.append(float(match))
            except ValueError:
                pass
    
    for pattern in memory_patterns:
        matches = re.findall(pattern, all_text)
        for match in matches:
            try:
                memory_values.append(float(match))
            except ValueError:
                pass
    
    for pattern in network_patterns:
        matches = re.findall(pattern, all_text)
        for match in matches:
            try:
                network_values.append(float(match))
            except ValueError:
                pass
    
    for pattern in db_patterns:
        matches = re.findall(pattern, all_text)
        for match in matches:
            try:
                val = float(match)
                # Convert seconds to milliseconds if needed
                if val < 100:  # Likely already in seconds
                    val = val * 1000
                db_values.append(val)
            except ValueError:
                pass
    
    for pattern in disk_patterns:
        matches = re.findall(pattern, all_text)
        for match in matches:
            try:
                disk_values.append(float(match))
            except ValueError:
                pass
    
    # Calculate thresholds using p95 percentile
    def calc_threshold(values: list[float], default: float) -> tuple[float, bool]:
        if len(values) >= 5:
            sorted_vals = sorted(values)
            p95_idx = int(len(sorted_vals) * 0.95)
            threshold = sorted_vals[p95_idx] if p95_idx < len(sorted_vals) else sorted_vals[-1]
            return (threshold, True)
        return (default, False)
    
    if cpu_values:
        threshold, detected = calc_threshold(cpu_values, 80.0)
        kpis["cpu"]["threshold"] = threshold
        kpis["cpu"]["detected"] = detected
    
    if memory_values:
        threshold, detected = calc_threshold(memory_values, 85.0)
        kpis["memory"]["threshold"] = threshold
        kpis["memory"]["detected"] = detected
    
    if network_values:
        threshold, detected = calc_threshold(network_values, 500.0)
        kpis["network"]["threshold"] = threshold
        kpis["network"]["detected"] = detected
    
    if db_values:
        threshold, detected = calc_threshold(db_values, 1000.0)
        kpis["database"]["threshold"] = threshold
        kpis["database"]["detected"] = detected
    
    if disk_values:
        threshold, detected = calc_threshold(disk_values, 20.0)
        kpis["disk_io"]["threshold"] = threshold
        kpis["disk_io"]["detected"] = detected
    
    return kpis


def _invoke_llm(prompt: str, history, context: str | None = None, parsed_data: dict[str, Any] | None = None) -> str:
    llm = get_llm()
    if not llm:
        if context:
            return f"(LLM unavailable) Context snippets:\n{context}\n\nUser prompt: {prompt}"
        return "(LLM unavailable right now.)"

    messages = [SystemMessage(content=SYSTEM_PROMPT), *_build_history_messages(history)]
    
    # Add parsed data summary if available
    if parsed_data:
        summary_parts = []
        if "total_lines" in parsed_data:
            summary_parts.append(f"Log file analysis: {parsed_data.get('total_lines', 0)} lines, "
                               f"{parsed_data.get('error_count', 0)} errors, "
                               f"{parsed_data.get('warning_count', 0)} warnings")
        if "data_points" in parsed_data:
            summary_parts.append(f"Metrics data: {parsed_data.get('data_points', 0)} data points")
        if summary_parts:
            messages.append(HumanMessage(content=f"Data summary: {'; '.join(summary_parts)}"))
        
        # Add KPI thresholds if available
        if "kpi_thresholds" in parsed_data:
            messages.append(HumanMessage(content=parsed_data["kpi_thresholds"]))
    
    if context:
        messages.append(
            HumanMessage(
                content=(
                    "Use the following log/metrics data when analyzing for bottlenecks. "
                    "Focus on patterns that indicate performance issues.\n\n"
                    f"{context}"
                )
            )
        )
    
    # Enhance prompt to explicitly request concise executive summary and list format
    enhanced_prompt = (
        f"{prompt}\n\n"
        "IMPORTANT: Format your response as follows:\n"
        "1. Executive Summary (1-2 sentences): Total bottlenecks, top critical issue, system health\n"
        "2. Bottleneck List (bulleted): [Type] [Severity] - [Brief description] - [Key metric]\n"
        "Keep it concise and scannable. No detailed sections."
    )
    messages.append(HumanMessage(content=enhanced_prompt))
    response = llm.invoke(messages)
    content = getattr(response, "content", None)
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if content:
        return str(content)
    return str(response)


async def execute_agent(request: AgentRequest) -> AgentResponse:
    """Execute Performance Analysis Agent - analyzes logs and metrics for bottlenecks."""
    try:
        base_query = (request.prompt or "").strip()
        lower = base_query.lower()
        
        # Special case: user asking what files are available
        list_intent_phrases = [
            "what files do we have",
            "what logs do we have",
            "what metrics do we have",
            "which files have i uploaded",
            "list my files",
            "list uploaded files",
        ]
        if any(phrase in lower for phrase in list_intent_phrases):
            indexed = list_files()
            if not indexed:
                return AgentResponse(
                    response=(
                        "I don't see any log or metrics files uploaded yet.\n\n"
                        "You can upload log files (.log, .txt), JSON metrics files, or CSV metrics files "
                        "from the Uploads page, and I'll analyze them for performance bottlenecks."
                    ),
                    sources=[],
                    confidence=0.9,
                )

            lines = ["Here are the files I currently have indexed:\n"]
            for item in indexed:
                filename = item.get("filename") or "Unknown"
                chunks = item.get("chunks", 0)
                file_type = "log" if any(ext in filename.lower() for ext in [".log", ".txt"]) else "metrics"
                lines.append(f"- {filename} ({file_type}, {chunks} chunks)")
            summary = "\n".join(lines)
            return AgentResponse(
                response=summary,
                sources=[item.get("filename") or "Unknown" for item in indexed],
                confidence=0.95,
            )

        # Build a conversation-aware retrieval query
        last_user = None
        last_assistant = None
        if request.history:
            for msg in reversed(request.history):
                if not last_user and msg.role == "user":
                    last_user = msg
                elif not last_assistant and msg.role == "assistant":
                    last_assistant = msg
                if last_user and last_assistant:
                    break
        
        retrieval_parts = []
        if last_user:
            retrieval_parts.append(f"Previous question: {last_user.content}")
        if last_assistant:
            retrieval_parts.append(f"Previous analysis: {last_assistant.content}")
        retrieval_parts.append(f"Current question: {base_query}")
        retrieval_query = "\n".join(retrieval_parts)

        # Search for relevant log/metrics data
        docs_with_scores = search_with_scores(retrieval_query, k=10)
        snippets: list[str] = []
        sources: list[str] = []
        scores: list[float] = []
        parsed_data_summary: dict[str, Any] = {}

        preferred_sources = set()
        if request.metadata and isinstance(request.metadata, dict):
            preferred = request.metadata.get("preferred_sources") or []
            if isinstance(preferred, list):
                preferred_sources = {str(name) for name in preferred}

        if preferred_sources:
            filtered = []
            for doc, score in docs_with_scores:
                filename = doc.metadata.get("filename") or "Uploaded file"
                if filename in preferred_sources:
                    filtered.append((doc, score))
            if filtered:
                docs_with_scores = filtered

        # Parse and analyze each document
        for doc, score in docs_with_scores:
            content = doc.page_content.strip()
            if not content:
                continue
            
            filename = doc.metadata.get("filename") or "Uploaded file"
            file_type = doc.metadata.get("file_type", "unknown")
            
            # Parse based on file type
            if file_type == "log" or any(ext in filename.lower() for ext in [".log", ".txt"]):
                parsed = _parse_log_file(content)
                parsed_data_summary.update(parsed)
            elif file_type == "json" or filename.lower().endswith(".json"):
                parsed = _parse_json_metrics(content)
                parsed_data_summary.update(parsed)
            elif file_type == "csv" or filename.lower().endswith(".csv"):
                parsed = _parse_csv_metrics(content)
                parsed_data_summary.update(parsed)
            
            snippets.append(content)
            sources.append(filename)
            similarity = max(0.0, min(1.0, 1.0 - abs(score)))
            scores.append(similarity)

        if not snippets:
            # Fallback to direct answer if no files are available
            result = _invoke_llm(
                "Analyze the following for performance bottlenecks: " + base_query,
                request.history
            )
            return AgentResponse(response=result, sources=[], confidence=0.3)

        # Calculate confidence based on average similarity and data quality
        avg_similarity = sum(scores) / len(scores) if scores else 0.0
        doc_count_factor = min(1.0, len(snippets) / 5.0)  # Max boost at 5+ docs
        
        # Boost confidence if we have structured data
        data_quality_factor = 0.0
        if parsed_data_summary.get("error_count", 0) > 0:
            data_quality_factor += 0.1
        if parsed_data_summary.get("performance_indicators"):
            data_quality_factor += 0.1
        if parsed_data_summary.get("metrics"):
            data_quality_factor += 0.1
        
        confidence = min(1.0, avg_similarity * 0.6 + doc_count_factor * 0.2 + data_quality_factor)

        context = "\n\n---\n\n".join(snippets[:8])  # Limit to first 8 snippets
        
        # Detect KPIs from logs
        detected_kpis = _detect_kpis_from_logs(snippets, parsed_data_summary)
        
        # Use custom KPIs from metadata if provided, otherwise use detected/defaults
        custom_kpis = None
        if request.metadata and isinstance(request.metadata, dict):
            custom_kpis = request.metadata.get("kpis")
        
        kpis_to_use = custom_kpis if custom_kpis else detected_kpis
        
        # Pass KPIs to LLM in context
        kpi_context = ""
        if kpis_to_use:
            kpi_lines = ["KPI Thresholds for bottleneck detection:"]
            for kpi_type, kpi_data in kpis_to_use.items():
                threshold = kpi_data.get("threshold", 0)
                unit = kpi_data.get("unit", "")
                detected = kpi_data.get("detected", False)
                source = "detected from logs" if detected else "default"
                kpi_lines.append(f"- {kpi_type.upper()}: {threshold}{unit} ({source})")
            kpi_context = "\n".join(kpi_lines)
        
        # Add KPI context to parsed_data for LLM
        if kpi_context:
            parsed_data_summary["kpi_thresholds"] = kpi_context
        
        result = _invoke_llm(base_query, request.history, context=context, parsed_data=parsed_data_summary)
        unique_sources = list(dict.fromkeys(sources))
        
        # Include detected KPIs in response metadata
        response_metadata = {"detected_kpis": detected_kpis}
        
        return AgentResponse(
            response=result, 
            sources=unique_sources, 
            confidence=confidence,
            metadata=response_metadata
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in performance analyzer agent: {e}", exc_info=True)
        return AgentResponse(
            response=f"I encountered an error while analyzing performance data: {str(e)}. Please try again or rephrase your question.",
            sources=[],
            confidence=0.1
        )

