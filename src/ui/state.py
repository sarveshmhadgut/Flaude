import sys
import uuid
from typing import Any

import streamlit as st

from src.exception import MyException
from src.logger import logging


def new_conversation() -> None:
    """
    Initializes a new conversation by resetting the session state variables.



    Raises:
        MyException: If resetting the session state fails.
    """
    try:
        logging.info("Creating New Conversation...")

        thread_id: str = str(uuid.uuid1())
        st.session_state["current_thread"] = thread_id

        if thread_id not in st.session_state["threads"]:
            st.session_state["threads"].append(thread_id)
        st.session_state["messages"] = []

        logging.info("New Conversation created.")
        st.rerun()

    except Exception as e:
        logging.error(f"Error in creating New Conversation: {e}")
        raise MyException(e, sys) from e


def init_session(load_conversations: Any, load_thread_mapping: Any) -> None:
    """
    Initializes the global Streamlit session state and loads user history on startup.

    Args:
        load_conversations (Any): Callable to load conversation history from the database.
        load_thread_mapping (Any): Callable to load thread title mappings from the database.


    Raises:
        MyException: If session initialization fails.
    """
    try:
        logging.info("Initializing Session State...")

        if "threads" not in st.session_state:
            st.session_state["threads"] = load_conversations()

        if "thread_mapping" not in st.session_state:
            st.session_state["thread_mapping"] = load_thread_mapping()

        if "current_thread" not in st.session_state:
            new_conversation()

        if "messages" not in st.session_state:
            st.session_state["messages"] = []

        if "retrievers" not in st.session_state:
            st.session_state["retrievers"] = {}

        if "metadatas" not in st.session_state:
            st.session_state["metadatas"] = {}

        logging.info("Session State initialized.")

    except Exception as e:
        logging.error(f"Error in Session State initialization: {e}")
        raise MyException(e, sys) from e
