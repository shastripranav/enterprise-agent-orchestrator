"""Planning domain tools — roadmap, resources, timelines, and risk assessment."""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_roadmap_cache: dict | None = None


def _load_roadmap_data() -> dict:
    global _roadmap_cache
    if _roadmap_cache is None:
        with open(_DATA_DIR / "mock_roadmap.json") as f:
            _roadmap_cache = json.load(f)
    return _roadmap_cache


def get_product_roadmap(quarter: str | None = None) -> dict:
    data = _load_roadmap_data()
    roadmap = data["roadmap"]

    if quarter:
        quarter = quarter.upper()
        if quarter not in roadmap:
            return {"error": f"No roadmap for {quarter}. Available: {list(roadmap.keys())}"}
        return {"quarter": quarter, **roadmap[quarter]}

    summary = {}
    for qtr, info in roadmap.items():
        summary[qtr] = {
            "theme": info["theme"],
            "initiative_count": len(info["initiatives"]),
            "initiatives": [
                {"name": i["name"], "status": i["status"], "progress_pct": i["progress_pct"]}
                for i in info["initiatives"]
            ],
        }
    return {"fiscal_year": data["fiscal_year"], "quarters": summary}


def get_resource_allocation(team: str | None = None) -> dict:
    data = _load_roadmap_data()
    alloc = data["resource_allocation"]

    if team:
        matches = {k: v for k, v in alloc.items() if team.lower() in k.lower()}
        if not matches:
            return {"error": f"No team matching '{team}'. Available: {list(alloc.keys())}"}
        return {"teams": matches}

    # overall headcount and utilization
    total_hc = sum(t["headcount"] for t in alloc.values())
    return {
        "total_headcount": total_hc,
        "team_count": len(alloc),
        "teams": {
            name: {"headcount": info["headcount"], "project_count": len(info["projects"])}
            for name, info in alloc.items()
        },
    }


def get_project_timeline(project: str | None = None) -> dict:
    """Return milestones for a specific project or a summary of all tracked projects."""
    data = _load_roadmap_data()
    timelines = data["project_timelines"]

    if project:
        # try exact match first, then fuzzy
        match = timelines.get(project)
        if not match:
            match = next(
                (v for k, v in timelines.items() if project.lower() in k.lower()),
                None,
            )
        if not match:
            return {
                "error": f"No timeline for '{project}'. Tracked: {list(timelines.keys())}",
            }
        return match

    return {
        "tracked_projects": len(timelines),
        "projects": {
            pid: {
                "name": info["name"],
                "milestone_count": len(info["milestones"]),
                "next_milestone": next(
                    (m for m in info["milestones"] if m["status"] != "completed"),
                    None,
                ),
            }
            for pid, info in timelines.items()
        },
    }


def get_risk_assessment() -> dict:
    data = _load_roadmap_data()
    risks = data["risks"]

    by_category = {}
    for r in risks:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r)

    high_impact = [r for r in risks if r["impact"] in ("high", "critical")]

    return {
        "total_risks": len(risks),
        "high_impact_count": len(high_impact),
        "by_category": {cat: len(items) for cat, items in by_category.items()},
        "risks": risks,
    }
