import sys
from typing import List, Tuple

import yaml
from langgraph.store.base import BaseStore, SearchItem
from pydantic import BaseModel, Field

from src.exception import MyException
from src.infra.config import ROOT_DIR
from src.logger import logging

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    PROMPTS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/prompts.yaml").read_text())
except Exception as e:
    raise MyException(e, sys) from e


class MemorySchema(BaseModel):
    key: str = Field(description=PARAMS_CONFIGS.get("MemorySchema", {}).get("KEY"))
    value: str = Field(description=PARAMS_CONFIGS.get("MemorySchema", {}).get("VALUE"))
    importance: float = Field(description=PARAMS_CONFIGS.get("MemorySchema", {}).get("IMPORTANCE"))


class DecisionSchema(BaseModel):
    update_memory: bool = Field(description=PARAMS_CONFIGS.get("DecisionSchema", {}).get("UPDATE_MEMORY"))
    memories: List[MemorySchema] = Field(description=PARAMS_CONFIGS.get("DecisionSchema", {}).get("MEMORIES"))


def get_namespace(user_id: str) -> Tuple[str, str]:
    """
    Constructs the memory namespace for a specific user.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        Tuple[str, str]:
            - The tuple containing the user namespace string.

    Raises:
        MyException: If constructing the namespace fails.
    """
    try:
        res: Tuple[str, str] = ("user_id", user_id)
        return res

    except Exception as e:
        raise MyException(e, sys) from e


def get_memories(namespace: Tuple[str, str], store: BaseStore, query: str | None = None, limit: int = 5) -> str:
    """
    Retrieves and formats memories from the PostgreSQL store for a given user.

    When query is None all memories in the namespace are returned (original
    behaviour, useful as a fallback).

    Args:
        namespace (Tuple[str, str]): The namespace tuple to fetch memories for.
        store (BaseStore): The initialized BaseStore instance.
        query (str | None): Optional natural-language query used for semantic
            search. Defaults to None (full scan).
        limit (int): Maximum number of memories to return. Defaults to 5.

    Returns:
        str:
            - A formatted string of retrieved memories, or a placeholder if none exist.

    Raises:
        MyException: If retrieving memories fails.
    """
    try:
        logging.info(f"Fetching memories for namespace: {namespace}...")

        search_kwargs: dict = {"limit": limit}
        if query:
            search_kwargs["query"] = query

        items: List[SearchItem] = store.search(namespace, **search_kwargs)
        if not items:
            logging.info(f"No memories found for namespace: {namespace}.")
            return "No memories available."

        memories: str = "\n".join(f"{item.key}: {item.value['text']} ({item.value['importance']})" for item in items)

        logging.info(f"Fetched memories for namespace: {namespace}.")
        return memories

    except Exception as e:
        logging.error(f"Failed to fetch memories for namespace: {namespace}: {e}")
        raise MyException(e, sys) from e
