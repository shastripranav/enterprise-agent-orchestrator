"""Tests for the hybrid routing logic — the key differentiator."""

from unittest.mock import patch

from langchain_core.messages import HumanMessage

from src.routing import classify_with_llm, compute_keyword_scores, route_to_agent
from src.state import create_initial_state


class TestKeywordScoring:
    def test_finance_keywords_score(self):
        scores = compute_keyword_scores("What's our Q3 budget utilization and revenue?")
        assert scores["finance"] >= 2
        assert scores["operations"] == 0
        assert scores["planning"] == 0

    def test_operations_keywords_score(self):
        scores = compute_keyword_scores("Show me SLA compliance and incident report")
        assert scores["operations"] >= 2
        assert scores["finance"] == 0

    def test_planning_keywords_score(self):
        scores = compute_keyword_scores("What's on the roadmap and what are the risks?")
        assert scores["planning"] >= 2

    def test_no_keywords_all_zeros(self):
        scores = compute_keyword_scores("Tell me something interesting")
        assert all(v == 0 for v in scores.values())

    def test_mixed_keywords_produce_scores(self):
        scores = compute_keyword_scores("What's the budget impact on our roadmap timeline?")
        assert scores["finance"] > 0
        assert scores["planning"] > 0


class TestRouteToAgent:
    def _make_state(self, query, iteration=0, responses=None):
        state = create_initial_state()
        state["messages"] = [HumanMessage(content=query)]
        state["iteration_count"] = iteration
        state["agent_responses"] = responses or {}
        return state

    def test_clear_finance_query_routes_to_finance(self):
        state = self._make_state("What's our Q3 budget status?")
        assert route_to_agent(state) == "finance"

    def test_clear_operations_query_routes_to_operations(self):
        state = self._make_state("Show me SLA compliance for our services")
        assert route_to_agent(state) == "operations"

    def test_clear_planning_query_routes_to_planning(self):
        state = self._make_state("What's on the product roadmap for Q4?")
        assert route_to_agent(state) == "planning"

    def test_iteration_guard_returns_finish(self):
        state = self._make_state("budget status", iteration=5)
        assert route_to_agent(state) == "FINISH"

    def test_final_response_present_returns_finish(self):
        state = self._make_state("budget status")
        state["final_response"] = "Already answered"
        assert route_to_agent(state) == "FINISH"

    def test_multi_agent_query_routes_sequentially(self):
        state = self._make_state("Give me an executive summary")
        result = route_to_agent(state)
        assert result == "finance"

        state["agent_responses"]["finance"] = "done"
        result = route_to_agent(state)
        assert result == "operations"

        state["agent_responses"]["operations"] = "done"
        result = route_to_agent(state)
        assert result == "planning"

        state["agent_responses"]["planning"] = "done"
        result = route_to_agent(state)
        assert result == "FINISH"

    @patch("src.routing.classify_with_llm")
    def test_ambiguous_query_falls_through_to_llm(self, mock_classify):
        mock_classify.return_value = "finance"
        state = self._make_state("How are things going at the company lately?")
        result = route_to_agent(state)
        mock_classify.assert_called_once()
        assert result == "finance"

    @patch("src.routing.classify_with_llm")
    def test_tied_scores_use_llm_fallback(self, mock_classify):
        mock_classify.return_value = "operations"
        # "budget" (finance) + "capacity" (operations) — tied at 1 each
        state = self._make_state("How does the budget affect capacity?")
        result = route_to_agent(state)
        assert result == "operations"
        mock_classify.assert_called_once()


class TestClassifyWithLLM:
    @patch("src.routing._create_llm")
    def test_llm_classification_parses_response(self, mock_factory):
        mock_llm = mock_factory.return_value
        mock_llm.invoke.return_value.content = "finance"
        result = classify_with_llm("what about our earnings?")
        assert result == "finance"

    @patch("src.routing._create_llm")
    def test_llm_failure_defaults_to_planning(self, mock_factory):
        mock_factory.side_effect = Exception("API error")
        result = classify_with_llm("something ambiguous")
        assert result == "planning"

    # TODO: add test for LLM returning unexpected output like "I think finance"
