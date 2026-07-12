import sys
from typing import List, Tuple

import yaml
from langgraph.store.postgres import PostgresStore
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
    importance: float = Field(
        description=PARAMS_CONFIGS.get("MemorySchema", {}).get("IMPORTANCE")
    )


class DecisionSchema(BaseModel):
    update_memory: bool = Field(
        description=PARAMS_CONFIGS.get("DecisionSchema", {}).get("UPDATE_MEMORY")
    )
    memories: List[MemorySchema] = Field(
        description=PARAMS_CONFIGS.get("DecisionSchema", {}).get("MEMORIES")
    )


def get_namespace(user_id: str) -> Tuple[str, str]:
    try:
        res = ("user_id", user_id)
        return res

    except Exception as e:
        raise MyException(e, sys) from e


def get_memories(namespace: Tuple[str, str], store: PostgresStore) -> str:
    try:
        logging.info(f"Fetching memories for namespace: {namespace}...")

        items = store.search(namespace=namespace)
        if not items:
            logging.info(f"No memories found for namespace: {namespace}.")
            return "No memories available."

        memories = "\n".join(
            f"{item.key}: {item.value['text']} ({item.value['importance']})"
            for item in items
        )

        logging.info(f"Fetched memories for namespace: {namespace}.")
        return memories

    except Exception as e:
        logging.error(f"Failed to fetch memories for namespace: {namespace}: {e}")
        raise MyException(e, sys) from e
