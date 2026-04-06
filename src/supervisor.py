"""Supervisor node — entry point for the orchestration graph.

Receives user queries, delegates to routing, and aggregates final responses
when all needed agents have reported back.
"""

import structlog
from langchain_core.messages import AIMessage

from .routing import _is_multi_agent_query
from .state import OrchestratorState

log = structlog.get_logger()


def supervisor_node(state: OrchestratorState) -> dict:
    """Central hub — runs on every graph cycle.

    First call: initializes tracking, increments iteration counter.
    Subsequent calls: checks if aggregation is needed or if we're done.
    """
    iteration = state.get("iteration_count", 0)
    agent_responses = state.get("agent_responses", {})
    # always refer to the original user query, not the latest agent message
    query = state["messages"][0].content if state["messages"] else ""

    # first time through — just set up state
    if iteration == 0:
        return {
            "messages": [],
            "iteration_count": 1,
            "query_intent": _infer_intent(query),
        }

    # for multi-agent queries, check if all agents have reported
    if _is_multi_agent_query(query) and len(agent_responses) >= 3:
        summary = _aggregate_responses(agent_responses, query)
        return {
            "messages": [AIMessage(content=summary, name="supervisor")],
            "final_response": summary,
            "iteration_count": iteration + 1,
        }

    # single-agent query — if we got one response, we're done
    if not _is_multi_agent_query(query) and agent_responses:
        # pass through the agent's response as the final answer
        response_text = next(iter(agent_responses.values()))
        return {
            "messages": [AIMessage(content=response_text, name="supervisor")],
            "final_response": response_text,
            "iteration_count": iteration + 1,
        }

    return {"iteration_count": iteration + 1, "messages": []}


def _infer_intent(query: str) -> str:
    q_lower = query.lower()
    if _is_multi_agent_query(query):
        return "multi_agent_summary"

    # broad bucketing for telemetry, not for routing
    if any(kw in q_lower for kw in ("budget", "revenue", "expense", "cost")):
        return "financial_query"
    if any(kw in q_lower for kw in ("kpi", "sla", "incident", "capacity")):
        return "operational_query"
    if any(kw in q_lower for kw in ("roadmap", "timeline", "risk", "resource")):
        return "planning_query"
    return "general_query"


def _aggregate_responses(responses: dict, query: str) -> str:
    """Combine outputs from all specialist agents into an executive summary."""
    parts = ["**Executive Summary**\n"]
    parts.append(f"Query: {query}\n")
    parts.append("---\n")

    # TODO: use an LLM to synthesize a more natural summary for complex queries
    for domain, content in responses.items():
        parts.append(f"### {domain.title()}\n{content}\n")

    parts.append("---")
    parts.append(
        "*This summary aggregates reports from Finance, Operations, and Planning agents.*"
    )
    return "\n".join(parts)
