import sys
import uuid

import streamlit as st

from src.exception import MyException
from src.logger import logging


def new_conversation():
    try:
        logging.info("Creating New Conversation...")

        thread_id = str(uuid.uuid1())
        st.session_state["current_thread"] = thread_id

        if thread_id not in st.session_state["threads"]:
            st.session_state["threads"].append(thread_id)
        st.session_state["messages"] = []

        logging.info("New Conversation created.")
        st.rerun()

    except Exception as e:
        logging.error(f"Error in creating New Conversation: {e}")
        raise MyException(e, sys) from e


def init_session(load_conversations, load_thread_mapping):
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
