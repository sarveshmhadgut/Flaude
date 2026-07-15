import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from src.exception import MyException
from src.logger import logging

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    PROMPTS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/prompts.yaml").read_text())

except Exception as e:
    raise MyException(e, sys) from e


# primitives
def load_css(filepath: Path) -> str:
    """
    Loads custom CSS from a file.

    Args:
        filepath (Path): The Path object pointing to the CSS file.

    Returns:
        str:
            - The CSS string wrapped in an HTML style tag.

    Raises:
        MyException: If the CSS file cannot be read.
    """
    try:
        logging.info(f"Loading CSS from {filepath}...")

        if filepath.exists():
            res: str = f"<style>{filepath.read_text()}</style>"
            logging.info(f"CSS loaded from {filepath}.")
            return res

        logging.warning(f"CSS file not found at {filepath}.")
        return ""

    except Exception as e:
        logging.error(f"Failed to load CSS from {filepath}: {e}")
        raise MyException(e, sys) from e


def get_llm(params: Dict[str, Any]) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI instance.

    Args:
        params (Dict[str, Any]): Dictionary containing LLM configuration parameters.

    Returns:
        ChatGoogleGenerativeAI:
            - The configured language model instance.

    Raises:
        MyException: If initializing the LLM fails.
    """
    try:
        logging.info("Initializing LLM...")
        res: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(**params)

        logging.info("LLM initialized.")
        return res

    except Exception as e:
        logging.error(f"Failed to initialize LLM: {e}")
        raise MyException(e, sys) from e


def get_embeddings(params: Dict[str, Any]) -> GoogleGenerativeAIEmbeddings:
    """
    Initializes and returns the GoogleGenerativeAIEmbeddings instance.

    Args:
        params (Dict[str, Any]): Dictionary containing embedding configuration parameters.

    Returns:
        GoogleGenerativeAIEmbeddings:
            - The configured embeddings instance.

    Raises:
        MyException: If initializing the embeddings model fails.
    """
    try:
        logging.info("Initializing Embedding Model...")
        res: GoogleGenerativeAIEmbeddings = GoogleGenerativeAIEmbeddings(**params)

        logging.info("Embedding Model initialized.")
        return res

    except Exception as e:
        logging.error(f"Failed to initialize Embedding Model: {e}")
        raise MyException(e, sys) from e


# database
def get_conn(db_path: str) -> sqlite3.Connection:
    """
    Establishes a connection to a SQLite database.

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        sqlite3.Connection:
            - The active database connection object.

    Raises:
        MyException: If connecting to the database fails.
    """
    try:
        logging.info(f"Connecting to database at {db_path}...")
        path: Path = ROOT_DIR / db_path
        path.parent.mkdir(parents=True, exist_ok=True)

        conn: sqlite3.Connection = sqlite3.connect(
            database=str(path),
            check_same_thread=False,
        )
        logging.info(f"Connected to database at {db_path}.")
        return conn

    except Exception as e:
        logging.error(f"Failed to connect to database at {db_path}: {e}")
        raise MyException(e, sys) from e


# runnable
def get_runnable_config(
    thread_id: str, thread_name: str, user_id: str = "default_user"
) -> RunnableConfig:
    """
    Constructs a LangGraph RunnableConfig object with session metadata.

    Args:
        thread_id (str): The unique identifier for the conversation thread.
        thread_name (str): The title of the conversation thread.
        user_id (str, optional): The ID of the user. Defaults to "default_user".

    Returns:
        RunnableConfig:
            - The configuration object for LangGraph execution.

    Raises:
        MyException: If constructing the configuration fails.
    """

    try:
        logging.info(
            f"Configuring run context for thread {thread_id} and user {user_id}..."
        )
        res = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "user_id": user_id,
            },
            metadata={
                "thread_id": thread_id,
                "thread_name": thread_name,
                "user_id": user_id,
                "environment": os.getenv("APP_ENV", "default"),
                "app": "flaude",
            },
            run_name="flaude_turn",
        )

        logging.info(f"Run context configured for thread {thread_id}.")
        return res

    except Exception as e:
        logging.error(f"Failed to configure run context for thread {thread_id}: {e}")
        raise MyException(e, sys) from e
