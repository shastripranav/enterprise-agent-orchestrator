# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-18

### Added

- Hub-and-spoke (supervisor) multi-agent pattern built on LangGraph for state management and orchestration
- Three specialist agents: Finance, Operations, and Planning
- Hybrid routing layer combining fast keyword rules with an LLM classifier fallback for ambiguous queries, including a multi-agent path that fans out to all specialists and aggregates results
- Supervisor node that classifies intent, dispatches to one or more specialists, and aggregates their outputs into a single response
- Pluggable multi-provider LLM factory supporting OpenAI, Anthropic, and Ollama
- Architecture Decision Records under `docs/adr/` documenting hub-vs-peer choice, LangGraph-vs-CrewAI selection, and the mock data strategy
- Click-based CLI (`cli.py`) with single-query, interactive chat, and `--debug` routing modes
- Streamlit UI (`app.py`) as an alternative front end
- Per-agent mock data tools: budget/revenue/forecast/expenses (Finance), KPIs/SLAs/incidents/capacity (Operations), and roadmap/resources/timeline/risks (Planning)
- Test suite covering routing decisions, supervisor orchestration, shared state schema, and each specialist agent
- Python 3.10 and 3.12 support (matrix-tested in CI)
