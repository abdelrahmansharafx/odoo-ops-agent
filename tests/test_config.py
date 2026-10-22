import pytest

from odoo_agent import config


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for k in ("LLM_PROVIDER", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def test_default_follows_present_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert config.resolve_provider() == "gemini"
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert config.resolve_provider() == "openai"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert config.resolve_provider() == "anthropic"


def test_explicit_provider_wins(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    assert config.resolve_provider() == "gemini"


def test_no_key_and_bad_provider(monkeypatch):
    with pytest.raises(RuntimeError):
        config.resolve_provider()
    monkeypatch.setenv("LLM_PROVIDER", "nope")
    with pytest.raises(ValueError):
        config.resolve_provider()


def test_gemini_builds_chat_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert type(config.get_llm()).__name__ == "ChatGoogleGenerativeAI"
