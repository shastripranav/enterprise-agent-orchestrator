"""Main LangGraph graph definition — wires supervisor, agents, and routing together."""

from langgraph.graph import END, StateGraph

from .agents.finance_agent import finance_node
from .agents.operations_agent import operations_node
from .agents.planning_agent import planning_node
from .routing import route_to_agent
from .state import OrchestratorState, create_initial_state
from .supervisor import supervisor_node


def build_graph() -> StateGraph:
    """Construct the hub-and-spoke orchestration graph.

    Supervisor sits at the center. Conditional edges route to specialist agents
    based on the hybrid routing function. Each agent reports back to the supervisor
    for aggregation or completion.
    """
    graph = StateGraph(OrchestratorState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("finance", finance_node)
    graph.add_node("operations", operations_node)
    graph.add_node("planning", planning_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "finance": "finance",
            "operations": "operations",
            "planning": "planning",
            "FINISH": END,
        },
    )

    # spoke → hub: every agent reports back to supervisor
    graph.add_edge("finance", "supervisor")
    graph.add_edge("operations", "supervisor")
    graph.add_edge("planning", "supervisor")

    return graph


_compiled_graph = None


def get_orchestrator():
    """Singleton compiled graph — avoids rebuilding on every invocation."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph


def run_query(query: str) -> dict:
    """Execute a single query through the orchestration pipeline.

    Returns the full final state including routing metadata, agent responses,
    and the final synthesized answer.
    """
    from langchain_core.messages import HumanMessage

    orchestrator = get_orchestrator()
    initial_state = create_initial_state()
    initial_state["messages"] = [HumanMessage(content=query)]

    result = orchestrator.invoke(initial_state)
    return result


def reset_orchestrator():
    """Force graph rebuild — used in tests and when switching LLM providers."""
    global _compiled_graph
    _compiled_graph = None
