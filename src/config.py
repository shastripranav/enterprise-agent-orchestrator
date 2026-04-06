from pydantic_settings import BaseSettings


class OrchestratorConfig(BaseSettings):
    llm_provider: str = "openai"
    llm_model: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    max_iterations: int = 5
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def resolved_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "ollama": "llama3.1",
        }
        return defaults.get(self.llm_provider, "gpt-4o-mini")


_config: OrchestratorConfig | None = None


def get_config() -> OrchestratorConfig:
    global _config
    if _config is None:
        _config = OrchestratorConfig()
    return _config


def reset_config():
    """Used in tests to force config reload."""
    global _config
    _config = None


# Domain keyword sets — shared between routing and supervisor
FINANCE_KEYWORDS = [
    "budget", "revenue", "expense", "forecast", "p&l",
    "cost", "profit", "margin", "spending", "financial",
    "earnings", "cash flow", "roi", "invoice", "payroll",
]

OPERATIONS_KEYWORDS = [
    "kpi", "sla", "incident", "capacity", "uptime",
    "latency", "throughput", "deployment", "monitoring",
    "outage", "alert", "availability", "performance", "downtime",
]

PLANNING_KEYWORDS = [
    "roadmap", "timeline", "resource", "milestone",
    "risk", "strategy", "initiative", "quarter", "priority",
    "objective", "okr", "goal", "deadline", "deliverable",
]
