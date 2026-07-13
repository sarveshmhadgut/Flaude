import sys
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import tools_condition
from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool

from src.core.agents.chains import DB_URI
from src.core.workflow.nodes import approve_tools, chat, memory, route_summary, summarize, use_tools
from src.core.workflow.state import MessagesState
from src.exception import MyException
from src.infra.config import PARAMS_CONFIGS, get_embeddings
from src.logger import logging


def compile_workflow(checkpointer: PostgresSaver, store: PostgresStore) -> CompiledStateGraph:
    """
    Builds and compiles the main LangGraph state machine for the application.

    Args:
        checkpointer (PostgresSaver): The checkpoint saver for maintaining state.
        store (PostgresStore): The PostgreSQL store instance for long-term memory.

    Returns:
        CompiledStateGraph:
            - The fully compiled and runnable LangGraph workflow.

    Raises:
        MyException: If the graph compilation process fails.
    """
    try:
        logging.info("Compiling graph workflow...")

        # tools workflow
        tools_subgraph: StateGraph = StateGraph(MessagesState)
        tools_subgraph.add_node(node="approve_tools", action=approve_tools)
        tools_subgraph.add_node(node="use_tools", action=use_tools)

        tools_subgraph.add_edge(start_key=START, end_key="approve_tools")
        tools_subgraph.add_edge(start_key="use_tools", end_key=END)
        tools_workflow: CompiledStateGraph = tools_subgraph.compile(checkpointer=checkpointer)

        # summary workflow
        summary_subgraph: StateGraph = StateGraph(MessagesState)
        summary_subgraph.add_node(node="summarize", action=summarize)
        summary_subgraph.add_node(node="route_summary", action=route_summary)

        summary_subgraph.add_edge(start_key=START, end_key="route_summary")
        summary_subgraph.add_edge(start_key="summarize", end_key=END)
        summary_workflow: CompiledStateGraph = summary_subgraph.compile(checkpointer=checkpointer)

        # main workflow
        main_graph: StateGraph = StateGraph(MessagesState)
        main_graph.add_node(node="chat", action=chat)
        main_graph.add_node(node="memory", action=memory)
        main_graph.add_node(node="tools_workflow", action=tools_workflow)
        main_graph.add_node(node="summary_workflow", action=summary_workflow)

        main_graph.add_edge(start_key=START, end_key="memory")
        main_graph.add_edge(start_key="memory", end_key="chat")
        main_graph.add_conditional_edges(
            source="chat",
            path=tools_condition,
            path_map={
                "tools": "tools_workflow",
                "__end__": "summary_workflow",
            },
        )
        main_graph.add_edge(start_key="tools_workflow", end_key="chat")
        main_graph.add_edge(start_key="summary_workflow", end_key=END)

        # compiled workflow
        workflow: CompiledStateGraph = main_graph.compile(checkpointer=checkpointer, store=store)
        logging.info("Graph workflow compiled.")
        return workflow

    except Exception as e:
        logging.error(f"Failed to compile graph workflow: {e}")
        raise MyException(e, sys) from e


try:
    logging.info("Initializing PostgreSQL connection pool...")
    if not DB_URI:
        raise ValueError("DB_URI is required.")
    pool: Any = ConnectionPool(conninfo=DB_URI, kwargs={"autocommit": True})
    logging.info("PostgreSQL connection pool initialized.")

    logging.info("Setting up PostgreSQL checkpointer...")
    checkpointer = PostgresSaver(conn=pool)
    checkpointer.setup()
    logging.info("PostgreSQL checkpointer setup completed.")

    logging.info("Setting up PostgreSQL store...")
    store = PostgresStore(
        conn=pool,
        index={
            "dims": 768,
            "embed": get_embeddings(params=PARAMS_CONFIGS.get("EMBEDDINGS", {})),
        },
    )
    store.setup()
    logging.info("PostgreSQL store setup completed.")

    workflow: CompiledStateGraph = compile_workflow(checkpointer=checkpointer, store=store)

except Exception as e:
    logging.error(f"Failed to initialize graph database components: {e}")
    raise MyException(e, sys) from e
