"""Finance specialist agent — handles budget, revenue, expense, and forecast queries."""

import structlog
from langchain_core.messages import AIMessage

from ..state import OrchestratorState
from ..tools.finance_tools import (
    get_budget_status,
    get_expense_breakdown,
    get_financial_forecast,
    get_revenue_report,
)

log = structlog.get_logger()

# maps keywords in the query to the right tool call
_TOOL_DISPATCH = {
    "budget": get_budget_status,
    "revenue": get_revenue_report,
    "expense": get_expense_breakdown,
    "spending": get_expense_breakdown,
    "forecast": get_financial_forecast,
    "projection": get_financial_forecast,
    "cost": get_expense_breakdown,
    "p&l": get_revenue_report,
    "profit": get_revenue_report,
    "margin": get_financial_forecast,
}


def _extract_quarter(query: str) -> str | None:
    """Pull quarter reference out of a query string."""
    import re
    match = re.search(r"\b(Q[1-4])\b", query, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _pick_tools(query: str) -> list[callable]:
    q_lower = query.lower()
    matched = []
    seen = set()
    for kw, fn in _TOOL_DISPATCH.items():
        if kw in q_lower and fn not in seen:
            matched.append(fn)
            seen.add(fn)

    # default: give them the budget overview
    if not matched:
        matched = [get_budget_status]
    return matched


def finance_node(state: OrchestratorState) -> dict:
    query = state["messages"][0].content
    quarter = _extract_quarter(query) or "Q3"

    tools_to_call = _pick_tools(query)
    results = {}
    for tool_fn in tools_to_call:
        try:
            # pass quarter or department depending on the tool's signature
            if tool_fn in (get_budget_status, get_revenue_report):
                results[tool_fn.__name__] = tool_fn(quarter)
            elif tool_fn == get_expense_breakdown:
                results[tool_fn.__name__] = tool_fn()
            elif tool_fn == get_financial_forecast:
                results[tool_fn.__name__] = tool_fn()
        except Exception as exc:
            log.error("finance_tool_error", tool=tool_fn.__name__, error=str(exc))
            results[tool_fn.__name__] = {"error": str(exc)}

    summary = _build_summary(results, query, quarter)

    return {
        "messages": [AIMessage(content=summary, name="finance_agent")],
        "agent_responses": {**state.get("agent_responses", {}), "finance": summary},
    }


def _build_summary(results: dict, query: str, quarter: str) -> str:
    """Synthesize tool outputs into a readable finance summary."""
    parts = [f"**Finance Analysis ({quarter})**\n"]

    if "get_budget_status" in results:
        b = results["get_budget_status"]
        if "error" not in b:
            parts.append(
                f"Budget utilization: {b['utilization_pct']}% "
                f"(${b['total_spent']:,.0f} of ${b['total_budget']:,.0f})"
            )
            top_spenders = sorted(
                b["departments"].items(),
                key=lambda x: x[1]["utilization_pct"],
                reverse=True,
            )[:3]
            for dept, info in top_spenders:
                parts.append(
                    f"  - {dept}: {info['utilization_pct']}% utilized "
                    f"(${info['remaining']:,.0f} remaining)"
                )

    if "get_revenue_report" in results:
        r = results["get_revenue_report"]
        if "error" not in r:
            parts.append(f"\nRevenue: ${r['total_revenue']:,.0f}")
            for prod, info in r["by_product"].items():
                yoy = info["yoy_growth_pct"]
                yoy_str = f"+{yoy}%" if yoy else "new product"
                parts.append(f"  - {prod}: ${info['current']:,.0f} ({yoy_str} YoY)")

    if "get_expense_breakdown" in results:
        e = results["get_expense_breakdown"]
        if "error" not in e:
            parts.append(f"\nExpense breakdown for {e['department']}:")
            for qtr, info in e["quarters"].items():
                parts.append(f"  {qtr}: ${info['total_spent']:,.0f}")

    if "get_financial_forecast" in results:
        fc = results["get_financial_forecast"]
        parts.append("\nForecast:")
        for period, proj in fc.get("projections", {}).items():
            parts.append(
                f"  {period}: revenue ${proj['projected_revenue']:,.0f}, "
                f"margin {proj['projected_margin_pct']}%"
            )

    return "\n".join(parts)
