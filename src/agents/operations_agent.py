"""Operations specialist agent — handles KPIs, SLAs, incidents, and capacity queries."""

import structlog
from langchain_core.messages import AIMessage

from ..state import OrchestratorState
from ..tools.operations_tools import (
    get_capacity_report,
    get_kpi_dashboard,
    get_recent_incidents,
    get_sla_compliance,
)

log = structlog.get_logger()

_TOOL_DISPATCH = {
    "kpi": get_kpi_dashboard,
    "metric": get_kpi_dashboard,
    "uptime": get_kpi_dashboard,
    "latency": get_kpi_dashboard,
    "sla": get_sla_compliance,
    "compliance": get_sla_compliance,
    "incident": get_recent_incidents,
    "outage": get_recent_incidents,
    "alert": get_recent_incidents,
    "capacity": get_capacity_report,
    "utilization": get_capacity_report,
    "cpu": get_capacity_report,
    "memory": get_capacity_report,
    "storage": get_capacity_report,
}


def _pick_tools(query: str) -> list[callable]:
    q_lower = query.lower()
    matched = []
    seen = set()
    for kw, fn in _TOOL_DISPATCH.items():
        if kw in q_lower and fn not in seen:
            matched.append(fn)
            seen.add(fn)
    return matched or [get_kpi_dashboard]


def _extract_severity(query: str) -> str | None:
    for sev in ("critical", "high", "medium", "low"):
        if sev in query.lower():
            return sev
    return None


def operations_node(state: OrchestratorState) -> dict:
    query = state["messages"][0].content
    tools_to_call = _pick_tools(query)

    results = {}
    for tool_fn in tools_to_call:
        try:
            if tool_fn == get_recent_incidents:
                severity = _extract_severity(query)
                results[tool_fn.__name__] = tool_fn(severity=severity)
            elif tool_fn == get_sla_compliance:
                results[tool_fn.__name__] = tool_fn()
            else:
                results[tool_fn.__name__] = tool_fn()
        except Exception as exc:
            log.error("ops_tool_error", tool=tool_fn.__name__, error=str(exc))
            results[tool_fn.__name__] = {"error": str(exc)}

    summary = _build_summary(results, query)

    return {
        "messages": [AIMessage(content=summary, name="operations_agent")],
        "agent_responses": {**state.get("agent_responses", {}), "operations": summary},
    }


def _build_summary(results: dict, query: str) -> str:
    parts = ["**Operations Report**\n"]

    if "get_kpi_dashboard" in results:
        kpis = results["get_kpi_dashboard"].get("kpis", {})
        parts.append(f"Platform uptime: {kpis.get('uptime_pct', 'N/A')}%")
        avg_lat = kpis.get('avg_latency_ms', 'N/A')
        p99_lat = kpis.get('p99_latency_ms', 'N/A')
        parts.append(f"Avg latency: {avg_lat}ms (p99: {p99_lat}ms)")
        parts.append(f"Error rate: {kpis.get('error_rate_pct', 'N/A')}%")
        parts.append(f"Throughput: {kpis.get('throughput_rps', 'N/A')} req/s")
        parts.append(f"Daily active users: {kpis.get('active_users_daily', 'N/A'):,}")

    if "get_sla_compliance" in results:
        sla = results["get_sla_compliance"]
        if "error" not in sla:
            breached = sla.get("breached_count", 0)
            total = sla.get("total_services", 0)
            parts.append(f"\nSLA compliance: {total - breached}/{total} services meeting targets")
            for svc, info in sla.get("breached_services", {}).items():
                parts.append(
                    f"  ⚠ {svc}: {info['actual_uptime_pct']}% "
                    f"(target: {info['target_uptime_pct']}%)"
                )

    if "get_recent_incidents" in results:
        inc = results["get_recent_incidents"]
        incidents = inc.get("incidents", [])
        parts.append(f"\nRecent incidents: {inc.get('count', 0)}")
        for i in incidents[:3]:
            parts.append(
                f"  [{i['severity'].upper()}] {i['title']} — "
                f"{i['duration_minutes']}min, {i['impact']}"
            )

    if "get_capacity_report" in results:
        cap_data = results["get_capacity_report"]
        cap = cap_data.get("capacity", {})
        parts.append("\nCapacity:")
        for resource, info in cap.items():
            util = info.get("utilization_pct") or info.get("avg_utilization_pct", 0)
            parts.append(f"  {resource}: {util}% utilized")
        for w in cap_data.get("warnings", []):
            parts.append(f"  ⚠ {w}")

    return "\n".join(parts)
