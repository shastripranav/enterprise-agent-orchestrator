from langchain_core.messages import HumanMessage

from src.agents.operations_agent import operations_node
from src.state import create_initial_state


def _make_state(query: str) -> dict:
    state = create_initial_state()
    state["messages"] = [HumanMessage(content=query)]
    return state


def test_kpi_query_returns_metrics():
    state = _make_state("Show me the KPI dashboard")
    result = operations_node(state)
    response = result["messages"][0].content
    assert "uptime" in response.lower()
    assert "operations" in result["agent_responses"]


def test_sla_query_returns_compliance():
    state = _make_state("What's our SLA compliance status?")
    result = operations_node(state)
    response = result["messages"][0].content
    assert "SLA" in response or "compliance" in response.lower()


def test_incident_query_returns_log():
    state = _make_state("Any critical incidents this week?")
    result = operations_node(state)
    response = result["messages"][0].content
    assert "incident" in response.lower()


def test_capacity_query_returns_utilization():
    state = _make_state("Show me the capacity report")
    result = operations_node(state)
    response = result["messages"][0].content
    assert "Capacity" in response or "capacity" in response.lower()
