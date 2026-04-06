import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class OrchestratorState(TypedDict):
    """Shared state passed between all nodes in the orchestration graph."""

    messages: Annotated[list[BaseMessage], operator.add]
    next_agent: str
    query_intent: str
    agent_responses: dict
    iteration_count: int
    final_response: str
    routing_metadata: dict  # tracks how routing decisions were made


def create_initial_state() -> OrchestratorState:
    return {
        "messages": [],
        "next_agent": "",
        "query_intent": "",
        "agent_responses": {},
        "iteration_count": 0,
        "final_response": "",
        "routing_metadata": {},
    }
