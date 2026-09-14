def test_deps_import():
    import lancedb  # noqa: F401
    import openai  # noqa: F401
    import dotenv  # noqa: F401


def test_config_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    from dnd5e_engine import config
    assert config.embedding_model() == "text-embedding-3-large"


def test_config_model_override(monkeypatch):
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    from dnd5e_engine import config
    assert config.embedding_model() == "text-embedding-3-small"
