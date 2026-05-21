"""Run the supervisor routing evaluation harness and print a scorecard.

Usage:
    python scripts/run_evaluation.py

Reads tests/evaluation/queries.yaml, sends each query through the supervisor's
routing layer, compares the actual routing against expected_routing, and
prints a per-query and overall scorecard.

This evaluation focuses on routing correctness — it does NOT exercise the
specialist agents' content quality (that's a separate evaluation).

Note: this harness exercises the routing layer end-to-end. If LLM-based
routing is triggered (ambiguous queries with tied/zero keyword scores), set
the appropriate API key in your environment (see README) before running.
The keyword-only routing path works without any keys; on LLM failure the
router defaults to the planning agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from langchain_core.messages import HumanMessage

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from src.routing import route_to_agent
    from src.state import create_initial_state
except ImportError:
    print(
        "ERROR: could not import the router from src/. Run this script from the "
        "repository root or ensure src/ is on PYTHONPATH.",
        file=sys.stderr,
    )
    raise


def load_queries(path: Path) -> list[dict]:
    with path.open() as f:
        return yaml.safe_load(f)["queries"]


def route_query(query: str) -> list[str]:
    """Send a query through the supervisor's routing layer.

    Builds a fresh OrchestratorState with the user query and invokes the
    hybrid router. Returns the selected agent(s) as a list so the harness
    can compare against expected_routing.
    """
    state = create_initial_state()
    state["messages"] = [HumanMessage(content=query)]
    selected = route_to_agent(state)
    if isinstance(selected, str):
        return [] if selected == "FINISH" else [selected]
    return list(selected)


def run_one(query: dict) -> dict:
    """Route one query and return a result record."""
    actual_routing = route_query(query["query"])
    expected = sorted(query["expected_routing"])
    actual = sorted(actual_routing)
    return {
        "id": query["id"],
        "query": query["query"][:60] + ("..." if len(query["query"]) > 60 else ""),
        "expected": expected,
        "actual": actual,
        "match": expected == actual,
    }


def print_scorecard(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["match"])
    print()
    print(f"{'ID':<25} {'Expected':<35} {'Actual':<35} {'PASS':<6}")
    print("-" * 105)
    for r in results:
        marker = "PASS" if r["match"] else "FAIL"
        print(f"{r['id']:<25} {str(r['expected']):<35} {str(r['actual']):<35} {marker:<6}")
    print("-" * 105)
    print(f"Total: {passed}/{total} passed ({100 * passed / total:.0f}%)")
    print()


def main() -> int:
    queries_path = REPO_ROOT / "tests" / "evaluation" / "queries.yaml"
    queries = load_queries(queries_path)
    results = [run_one(q) for q in queries]
    print_scorecard(results)
    failed = [r for r in results if not r["match"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
