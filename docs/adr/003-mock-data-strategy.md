# ADR-003: Mock Data With Adapter Pattern for Real Integrations

## Status
Accepted

## Context
The specialist agents need data to answer queries — budget numbers, KPIs, roadmap items. We had three options:
1. **Mock data**: JSON fixtures with realistic but synthetic enterprise data
2. **Live API integrations**: Connect to real services (Jira, Datadog, QuickBooks, etc.)
3. **Database-backed**: Stand up a local database with seeded data

## Decision
Mock data via JSON fixtures, with tool functions structured as adapters that can be swapped to real integrations without changing agent code.

## Rationale
- **Demo-friendly**: Anyone can clone and run the project without API keys, service accounts, or infrastructure setup. The mock data demonstrates the orchestration pattern, not the integration.
- **Adapter pattern**: Each tool function (e.g., `get_budget_status()`) reads from JSON today but has the same interface a real API client would have. Swapping `json.load()` for an HTTP call requires zero changes to the agent layer.
- **Consistent for testing**: Mock data is deterministic — tests don't break because a live API returned different numbers. Test assertions can be exact.
- **Realistic data**: The JSON fixtures model real enterprise scenarios — multi-department budgets, SLA breaches, roadmap initiatives with progress tracking, risk assessments. This makes demos convincing.

## Data Design Decisions
- Budget data includes 3 quarters (Q1-Q3) with 5 departments each, plus revenue and forecast
- KPI data includes platform metrics, SLA compliance for 5 services, 5 incidents, and capacity numbers
- Roadmap data includes 3 quarters of initiatives, resource allocation for 6 teams, project timelines, and 5 risks
- All numbers are internally consistent (e.g., budget utilization % matches spent/allocated)

## Consequences
- Tool functions live in `src/tools/` and read from `data/` directory
- Adding a real integration means replacing the data loading in a tool function
- Tests can rely on exact values from mock data
- FIXME: we should add a data adapter interface to formalize the contract
