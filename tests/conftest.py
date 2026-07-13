import os

import pytest

# Set safe dummy environment variables for test collection and execution
os.environ["GOOGLE_API_KEY"] = "goofy-ahh-google-key"
os.environ["LANGCHAIN_API_KEY"] = "goofy-ahh-langchain-key"
os.environ["DB_USER"] = "admin"
os.environ["DB_PASSWORD"] = "admin"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "test_db"
os.environ["DB_URI"] = "postgresql://postgresql:postgresql@localhost:5432/postgresql"

from unittest.mock import MagicMock
import psycopg_pool
import langgraph.checkpoint.postgres
import langgraph.store.postgres

# Prevent DB connection during test collection module imports
psycopg_pool.ConnectionPool = MagicMock()
langgraph.checkpoint.postgres.PostgresSaver.setup = MagicMock()
langgraph.checkpoint.postgres.PostgresSaver.list = MagicMock(return_value=[])
langgraph.store.postgres.PostgresStore.setup = MagicMock()

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
    monkeypatch.setenv("DB_URI", "postgresql://postgresql:postgresql@localhost:5432/postgresql")
