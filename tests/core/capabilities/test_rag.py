from unittest.mock import MagicMock, patch

from chromadb.errors import NotFoundError
from langchain_core.documents.base import Document

from src.core.capabilities.rag import get_retriever, ingestion_pipeline


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


def test_ingestion_pipeline_non_existent_collection() -> None:
    """Test ingestion pipeline when deleting a non-existent collection raises NotFoundError."""
    mock_doc = Document(page_content="Test cover letter content", metadata={"source": "test.pdf"})
    mock_loader = MagicMock()
    mock_loader.load.return_value = [mock_doc]

    mock_client = MagicMock()
    mock_client.delete_collection.side_effect = NotFoundError("Collection [thread_test] does not exist")

    session_state = {
        "current_thread": "thread_test",
        "retrievers": {},
        "metadatas": {},
    }

    with (
        patch("src.core.capabilities.rag.PyPDFLoader", return_value=mock_loader),
        patch("src.core.capabilities.rag.get_embeddings"),
        patch("src.core.capabilities.rag.chromadb.PersistentClient", return_value=mock_client),
        patch("src.core.capabilities.rag.Chroma.from_documents") as mock_chroma_from_docs,
        patch("streamlit.session_state", session_state),
    ):
        result = ingestion_pipeline(filepath="test.pdf", chunk_size=1000, chunk_overlap=200)

        assert result["docs"] == 1
        assert result["filepath"] == "test.pdf"
        mock_client.delete_collection.assert_called_once_with(name="thread_test")
        mock_chroma_from_docs.assert_called_once()


def test_rag_tool() -> None:
    """Test executing the rag_tool to retrieve document content."""
    from src.core.tools.rag import rag_tool

    mock_doc = Document(page_content="Deep learning question text", metadata={"source": "test.md"})
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [mock_doc]

    mock_chroma = MagicMock()
    mock_chroma.as_retriever.return_value = mock_retriever

    config = {"configurable": {"thread_id": "thread_test"}}

    with (
        patch("src.core.tools.rag.Chroma", return_value=mock_chroma),
        patch("src.core.tools.rag.get_embeddings"),
    ):
        result = rag_tool.invoke({"query": "deep learning questions"}, config=config)
        assert result["status"] == "success"
        assert result["content"] == ["Deep learning question text"]
        assert result["metadata"] == [{"source": "test.md"}]
