# imports & setups
import os
import sys
from typing import Any, List, Optional

import streamlit as st
import yaml
from dotenv import load_dotenv
from streamlit.elements.widgets.chat import ChatInputValue
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.exception import MyException
from src.infra.config import ROOT_DIR, load_css
from src.logger import logging

try:
    logging.info("Starting Streamlit application...")
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())

    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = PARAMS_CONFIGS.get("LANGSMITH_PROJECT", "")
    os.environ["LANGSMITH_TRACING_V2"] = str(
        PARAMS_CONFIGS.get("LANGCHAIN_TRACING_V2", "")
    ).lower()

    from src.infra.database import load_conversations, load_thread_mapping
    from src.ui.components.chat import display_messages, handle_input
    from src.ui.components.sidebar import render_sidebar
    from src.ui.state import init_session, new_conversation

    STYLE_CSS = load_css(
        filepath=ROOT_DIR / PARAMS_CONFIGS.get("FILES", {}).get("CSS_FILEPATH", "")
    )

    # title and header
    st.set_page_config(page_title="Flaude", layout="centered")
    if STYLE_CSS:
        st.markdown(STYLE_CSS, unsafe_allow_html=True)
    st.markdown("<h1>Flaude</h1>", unsafe_allow_html=True)

    # init params
    init_session(
        load_conversations=load_conversations, load_thread_mapping=load_thread_mapping
    )

    # display current conversation messages
    display_messages(st.session_state["messages"])

    # new chat button
    if st.sidebar.button(
        "New Conversation",
        icon=":material/add:",
        key="btn_new_chat",
        type="primary",
        use_container_width=True,
    ):
        new_conversation()

    # render sidebar
    st.sidebar.header("Conversations")
    render_sidebar()

    # approval UI
    if st.session_state.get("awaiting_approval", False):
        required_tools: List[Any] = st.session_state.get("required_tools", [])
        if required_tools:
            st.write(
                f"The model requires tool approval before continuing. Required tools: `{', '.join(required_tools)}`"
            )
        else:
            st.write("The model requires tool approval before continuing.")

        resume = None
        col1, col2, _ = st.columns([2, 2, 6])

        with col1:
            if st.button("Approve", type="primary", use_container_width=True):
                resume = True

        with col2:
            if st.button("Reject", use_container_width=True):
                resume = False

        if resume is not None and handle_input(user_input=None, resume=resume):
            st.rerun()

    # input field
    user_input: ChatInputValue | None = st.chat_input(
        "Ask Flaude",
        accept_file=True,
        disabled=st.session_state.get("awaiting_approval", False),
    )
    if user_input:
        try:
            text = user_input.text
        except AttributeError:
            text = user_input

        try:
            files: Optional[List[UploadedFile]] = user_input.files
        except AttributeError:
            files = None

        need_rerun: bool = handle_input(user_input=text, files=files)

        if need_rerun:
            st.rerun()

except Exception as e:
    logging.error(f"Failed to start Streamlit application: {e}")
    raise MyException(e, sys) from e
