from langchain_core.messages import AIMessage, HumanMessage

from src.state import create_initial_state


def test_create_initial_state_has_all_keys():
    state = create_initial_state()
    assert state["messages"] == []
    assert state["next_agent"] == ""
    assert state["iteration_count"] == 0
    assert state["agent_responses"] == {}
    assert state["final_response"] == ""
    assert state["routing_metadata"] == {}


def test_state_messages_are_appendable():
    state = create_initial_state()
    state["messages"] = [HumanMessage(content="hello")]
    assert len(state["messages"]) == 1
    state["messages"].append(AIMessage(content="hi back"))
    assert len(state["messages"]) == 2


def test_state_agent_responses_accumulate():
    state = create_initial_state()
    state["agent_responses"]["finance"] = "budget looks good"
    state["agent_responses"]["operations"] = "kpis are healthy"
    assert len(state["agent_responses"]) == 2
