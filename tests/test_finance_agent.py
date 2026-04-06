from langchain_core.messages import HumanMessage

from src.agents.finance_agent import finance_node
from src.state import create_initial_state


def _make_state(query: str) -> dict:
    state = create_initial_state()
    state["messages"] = [HumanMessage(content=query)]
    return state


def test_budget_query_returns_utilization():
    state = _make_state("What's our Q3 budget utilization?")
    result = finance_node(state)
    response = result["messages"][0].content
    assert "Budget utilization" in response or "budget" in response.lower()
    assert "finance" in result["agent_responses"]


def test_revenue_query_includes_products():
    state = _make_state("Show me the Q2 revenue report")
    result = finance_node(state)
    response = result["messages"][0].content
    assert "Revenue" in response
    assert "Enterprise Platform" in response


def test_forecast_query_returns_projections():
    state = _make_state("What's the financial forecast?")
    result = finance_node(state)
    response = result["messages"][0].content
    assert "Forecast" in response or "forecast" in response.lower()


def test_expense_query_returns_breakdown():
    state = _make_state("Show me expense breakdown for Engineering")
    result = finance_node(state)
    response = result["messages"][0].content
    assert "expense" in response.lower() or "Engineering" in response


def test_default_quarter_is_q3():
    state = _make_state("What's the budget status?")
    result = finance_node(state)
    assert "Q3" in result["messages"][0].content
