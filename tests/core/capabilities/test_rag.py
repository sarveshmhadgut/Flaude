from unittest.mock import patch

from src.core.capabilities.rag import get_retriever


def test_get_retriever() -> None:
    """Test initializing and getting the RAG retriever."""
    # Mock dependencies and session state cache
    with (
        patch("src.core.capabilities.rag.Chroma") as mock_chroma,
        patch("src.core.capabilities.rag.get_embeddings"),
        patch("streamlit.session_state", {"retrievers": {}}),
    ):
        get_retriever("thread_67")

        # Verify Chroma initialization
        mock_chroma.assert_called_once()
        mock_chroma.return_value.as_retriever.assert_called_once()
