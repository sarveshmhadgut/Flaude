import sys
from datetime import datetime
from typing import Any, Dict, List, Literal, Tuple

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphInterrupt
from langgraph.graph import END
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Command, interrupt
from langsmith import traceable

from src.core.agents.chains import CHAT_CHAIN, MEMORY_CHAIN, PARAMS_CONFIGS, SUMMARY_CHAIN
from src.core.capabilities.memory import DecisionSchema, get_memories, get_namespace
from src.core.tools import available_tools
from src.core.workflow.state import MessagesState
from src.exception import MyException
from src.logger import logging


@traceable(name="memory")
def memory(state: MessagesState, config: RunnableConfig, store: BaseStore) -> Dict[str, Any]:
    """
    Executes the memory module to fetch and decide if memories need updating.

    Args:
        state (MessagesState): The current state of the workflow messages.
        config (RunnableConfig): Execution configuration.
        store (BaseStore): The PostgreSQL store instance for memories.

    Returns:
        Dict[str, Any]:
            - Returns a dictionary with updated messages or an empty dict.

    Raises:
        MyException: If the memory logic fails to execute.
    """
    try:
        logging.info("Executing memory module...")
        user_id: str = config["configurable"]["user_id"]
        namespace: Tuple[str, str] = get_namespace(user_id=user_id)

        recent_message: Any = next(message.content for message in reversed(state["messages"]) if isinstance(message, HumanMessage))
        current_memories: str = get_memories(
            namespace=namespace,
            store=store,
            query=recent_message,
            limit=PARAMS_CONFIGS.get("MEMORY_SEARCH_K", 5),
        )

        res: DecisionSchema = MEMORY_CHAIN.invoke(
            input={
                "current_memories": current_memories,
                "recent_message": recent_message,
            },
            config=config,
            store=store,
        )

        if res.update_memory:
            for memory in res.memories:
                store.put(
                    namespace=namespace,
                    key=memory.key,
                    value={
                        "text": memory.value,
                        "importance": memory.importance,
                        "metadata": {
                            "user_id": user_id,
                            "source": "user_message",
                            "type": getattr(memory, "type", "default"),
                            "created_at": datetime.now().isoformat(),
                        },
                    },
                )

        logging.info("Finished executing memory module.")
        return {}

    except Exception as e:
        logging.error(f"Failed to execute memory module: {e}")
        raise MyException(e, sys) from e


@traceable(name="chat")
def chat(state: MessagesState, config: RunnableConfig, store: BaseStore) -> Dict[str, Any]:
    """
    Executes the main chat logic, sending context and history to the LLM.

    Args:
        state (MessagesState): The current state of the workflow messages.
        config (RunnableConfig): Execution configuration containing thread and user IDs.
        store (BaseStore): The PostgreSQL store instance for memories.

    Returns:
        Dict[str, Any]:
            - A dictionary containing the newly generated AIMessage.

    Raises:
        MyException: If the chat interaction fails.
    """
    try:
        logging.info("Processing chat interaction...")

        thread_id: str = config["configurable"]["thread_id"]
        user_id: str = config["configurable"]["user_id"]

        namespace: Tuple[str, str] = get_namespace(user_id=user_id)
        recent_message: str = str(next(message.content for message in reversed(state["messages"]) if isinstance(message, HumanMessage)))
        current_memories: str = get_memories(
            namespace=namespace,
            store=store,
            query=recent_message,
            limit=PARAMS_CONFIGS.get("MEMORY_SEARCH_K", 5),
        )

        active_file = "None"
        if thread_id in st.session_state.get("metadatas", {}):
            metadata: Dict[str, Any] = st.session_state["metadatas"][thread_id]
            if "filepath" in metadata:
                active_file = metadata["filepath"].split("/")[-1]

        res: AIMessage = CHAT_CHAIN.invoke(
            input={
                "messages_summary": state.get("messages_summary", ""),
                "active_document": active_file,
                "current_memory": current_memories,
                "messages": state["messages"],
            },
            config=config,
            store=store,
        )

        logging.info("Chat interaction processed.")
        return {"messages": [res]}

    except Exception as e:
        logging.error(f"Failed to process chat interaction: {e}")
        raise MyException(e, sys) from e


use_tools: ToolNode = ToolNode(tools=available_tools)


@traceable(name="approve_tools")
def approve_tools(state: MessagesState, config: RunnableConfig) -> Command[Literal["use_tools", "__end__"]]:
    """
    Checks for tool calls and interrupts the workflow to ask for explicit user approval.

    Args:
        state (MessagesState): The current state containing the AI's tool call requests.
        config (RunnableConfig): Execution configuration.

    Returns:
        Command[Literal["use_tools", "__end__"]]:
            - A LangGraph Command routing to the tool execution node or ending the graph.

    Raises:
        MyException: If the approval step encounters an error.
    """
    try:
        logging.info("Verifying tools execution approvals...")
        recent_message: AIMessage = next(message for message in reversed(state["messages"]) if isinstance(message, AIMessage))

        required_tools: List[str] = [tool_call["name"] for tool_call in recent_message.tool_calls]
        approved = interrupt(
            {
                "type": "approval",
                "reason": "The model requires tool(s) approval.",
                "required_tools": required_tools,
            }
        )

        if approved:
            logging.info("Tools execution approved.")
            use_tools_literal: Literal["use_tools"] = "use_tools"
            return Command(goto=use_tools_literal)

        logging.info("Tools execution denied.")
        end_val: Literal["__end__"] = "__end__"
        return Command(goto=end_val)

    except GraphInterrupt:
        raise
    except Exception as e:
        logging.error(f"Failed to verify tools execution approvals: {e}")
        raise MyException(e, sys) from e


@traceable(name="summarize")
def summarize(state: MessagesState, config: RunnableConfig, store: BaseStore) -> Command[Tuple]:
    """
    Summarizes older messages in the conversation to conserve context length.

    Args:
        state (MessagesState): The current state of the workflow messages.
        config (RunnableConfig): Execution configuration.
        store (BaseStore): The PostgreSQL store instance.

    Returns:
        Command[Tuple]:
            - A Command that deletes old messages and appends the new summary.

    Raises:
        MyException: If summarization fails.
    """
    try:
        logging.info("Summarizing message history...")
        current_summary: str = state.get("messages_summary", "")

        updated_summary: str = SUMMARY_CHAIN.invoke(
            input={
                "messages": state["messages"][-4:],
                "current_summary": current_summary,
            },
            config=config,
            store=store,
        )

        logging.info("Message history summarized.")
        return Command(
            update={
                "messages_summary": updated_summary,
                "messages": [RemoveMessage(id=str(message.id)) for message in state["messages"][:-4]],
            },
            graph=Command.PARENT,
        )

    except Exception as e:
        logging.error(f"Failed to summarize message history: {e}")
        raise MyException(e, sys) from e


@traceable(name="route_summary")
def route_summary(state: MessagesState) -> Command[Literal["summarize", "__end__"]]:
    """
    Routes the workflow to the summarize node if the conversation is getting too long.

    Args:
        state (MessagesState): The current state of the workflow messages.

    Returns:
        Command[Literal["summarize", "__end__"]]:
            - A LangGraph Command directing to "summarize" or terminating the graph.

    Raises:
        MyException: If token counting or routing fails.
    """
    try:
        logging.info("Evaluating message payload for summarization...")
        current_tokens: int = count_tokens_approximately(messages=state["messages"])

        if current_tokens > PARAMS_CONFIGS.get("MAX_TOKENS", 4000):
            logging.info("Token threshold exceeded; routing to summarization module.")
            summarize_val: Literal["summarize"] = "summarize"
            return Command(goto=summarize_val)

        logging.info("Token count within limits; summarization bypassed.")
        end_val2: Literal["__end__"] = "__end__"
        return Command(goto=end_val2)

    except Exception as e:
        logging.error(f"Failed to evaluate summarization requirements: {e}")
        raise MyException(e, sys) from e
