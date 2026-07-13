from unittest.mock import MagicMock

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.state import CompiledStateGraph

from src.core.workflow.graph import compile_workflow


def test_graph_compiled() -> None:
    """Test that the workflow graph compiles successfully."""
    mock_checkpointer = MagicMock(spec=PostgresSaver)
    mock_store = MagicMock()

    workflow = compile_workflow(mock_checkpointer, mock_store)
    assert isinstance(workflow, CompiledStateGraph)


def test_graph_nodes() -> None:
    """Test that the workflow graph contains the expected nodes."""
    mock_checkpointer = MagicMock(spec=PostgresSaver)
    mock_store = MagicMock()

    workflow = compile_workflow(mock_checkpointer, mock_store)
    nodes = workflow.builder.nodes.keys()

    assert "chat" in nodes
    assert "memory" in nodes
    assert "tools_workflow" in nodes
    assert "summary_workflow" in nodes
