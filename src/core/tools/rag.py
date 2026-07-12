import sys
from typing import Any, Dict

import yaml
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from src.exception import MyException
from src.infra.config import ROOT_DIR, get_embeddings
from src.logger import logging

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    VECTOR_DB_PATH = str(
        ROOT_DIR / PARAMS_CONFIGS.get("FILES", {}).get("VECTOR_DB_PATH", "")
    )
except Exception as e:
    raise MyException(e, sys) from e


@tool(name_or_callable="rag")
def rag_tool(query: str, config: RunnableConfig) -> Dict[str, Any]:
    """
    Search the document database for information related to the query.
    Args:
        query: Search query for the RAG database.
    """
    try:
        logging.info(f"Executing rag_tool for {query}...")

        current_thread = config["configurable"]["thread_id"]
        embeddings = get_embeddings(params=PARAMS_CONFIGS.get("EMBEDDINGS", {}))
        vector_store = Chroma(
            collection_name=current_thread,
            embedding_function=embeddings,
            persist_directory=VECTOR_DB_PATH,
        )
        retriever = vector_store.as_retriever(**PARAMS_CONFIGS.get("RETRIEVER", {}))

        res = retriever.invoke(input=query)
        content = [doc.page_content for doc in res]
        metadata = [doc.metadata for doc in res]

        logging.info(f"Finished executing rag_tool for {query}.")
        return {
            "status": "success",
            "content": content,
            "metadata": metadata,
        }

    except Exception as e:
        logging.error(f"Failed to execute rag_tool : {e}")
        raise MyException(e, sys) from e
