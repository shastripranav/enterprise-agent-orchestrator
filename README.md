# Enterprise Multi-Agent Orchestrator

[![CI](https://github.com/shastripranav/enterprise-agent-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/shastripranav/enterprise-agent-orchestrator/actions/workflows/ci.yml)

Hub-and-spoke multi-agent system using LangGraph — routes enterprise queries to Finance, Operations, and Planning specialist agents via hybrid keyword + LLM routing.

## Architecture

```
                    ┌──────────────────────┐
                    │     User Query       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   SUPERVISOR AGENT    │
                    │   (Hub / Router)      │
                    │                       │
                    │ 1. Classify intent    │
                    │ 2. Route to agent     │
                    │ 3. Aggregate output   │
                    └───┬──────┬───────┬───┘
                        │      │       │
               ┌────────┘      │       └────────┐
               ▼               ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │   FINANCE    │  │  OPERATIONS  │  │   PLANNING   │
     │    AGENT     │  │    AGENT     │  │    AGENT     │
     │              │  │              │  │              │
     │ • budget     │  │ • kpi_dash   │  │ • roadmap    │
     │ • revenue    │  │ • sla_status │  │ • resources  │
     │ • forecast   │  │ • incidents  │  │ • timeline   │
     │ • expenses   │  │ • capacity   │  │ • risks      │
     └──────────────┘  └──────────────┘  └──────────────┘
```

## Quick Start

```bash
# install
pip install -e ".[dev]"

# configure
cp .env.example .env
# add your OpenAI/Anthropic API key to .env

# CLI — single query
python cli.py query "What's our Q3 budget utilization?"

# CLI — interactive chat
python cli.py chat

# CLI — with debug routing info
python cli.py query "Show SLA compliance" --debug

# Streamlit UI
streamlit run app.py
```

## Hybrid Routing

The key differentiator — keyword-based rules handle common queries instantly, LLM classification kicks in only for ambiguous ones:

| Query | Routing Method | Agent |
|-------|---------------|-------|
| "What's our Q3 budget?" | Keyword match (fast) | Finance |
| "Show SLA compliance" | Keyword match (fast) | Operations |
| "Product roadmap for Q4?" | Keyword match (fast) | Planning |
| "How are things going?" | LLM fallback | Classified by LLM |
| "Executive summary of Q3" | Multi-agent | All 3 → aggregated |

## Sample Queries

```
What's our Q3 budget utilization?
Show me the revenue report for Q2
What are our current KPIs?
Any critical incidents this week?
What's on the product roadmap for Q4?
What resources do we need for the AI initiative?
Give me an executive summary of Q3
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: openai, anthropic, ollama |
| `LLM_MODEL` | provider default | Model override (e.g., gpt-4o) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `MAX_ITERATIONS` | `5` | Max routing iterations (prevents infinite loops) |

## Development

```bash
# install dev deps
pip install -e ".[dev]"

# run tests
pytest -v

# lint
ruff check src/ tests/ cli.py app.py

# run with specific provider
python cli.py --provider anthropic query "Show me the roadmap"
```

## Architecture Decision Records

- [ADR-001: Hub-and-Spoke over Peer-to-Peer](docs/adr/001-hub-spoke-over-peer-to-peer.md)
- [ADR-002: LangGraph over CrewAI](docs/adr/002-langgraph-over-crewai.md)
- [ADR-003: Mock Data Strategy](docs/adr/003-mock-data-strategy.md)

## Project Structure

```
src/
├── orchestrator.py          # LangGraph graph definition
├── supervisor.py            # Supervisor node (hub)
├── routing.py               # Hybrid routing (keyword + LLM)
├── state.py                 # Shared state schema
├── config.py                # Configuration
├── llm_factory.py           # Multi-provider LLM factory
├── agents/
│   ├── finance_agent.py     # Finance specialist
│   ├── operations_agent.py  # Operations specialist
│   └── planning_agent.py    # Planning specialist
└── tools/
    ├── finance_tools.py     # Budget, revenue, expense, forecast
    ├── operations_tools.py  # KPIs, SLAs, incidents, capacity
    └── planning_tools.py    # Roadmap, resources, timelines, risks
```

## License

MIT
