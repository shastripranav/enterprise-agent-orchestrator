"""Finance domain tools — budget, revenue, expense, and forecast queries."""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_budget_cache: dict | None = None


def _load_budget_data() -> dict:
    global _budget_cache
    if _budget_cache is None:
        with open(_DATA_DIR / "mock_budget.json") as f:
            _budget_cache = json.load(f)
    return _budget_cache


def get_budget_status(quarter: str = "Q3") -> dict:
    """Return budget allocation, spent, and remaining by department for a quarter."""
    data = _load_budget_data()
    quarter = quarter.upper()
    if quarter not in data["quarters"]:
        return {"error": f"No data for {quarter}. Available: {list(data['quarters'].keys())}"}

    q = data["quarters"][quarter]
    summary = {
        "quarter": quarter,
        "fiscal_year": data["fiscal_year"],
        "total_budget": q["total_budget"],
        "total_spent": q["total_spent"],
        "utilization_pct": q["utilization_pct"],
        "departments": {},
    }
    for dept, info in q["departments"].items():
        summary["departments"][dept] = {
            "allocated": info["allocated"],
            "spent": info["spent"],
            "remaining": info["remaining"],
            "utilization_pct": round(info["spent"] / info["allocated"] * 100, 1),
        }
    return summary


def get_revenue_report(period: str = "Q3") -> dict:
    data = _load_budget_data()
    period = period.upper()
    rev = data.get("revenue", {})
    if period not in rev:
        return {"error": f"No revenue data for {period}. Available: {list(rev.keys())}"}

    q_rev = rev[period]
    return {
        "period": period,
        "total_revenue": q_rev["total"],
        "by_product": q_rev["by_product"],
    }


def get_expense_breakdown(department: str = "Engineering") -> dict:
    """Pull expense categories for a specific department across available quarters."""
    data = _load_budget_data()
    result = {"department": department, "quarters": {}}

    for qtr, q_data in data["quarters"].items():
        dept_data = q_data["departments"].get(department)
        if dept_data:
            result["quarters"][qtr] = {
                "total_spent": dept_data["spent"],
                "categories": dept_data["categories"],
            }

    if not result["quarters"]:
        available = set()
        for q_data in data["quarters"].values():
            available.update(q_data["departments"].keys())
        return {"error": f"Department '{department}' not found. Available: {sorted(available)}"}

    return result


def get_financial_forecast(quarters_ahead: int = 3) -> dict:
    data = _load_budget_data()
    forecasts = data.get("forecast", {})

    # only return as many quarters as requested
    items = list(forecasts.items())[:quarters_ahead]
    return {
        "quarters_ahead": len(items),
        "projections": {k: v for k, v in items},
    }
