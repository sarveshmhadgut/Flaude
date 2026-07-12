import sys
from uuid import uuid1

import streamlit as st
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.types import Command
from langsmith import get_current_run_tree, traceable

from src.core.capabilities.title_gen import generate_title
from src.core.workflow.graph import workflow
from src.exception import MyException
from src.infra.config import get_runnable_config
from src.infra.database import save_file
from src.logger import logging


def display_messages(messages):
    try:
        logging.info("Executing display_messages...")

        for message in messages:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.markdown(
                        f'<div class="user-message">{message["content"]}</div>',
                        unsafe_allow_html=True,
                    )

                else:
                    st.write(message["content"])
        logging.info("display_messages execution complete.")

    except Exception as e:
        logging.error(f"Error in display_messages: {e}")
        raise MyException(e, sys) from e


def stream_chat(
    user_input, config, stream_mode="messages", status_holder=None, resume=None
):
    try:
        logging.info("Executing stream_chat...")
        input_data = (
            Command(resume=resume)
            if resume is not None
            else {
                "messages": [
                    HumanMessage(
                        content=user_input,
                        id=str(uuid1()),
                    )
                ]
            }
        )

        for message_chunk, metadata in workflow.stream(
            input=input_data,
            config=config,
            stream_mode=stream_mode,
        ):
            if isinstance(message_chunk, AIMessageChunk):
                content = message_chunk.content
                yield (
                    content
                    if isinstance(content, str)
                    else "".join(
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in content
                    )
                    if content
                    else ""
                )

            if isinstance(message_chunk, ToolMessage):
                tool_name = getattr(message_chunk, "name", "tool")
                if status_holder["box"] is None:
                    status_holder["box"] = st.status(
                        f"Using `{tool_name}` …", expanded=True
                    )
                else:
                    status_holder["box"].update(
                        label=f"Using `{tool_name}` ...",
                        state="running",
                        expanded=True,
                    )
        logging.info("stream_chat execution complete.")
    except Exception as e:
        logging.error(f"Error in stream_chat: {e}")
        raise MyException(e, sys) from e


@traceable(name="flaude_run")
def handle_input(user_input, files=None, resume=None):
    try:
        logging.info("Executing handle_input...")
        need_rerun = False

        if files:
            file = files[0] if isinstance(files, list) else files

            with st.chat_message("assistant"):
                save_file(file)

            if not user_input:
                user_input = f"Uploaded document: {file.name}"

        if not user_input and resume is None:
            logging.info("handle_input execution complete (no input).")
            return need_rerun

        if resume is None:
            st.session_state["messages"].append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(
                    f'<div class="user-message">{user_input}</div>',
                    unsafe_allow_html=True,
                )

        thread_id = st.session_state["current_thread"]
        thread_name = st.session_state["thread_mapping"].get(
            thread_id, f"Conversation {thread_id[:8]}"
        )

        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.add_metadata({"thread_id": thread_id})

        config = get_runnable_config(
            thread_id=thread_id,
            thread_name=thread_name,
            user_id=st.session_state.get("user_id", "default_user"),
        )
        with st.chat_message("assistant"):
            tool_block = {"box": None}
            ai_message = st.write_stream(
                stream_chat(
                    user_input=user_input,
                    config=config,
                    stream_mode="messages",
                    status_holder=tool_block,
                    resume=resume,
                )
            )

            if not ai_message and resume is False:
                ai_message = "Tool execution was rejected."
                st.write(ai_message)
                workflow.update_state(
                    config,
                    {
                        "messages": [
                            AIMessage(
                                content=ai_message,
                                id=str(uuid1()),
                            )
                        ]
                    },
                )

            if tool_block["box"] is not None:
                tool_block["box"].update(
                    label="Tool finished",
                    state="complete",
                    expanded=False,
                )

        if ai_message:
            st.session_state["messages"].append(
                {"role": "assistant", "content": ai_message}
            )

        state = workflow.get_state(config)
        is_interrupted = len(state.tasks) > 0 and bool(state.tasks[0].interrupts)
        if is_interrupted != st.session_state.get("awaiting_approval", False):
            st.session_state["awaiting_approval"] = is_interrupted
            if is_interrupted:
                try:
                    interrupt_val = state.tasks[0].interrupts[0].value
                    st.session_state["required_tools"] = interrupt_val.get(
                        "required_tools", []
                    )
                except Exception:
                    st.session_state["required_tools"] = []
            need_rerun = True

        if run_tree:
            run_tree.end(outputs={"ai_response": ai_message})

        if not st.session_state["thread_mapping"].get(
            st.session_state["current_thread"]
        ):
            new_title = generate_title(
                thread_id=st.session_state["current_thread"],
                conversation_history=st.session_state["messages"][:2],
            )

            st.session_state["thread_mapping"][st.session_state["current_thread"]] = (
                new_title
            )
            need_rerun = True

        logging.info("handle_input execution complete.")
        return need_rerun
    except Exception as e:
        logging.error(f"Error in handle_input: {e}")
        raise MyException(e, sys) from e
