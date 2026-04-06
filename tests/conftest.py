import os
import sys
from pathlib import Path

import pytest

# ensure project root is importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# override env for tests — no real API calls
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("MAX_ITERATIONS", "5")


@pytest.fixture(autouse=True)
def reset_caches():
    """Clear module-level caches between tests."""
    from src.tools import finance_tools, operations_tools, planning_tools

    finance_tools._budget_cache = None
    operations_tools._kpi_cache = None
    planning_tools._roadmap_cache = None
    yield


@pytest.fixture
def sample_state():
    from langchain_core.messages import HumanMessage

    from src.state import create_initial_state

    state = create_initial_state()
    state["messages"] = [HumanMessage(content="What's our Q3 budget utilization?")]
    return state
