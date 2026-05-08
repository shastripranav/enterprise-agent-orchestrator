# Contributing to enterprise-agent-orchestrator

MIT licensed, contributions welcome. Useful contributions: new specialist agents, supervisor routing improvements, and additional ADRs (architecture decision records) for design choices that come up.

## How to Contribute

1. Fork the repository on GitHub.
2. Create a topic branch off `main` (e.g. `feat/legal-agent`).
3. Make your changes and run the test suite.
4. If you're making a non-trivial design choice, please include a new ADR under `docs/adr/` following the existing format.
5. Open a pull request describing the change.

## Development setup

```bash
pip install -e ".[dev]"
```

This project uses LangGraph for the supervisor pattern. If you're new to LangGraph, the existing agents under `src/agents/` are a useful reference.

## Code style

```bash
ruff check src/ tests/ cli.py app.py
```

## Testing

```bash
pytest -v
```

When you add a new specialist agent, please add tests covering: (1) the agent runs to completion on a representative query, (2) the supervisor correctly routes to it, and (3) the response shape matches what the supervisor expects.

## Questions

Open an issue with the `question` label.
