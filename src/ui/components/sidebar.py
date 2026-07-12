import sys

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.core.capabilities.rag import get_retriever
from src.core.workflow.graph import workflow
from src.exception import MyException
from src.infra.config import get_runnable_config
from src.logger import logging


def load_conversation_history(thread_id):
    try:
        logging.info(f"Executing load_conversation_history for {thread_id}...")
        thread_name = st.session_state["thread_mapping"].get(
            thread_id, f"Conversation {thread_id[:8]}"
        )
        state = workflow.get_state(
            config=get_runnable_config(
                thread_id=thread_id,
                thread_name=thread_name,
                user_id=st.session_state.get("user_id", "default_user"),
            )
        )
        logging.info(f"load_conversation_history execution complete for {thread_id}.")
        return state.values.get("messages", [])

    except Exception as e:
        logging.error(f"Error in load_conversation_history: {e}")
        raise MyException(e, sys) from e


def render_conversations():
    try:
        logging.info("Executing render_conversations...")
        for thread in reversed(st.session_state["threads"]):
            title = st.session_state["thread_mapping"].get(thread, "")

            if title and st.sidebar.button(
                title,
                icon=":material/chat:",
                key=f"btn_{thread}",
                use_container_width=True,
            ):
                logging.info(f"Switching to conversation thread: {thread}...")
                st.session_state["current_thread"] = thread
                conversation_history = load_conversation_history(
                    thread_id=st.session_state["current_thread"]
                )

                retriever = get_retriever(thread)
                vector_store = retriever.vectorstore

                if vector_store._collection.count() > 0:
                    db_data = vector_store.get(limit=1)
                    metadata = (
                        db_data["metadatas"][0]
                        if db_data["metadatas"] and db_data["metadatas"][0]
                        else {}
                    )
                    filepath = metadata.get("source", "Unknown Document")
                    st.session_state["metadatas"][thread] = {"filepath": filepath}

                previous_messages = []

                for message in conversation_history:
                    if isinstance(message, HumanMessage):
                        previous_messages.append(
                            {"role": "user", "content": str(message.content)}
                        )

                    elif isinstance(message, AIMessage):
                        content = message.content
                        content = (
                            content
                            if isinstance(content, str)
                            else "".join(
                                b.get("text", "") if isinstance(b, dict) else str(b)
                                for b in content
                            )
                            if content
                            else ""
                        )
                        if content:
                            previous_messages.append(
                                {"role": "assistant", "content": content}
                            )

                st.session_state["messages"] = previous_messages
                st.rerun()
        logging.info("render_conversations execution complete.")

    except Exception as e:
        logging.error(f"Error in render_conversations: {e}")
        raise MyException(e, sys) from e


def render_active_documents():
    try:
        logging.info("Executing render_active_documents...")
        st.sidebar.header("Active Documents")

        current_thread = st.session_state["current_thread"]
        if current_thread in st.session_state.get("metadatas", {}):
            metadata = st.session_state["metadatas"][current_thread]

            filename = metadata["filepath"].split("/")[-1]
            st.sidebar.button(
                filename,
                icon=":material/description:",
                key=f"active_doc_{current_thread}",
                use_container_width=True,
            )
        else:
            st.sidebar.caption("No documents loaded for this conversation.")
        logging.info("render_active_documents execution complete.")
    except Exception as e:
        logging.error(f"Error in render_active_documents: {e}")
        raise MyException(e, sys) from e


def render_sidebar():
    try:
        logging.info("Executing render_sidebar...")
        render_conversations()
        render_active_documents()
        logging.info("render_sidebar execution complete.")
    except Exception as e:
        logging.error(f"Error in render_sidebar: {e}")
        raise MyException(e, sys) from e
