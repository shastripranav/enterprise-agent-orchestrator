from langchain_core.messages import HumanMessage

from src.agents.planning_agent import planning_node
from src.state import create_initial_state


def _make_state(query: str) -> dict:
    state = create_initial_state()
    state["messages"] = [HumanMessage(content=query)]
    return state


def test_roadmap_query_returns_initiatives():
    state = _make_state("What's on the product roadmap?")
    result = planning_node(state)
    response = result["messages"][0].content
    assert "initiative" in response.lower() or "roadmap" in response.lower()
    assert "planning" in result["agent_responses"]


def test_q4_roadmap_filters_correctly():
    state = _make_state("What's on the roadmap for Q4?")
    result = planning_node(state)
    response = result["messages"][0].content
    assert "Q4" in response
    assert "Enterprise Expansion" in response


def test_resource_query_returns_allocation():
    state = _make_state("Show me resource allocation across teams")
    result = planning_node(state)
    response = result["messages"][0].content
    assert "headcount" in response.lower() or "Resource" in response


def test_risk_query_returns_assessment():
    state = _make_state("What are the top risks?")
    result = planning_node(state)
    response = result["messages"][0].content
    assert "risk" in response.lower()


def test_timeline_query_returns_milestones():
    state = _make_state("Show me project timelines and milestones")
    result = planning_node(state)
    response = result["messages"][0].content
    assert "milestone" in response.lower() or "Tracked" in response
