# ADR-002: LangGraph Over CrewAI for Orchestration

## Status
Accepted

## Context
We evaluated several frameworks for multi-agent orchestration:
1. **LangGraph** — graph-based orchestration from the LangChain ecosystem
2. **CrewAI** — role-based multi-agent framework
3. **AutoGen** — Microsoft's multi-agent conversation framework
4. **Custom implementation** — build from scratch with asyncio

## Decision
LangGraph.

## Rationale
- **Fine-grained state management**: LangGraph's `TypedDict` state is passed between nodes with full control over what each node reads and writes. This is critical for tracking routing metadata, agent responses, and iteration counts.
- **Conditional routing**: First-class support for `add_conditional_edges` maps directly to our hybrid routing requirement. We can inject custom routing functions that return the next node name.
- **LangChain ecosystem**: Seamless integration with `langchain-openai`, `langchain-anthropic`, and `langchain-community` for multi-provider LLM support. No adapter code needed.
- **Debuggability**: LangGraph's execution is deterministic given the same state — each node is a pure function of state → state updates. This makes testing straightforward.
- **Mature and maintained**: Active development, good documentation, production usage at scale.

## Alternatives Considered

**CrewAI**: Higher-level abstraction that's great for role-playing agents, but gives less control over routing logic. Our hybrid routing (keyword rules + LLM fallback) doesn't fit CrewAI's task delegation model cleanly.

**AutoGen**: Strong for conversational multi-agent patterns, but overkill for our classification → delegation → aggregation flow. Also heavier runtime.

**Custom**: Would give full control but means reimplementing state management, graph execution, and error handling from scratch. Not worth it when LangGraph provides these primitives.

## Consequences
- All orchestration logic is expressed as a `StateGraph` with nodes and edges
- Agent functions must accept and return `OrchestratorState` dicts
- We depend on `langgraph` and `langchain-core` as core dependencies
