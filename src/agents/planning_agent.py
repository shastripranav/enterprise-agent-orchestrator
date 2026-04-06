"""Planning specialist agent — roadmaps, resources, timelines, and risks."""

import structlog
from langchain_core.messages import AIMessage

from ..state import OrchestratorState
from ..tools.planning_tools import (
    get_product_roadmap,
    get_project_timeline,
    get_resource_allocation,
    get_risk_assessment,
)

log = structlog.get_logger()

_TOOL_DISPATCH = {
    "roadmap": get_product_roadmap,
    "initiative": get_product_roadmap,
    "resource": get_resource_allocation,
    "allocation": get_resource_allocation,
    "headcount": get_resource_allocation,
    "team": get_resource_allocation,
    "timeline": get_project_timeline,
    "milestone": get_project_timeline,
    "deadline": get_project_timeline,
    "risk": get_risk_assessment,
    "strategy": get_product_roadmap,
    "priority": get_product_roadmap,
}


def _pick_tools(query: str) -> list[callable]:
    q_lower = query.lower()
    matched = []
    seen = set()
    for kw, fn in _TOOL_DISPATCH.items():
        if kw in q_lower and fn not in seen:
            matched.append(fn)
            seen.add(fn)
    return matched or [get_product_roadmap]


def _extract_quarter(query: str) -> str | None:
    import re
    m = re.search(r"\b(Q[1-4])\b", query, re.IGNORECASE)
    return m.group(1).upper() if m else None


def planning_node(state: OrchestratorState) -> dict:
    query = state["messages"][0].content
    quarter = _extract_quarter(query)
    tools_to_call = _pick_tools(query)

    results = {}
    for tool_fn in tools_to_call:
        try:
            if tool_fn == get_product_roadmap:
                results[tool_fn.__name__] = tool_fn(quarter)
            elif tool_fn == get_resource_allocation:
                results[tool_fn.__name__] = tool_fn()
            elif tool_fn == get_project_timeline:
                results[tool_fn.__name__] = tool_fn()
            else:
                results[tool_fn.__name__] = tool_fn()
        except Exception as exc:
            log.error("planning_tool_error", tool=tool_fn.__name__, error=str(exc))
            results[tool_fn.__name__] = {"error": str(exc)}

    summary = _build_summary(results, query, quarter)

    return {
        "messages": [AIMessage(content=summary, name="planning_agent")],
        "agent_responses": {**state.get("agent_responses", {}), "planning": summary},
    }


def _build_summary(results: dict, query: str, quarter: str | None) -> str:
    parts = ["**Strategic Planning Report**\n"]

    if "get_product_roadmap" in results:
        rm = results["get_product_roadmap"]
        if "error" not in rm:
            if "quarters" in rm:
                for qtr, info in rm["quarters"].items():
                    count = info['initiative_count']
                    parts.append(f"{qtr} — {info['theme']} ({count} initiatives)")
                    for init in info["initiatives"]:
                        parts.append(
                            f"  • {init['name']}: {init['status']} ({init['progress_pct']}%)"
                        )
            else:
                parts.append(f"{rm.get('quarter', '')} — {rm.get('theme', '')}")
                for init in rm.get("initiatives", []):
                    parts.append(
                        f"  • {init['name']}: {init['status']} ({init['progress_pct']}%)"
                    )

    if "get_resource_allocation" in results:
        ra = results["get_resource_allocation"]
        if "error" not in ra:
            parts.append(f"\nResource allocation: {ra.get('total_headcount', 0)} total headcount")
            for team_name, info in ra.get("teams", {}).items():
                hc, pc = info['headcount'], info['project_count']
                parts.append(f"  {team_name}: {hc} people, {pc} projects")

    if "get_project_timeline" in results:
        tl = results["get_project_timeline"]
        if "error" not in tl:
            parts.append(f"\nTracked projects: {tl.get('tracked_projects', 0)}")
            for pid, info in tl.get("projects", {}).items():
                nm = info.get("next_milestone")
                if nm:
                    nm_str = f"next: {nm['name']} (due {nm['due_date']})"
                else:
                    nm_str = "all milestones complete"
                parts.append(f"  {pid} ({info['name']}): {nm_str}")

    if "get_risk_assessment" in results:
        ra = results["get_risk_assessment"]
        total = ra['total_risks']
        hi = ra['high_impact_count']
        parts.append(f"\nRisk assessment: {total} risks ({hi} high/critical impact)")
        for risk in ra.get("risks", [])[:3]:
            parts.append(
                f"  [{risk['probability'].upper()} prob / {risk['impact'].upper()} impact] "
                f"{risk['title']}"
            )

    return "\n".join(parts)
