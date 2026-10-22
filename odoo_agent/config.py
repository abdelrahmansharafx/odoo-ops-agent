"""Environment-driven configuration and LLM factory."""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini", "gemini": "gemini-2.0-flash"}


def resolve_provider() -> str:
    """LLM_PROVIDER wins; otherwise whichever API key is present (Anthropic first)."""
    explicit = os.getenv("LLM_PROVIDER", "").strip().lower()
    if explicit:
        if explicit not in DEFAULT_MODELS:
            raise ValueError(f"LLM_PROVIDER must be one of {sorted(DEFAULT_MODELS)}, got {explicit!r}")
        return explicit
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    raise RuntimeError("No LLM key found: set ANTHROPIC_API_KEY, OPENAI_API_KEY or GEMINI_API_KEY in .env")


def get_llm(model_env: str = "LLM_MODEL", temperature: float = 0):
    """Build a LangChain chat model. `model_env` lets the eval judge use its own model name."""
    provider = resolve_provider()
    model = os.getenv(model_env) or os.getenv("LLM_MODEL") or DEFAULT_MODELS[provider]
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, temperature=temperature, max_tokens=2048)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=key)
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, temperature=temperature)


def setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
