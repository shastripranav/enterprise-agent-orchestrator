"""Integration tests for the full orchestration pipeline.

These test the complete flow: query → supervisor → routing → agent → response.
LLM calls are mocked to avoid API dependencies.
"""


import pytest

from src.orchestrator import build_graph, reset_orchestrator, run_query


@pytest.fixture(autouse=True)
def clean_orchestrator():
    reset_orchestrator()
    yield
    reset_orchestrator()


def test_finance_query_end_to_end():
    result = run_query("What's our Q3 budget utilization?")
    assert result.get("final_response")
    assert "finance" in result.get("agent_responses", {})
    assert result["iteration_count"] >= 2


def test_operations_query_end_to_end():
    result = run_query("Show me current SLA compliance")
    assert result.get("final_response")
    assert "operations" in result.get("agent_responses", {})


def test_planning_query_end_to_end():
    result = run_query("What's on the product roadmap for Q4?")
    assert result.get("final_response")
    assert "planning" in result.get("agent_responses", {})


def test_multi_agent_executive_summary():
    result = run_query("Give me an executive summary of Q3")
    assert result.get("final_response")
    responses = result.get("agent_responses", {})
    assert "finance" in responses
    assert "operations" in responses
    assert "planning" in responses
    assert "Executive Summary" in result["final_response"]


def test_iteration_guard_prevents_infinite_loop():
    result = run_query("What's the budget?")
    assert result["iteration_count"] <= 6


def test_graph_compiles_without_error():
    graph = build_graph()
    compiled = graph.compile()
    assert compiled is not None


# TODO: add test for error recovery when an agent throws
