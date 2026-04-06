# ADR-001: Hub-and-Spoke Over Peer-to-Peer Agent Communication

## Status
Accepted

## Context
We need to choose a communication topology for the multi-agent system. The two main options are:
1. **Hub-and-spoke** — a central supervisor coordinates all agent interactions
2. **Peer-to-peer** — agents communicate directly with each other, negotiating task handoffs

The system has 3 specialist agents (Finance, Operations, Planning) and needs to support both single-agent queries and multi-agent aggregation (e.g., executive summaries).

## Decision
Hub-and-spoke with a central supervisor agent.

## Rationale
- **Single control flow**: All routing decisions go through one node, making the system easier to debug, trace, and audit. In an enterprise context, auditability matters.
- **Clear accountability**: The supervisor owns the routing decision. If a query gets misrouted, there's one place to look — not a chain of peer negotiations.
- **Simpler iteration guard**: A central supervisor can enforce maximum iteration counts trivially. Peer-to-peer systems need distributed consensus on termination.
- **Works well at this scale**: For 3-7 specialist agents, hub-and-spoke is efficient. Peer-to-peer shines when agents need to collaborate dynamically on sub-tasks, which isn't our pattern.
- **Better for hybrid routing**: Our keyword + LLM routing logic naturally fits a centralized decision point.

## Tradeoffs
- Hub-and-spoke introduces a single point of failure (the supervisor). For production, we'd add health checks and supervisor failover.
- Peer-to-peer would allow more flexible agent collaboration, but adds complexity we don't need for classification + delegation.
- If we later need agents to sub-delegate to each other (e.g., Finance asking Operations for related data), we'll need to add cross-agent calls or extend the supervisor.

## Consequences
- The supervisor node must handle all routing logic (implemented in `routing.py`)
- All agents report back to the supervisor, not to each other
- Multi-agent queries are executed sequentially through the supervisor loop
