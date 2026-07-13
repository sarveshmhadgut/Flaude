from unittest.mock import MagicMock

from langgraph.store.base import SearchItem

from src.core.capabilities.memory import get_memories, get_namespace


def test_get_namespace() -> None:
    """Test getting namespace for a user."""
    assert get_namespace("user_67") == ("user_id", "user_67")


def test_get_memories() -> None:
    """Test retrieving memories from the store."""
    mock_store = MagicMock()
    ns = ("user_id", "user_67")

    # Test empty result
    mock_store.search.return_value = []
    assert get_memories(ns, mock_store) == "No memories available."

    # Test with results
    mock_item = MagicMock(spec=SearchItem)
    mock_item.key = "food_preference"
    mock_item.value = {"text": "Likes cabbage", "importance": 0.8}
    mock_store.search.return_value = [mock_item]

    assert get_memories(ns, mock_store) == "food_preference: Likes cabbage (0.8)"

    # Test with query
    get_memories(ns, mock_store, query="cabbage")
    mock_store.search.assert_called_with(ns, query="cabbage", limit=5)
