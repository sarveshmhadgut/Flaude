from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from src.core.workflow.nodes import approve_tools, chat, summarize


def test_approve_tools() -> None:
    """Test that the approve_tools node correctly interrupts the graph."""
    # Simulate tool request state
    state = {
        "messages": [
            AIMessage(
                content="Need approval",
                tool_calls=[{"name": "web_search", "args": {}, "id": "call_67"}],
            )
        ]
    }
    config = {"configurable": {"thread_id": "thread_67"}}

    # Node should interrupt for human approval
    with patch("src.core.workflow.nodes.interrupt") as mock_interrupt:
        from langgraph.errors import GraphInterrupt
        from langgraph.types import Interrupt

        mock_interrupt.side_effect = GraphInterrupt([Interrupt(value="mock interrupt")])

        with pytest.raises(GraphInterrupt):
            approve_tools(state, config)


def test_chat_node() -> None:
    """Test the chat node's ability to process messages and return a response."""
    state = {"messages": [HumanMessage(content="Hello")]}
    config = {"configurable": {"thread_id": "thread_67", "user_id": "user_67"}}
    mock_store = MagicMock()

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = AIMessage(content="Hi there")

    # Mock dependencies to isolate chat node
    with (
        patch("src.core.workflow.nodes.CHAT_CHAIN", mock_chain),
        patch(
            "src.core.workflow.nodes.get_namespace", return_value=("user_id", "user_67")
        ),
        patch("src.core.workflow.nodes.get_memories", return_value="some memory"),
    ):
        # Mock session state for RAG checks
        with patch("streamlit.session_state", {}):
            result = chat(state, config, mock_store)
            assert len(result["messages"]) == 1
            assert result["messages"][0].content == "Hi there"


def test_summarize() -> None:
    """Test the summarize node's ability to summarize long conversations."""
    # Simulate long conversation
    state = {"messages": [HumanMessage(content="A" * 100)] * 10, "messages_summary": ""}
    config = {"configurable": {"thread_id": "test"}}
    mock_store = MagicMock()

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "This is a summary"

    # Mock summary chain and force high token count
    with (
        patch("src.core.workflow.nodes.SUMMARY_CHAIN", mock_chain),
        patch("src.core.workflow.nodes.count_tokens_approximately", return_value=8500),
    ):
        result = summarize(state, config, mock_store)

        assert hasattr(result, "update") or result is not None
