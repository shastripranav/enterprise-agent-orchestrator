"""Hybrid routing — keyword rules for fast deterministic routing, LLM fallback for ambiguity.

This is the key differentiator of the orchestrator. Rule-based routing avoids an LLM
call entirely for common query patterns, reducing latency and API costs. The LLM is
only invoked when keyword scoring is tied or too weak to make a confident decision.
"""

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from .config import (
    FINANCE_KEYWORDS,
    OPERATIONS_KEYWORDS,
    PLANNING_KEYWORDS,
    get_config,
)
from .llm_factory import create_llm as _create_llm
from .state import OrchestratorState

log = structlog.get_logger()

VALID_AGENTS = {"finance", "operations", "planning"}

MULTI_AGENT_KEYWORDS = [
    "executive summary", "overall status", "full report",
    "company overview", "across the board", "everything",
]

_CLASSIFICATION_PROMPT = """\
You are a query classifier for an enterprise system. Given a user query, determine which \
specialist agent should handle it. Respond with EXACTLY one word: finance, operations, or planning.

- finance: budget, revenue, expenses, forecasts, P&L, costs, margins, spending
- operations: KPIs, SLAs, incidents, capacity, uptime, latency, deployments, monitoring
- planning: roadmaps, timelines, resources, milestones, risks, strategy, initiatives

Query: {query}

Agent:"""


def compute_keyword_scores(query: str) -> dict[str, int]:
    """Score a query against each domain's keyword list.

    Returns raw counts — higher means stronger signal for that domain.
    """
    q_lower = query.lower()
    return {
        "finance": sum(1 for kw in FINANCE_KEYWORDS if kw in q_lower),
        "operations": sum(1 for kw in OPERATIONS_KEYWORDS if kw in q_lower),
        "planning": sum(1 for kw in PLANNING_KEYWORDS if kw in q_lower),
    }


def _is_multi_agent_query(query: str) -> bool:
    q_lower = query.lower()
    return any(phrase in q_lower for phrase in MULTI_AGENT_KEYWORDS)


def classify_with_llm(query: str) -> str:
    """Use LLM to classify an ambiguous query. Expensive path — only called as fallback."""
    try:
        llm = _create_llm(temperature=0)
        messages = [
            SystemMessage(content="You are a query classifier. Respond with exactly one word."),
            HumanMessage(content=_CLASSIFICATION_PROMPT.format(query=query)),
        ]
        response = llm.invoke(messages)
        agent = response.content.strip().lower()

        # sanitize LLM output — it sometimes adds punctuation or explanation
        for valid in VALID_AGENTS:
            if valid in agent:
                return valid

        log.warning("llm_classification_unexpected", raw=agent, defaulting_to="planning")
        return "planning"

    except Exception as exc:
        # if LLM call fails, default to planning — it's the broadest agent
        log.error("llm_classification_failed", error=str(exc))
        return "planning"


def route_to_agent(state: OrchestratorState) -> str:
    """Hybrid routing: keyword rules first for speed, LLM fallback for ambiguity.

    Multi-agent queries (e.g., "executive summary") trigger sequential routing
    through all agents by tracking which ones have already responded.
    """
    if state["iteration_count"] >= get_config().max_iterations:
        return "FINISH"
    if state.get("final_response"):
        return "FINISH"

    # always route based on original user query, not the latest agent response
    query = state["messages"][0].content

    # multi-agent path — route to each agent that hasn't responded yet
    if _is_multi_agent_query(query):
        responded = set(state.get("agent_responses", {}).keys())
        for agent in ["finance", "operations", "planning"]:
            if agent not in responded:
                _record_routing(state, agent, "multi_agent_sequential")
                return agent
        return "FINISH"

    scores = compute_keyword_scores(query)
    max_score = max(scores.values())

    # clear winner — no LLM needed
    if max_score > 0 and list(scores.values()).count(max_score) == 1:
        winner = max(scores, key=scores.get)
        _record_routing(state, winner, "keyword_match", scores)
        return winner

    # tied or zero scores — ask the LLM
    agent = classify_with_llm(query)
    _record_routing(state, agent, "llm_fallback", scores)
    return agent


def _record_routing(
    state: OrchestratorState,
    agent: str,
    method: str,
    scores: dict | None = None,
):
    """Stash routing decision metadata for debugging and UI display."""
    state["routing_metadata"] = {
        "selected_agent": agent,
        "method": method,
        "keyword_scores": scores or {},
    }
