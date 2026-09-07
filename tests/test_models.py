"""make_model이 .env의 MODEL_NAME을 반영하는지 확인한다."""

from adk_study.models import DEFAULT_MODEL, make_model


def test_default_model_when_env_missing(monkeypatch):
    monkeypatch.delenv("MODEL_NAME", raising=False)
    model = make_model()
    assert model.model == f"openai/{DEFAULT_MODEL}"


def test_model_name_from_env(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "gpt-4o")
    model = make_model()
    assert model.model == "openai/gpt-4o"
