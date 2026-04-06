"""Factory for creating LLM instances across providers."""

from langchain_core.language_models.chat_models import BaseChatModel

from .config import get_config


def create_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """Build a chat model from config or explicit overrides.

    Supports OpenAI, Anthropic, and local Ollama. Falls back to config
    values when provider/model aren't specified.
    """
    cfg = get_config()
    provider = provider or cfg.llm_provider
    model = model or cfg.resolved_model

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=cfg.openai_api_key or None,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=cfg.anthropic_api_key or None,
        )

    if provider == "ollama":
        # FIXME: ollama import path may change when langchain-ollama stabilizes
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=cfg.ollama_base_url,
        )

    raise ValueError(f"Unknown LLM provider: {provider!r}. Use openai, anthropic, or ollama.")
