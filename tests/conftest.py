import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run with safe dummy environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "goofy-ahh-google-key")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "goofy-ahh-langchain-key")

    monkeypatch.setenv("DB_USER", "admin")
    monkeypatch.setenv("DB_PASSWORD", "admin")

    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
