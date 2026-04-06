"""Operations domain tools — KPIs, SLAs, incidents, and capacity."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_kpi_cache: dict | None = None


def _load_kpi_data() -> dict:
    global _kpi_cache
    if _kpi_cache is None:
        with open(_DATA_DIR / "mock_kpis.json") as f:
            _kpi_cache = json.load(f)
    return _kpi_cache


def get_kpi_dashboard() -> dict:
    """Return current platform KPIs — uptime, latency, error rate, throughput."""
    data = _load_kpi_data()
    return {
        "snapshot_date": data["snapshot_date"],
        "kpis": data["platform_kpis"],
    }


def get_sla_compliance(service: str | None = None) -> dict:
    data = _load_kpi_data()
    sla = data["sla_compliance"]

    if service:
        # fuzzy match on service name
        matches = {k: v for k, v in sla.items() if service.lower() in k.lower()}
        if not matches:
            return {
                "error": f"No SLA data for '{service}'. Available: {list(sla.keys())}",
            }
        return {"services": matches}

    breached = {k: v for k, v in sla.items() if v["status"] == "breached"}
    met = {k: v for k, v in sla.items() if v["status"] == "met"}

    return {
        "total_services": len(sla),
        "breached_count": len(breached),
        "breached_services": breached,
        "met_services": met,
    }


def get_recent_incidents(severity: str | None = None, days: int = 7) -> dict:
    data = _load_kpi_data()
    incidents = data["incidents"]

    # TODO: filter by actual date math once we have a real data layer
    _ = datetime.now(timezone.utc) - timedelta(days=days)

    filtered = incidents
    if severity:
        severity = severity.lower()
        filtered = [i for i in filtered if i["severity"] == severity]

    return {
        "filter": {"severity": severity, "days": days},
        "count": len(filtered),
        "incidents": filtered,
    }


def get_capacity_report() -> dict:
    data = _load_kpi_data()
    cap = data["capacity"]

    warnings = []
    for resource, info in cap.items():
        util = info.get("utilization_pct") or info.get("avg_utilization_pct", 0)
        if util > 80:
            warnings.append(f"{resource} utilization at {util}% — approaching threshold")

    return {
        "capacity": cap,
        "warnings": warnings,
        "warning_count": len(warnings),
    }
