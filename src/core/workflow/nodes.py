import sys
from datetime import datetime
from typing import Any, Dict, Literal, Tuple

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from langsmith import traceable

from src.core.agents.chains import (
    CHAT_CHAIN,
    MEMORY_CHAIN,
    PARAMS_CONFIGS,
    SUMMARY_CHAIN,
)
from src.core.capabilities.memory import PostgresStore, get_memories, get_namespace
from src.core.tools import available_tools
from src.core.workflow.state import MessagesState
from src.exception import MyException
from src.logger import logging


@traceable(name="memory")
def memory(state: MessagesState, config: RunnableConfig, store: PostgresStore) -> Dict:
    try:
        logging.info("Executing memory module...")
        user_id = config["configurable"]["user_id"]
        namespace = get_namespace(user_id=user_id)

        recent_message = next(
            message.content
            for message in reversed(state["messages"])
            if isinstance(message, HumanMessage)
        )
        current_memories = get_memories(namespace=namespace, store=store)

        res = MEMORY_CHAIN.invoke(
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
def chat(
    state: MessagesState, config: RunnableConfig, store: PostgresStore
) -> Dict[str, Any]:
    try:
        logging.info("Processing chat interaction...")

        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"]["user_id"]

        namespace = get_namespace(user_id=user_id)
        current_memories = get_memories(namespace=namespace, store=store)

        active_file = "None"
        if thread_id in st.session_state.get("metadatas", {}):
            metadata = st.session_state["metadatas"][thread_id]
            if "filepath" in metadata:
                active_file = metadata["filepath"].split("/")[-1]

        res = CHAT_CHAIN.invoke(
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


use_tools = ToolNode(tools=available_tools)


@traceable(name="approve_tools")
def approve_tools(
    state: MessagesState, config: RunnableConfig
) -> Command[Literal["use_tools", "__end__"]]:
    try:
        logging.info("Verifying tools execution approvals...")
        recent_message = next(
            message
            for message in reversed(state["messages"])
            if isinstance(message, AIMessage)
        )

        required_tools = [tool_call["name"] for tool_call in recent_message.tool_calls]
        approved = interrupt(
            {
                "type": "approval",
                "reason": "The model requires tool(s) approval.",
                "required_tools": required_tools,
            }
        )

        if approved:
            logging.info("Tools execution approved.")
            return Command(goto="use_tools")

        logging.info("Tools execution denied.")
        return Command(goto=END)

    except Exception as e:
        logging.error(f"Failed to verify tools execution approvals: {e}")
        raise MyException(e, sys) from e


@traceable(name="summarize")
def summarize(
    state: MessagesState, config: RunnableConfig, store: PostgresStore
) -> Command[Tuple]:
    try:
        logging.info("Summarizing message history...")
        current_summary = state.get("messages_summary", "")

        updated_summary = SUMMARY_CHAIN.invoke(
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
                "messages": [
                    RemoveMessage(id=message.id) for message in state["messages"][:-4]
                ],
            },
            graph=Command.PARENT,
        )

    except Exception as e:
        logging.error(f"Failed to summarize message history: {e}")
        raise MyException(e, sys) from e


@traceable(name="route_summary")
def route_summary(state: MessagesState) -> Command[Literal["summarize", "__end__"]]:
    try:
        logging.info("Evaluating message payload for summarization...")
        current_tokens = count_tokens_approximately(messages=state["messages"])

        if current_tokens > PARAMS_CONFIGS.get("MAX_TOKENS", 4000):
            logging.info("Token threshold exceeded; routing to summarization module.")
            return Command(goto="summarize")

        logging.info("Token count within limits; summarization bypassed.")
        return Command(goto=END)

    except Exception as e:
        logging.error(f"Failed to evaluate summarization requirements: {e}")
        raise MyException(e, sys) from e
