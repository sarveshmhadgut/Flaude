import sys
from typing import Any, Dict

import yaml
from langchain_chroma import Chroma
from langchain_core.documents.base import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings

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
    Executes a Retrieval-Augmented Generation (RAG) query against the active vector database.

    Args:
        query (str): The search query to retrieve information for.
        config (RunnableConfig): Execution configuration containing the thread ID.

    Returns:
        Dict[str, Any]:
            - A dictionary containing the retrieved text or an error message.

    Raises:
        MyException: If the RAG retrieval process fails.
    """
    try:
        logging.info(f"Executing rag_tool for {query}...")

        current_thread: str = config["configurable"]["thread_id"]
        embeddings: GoogleGenerativeAIEmbeddings = get_embeddings(
            params=PARAMS_CONFIGS.get("EMBEDDINGS", {})
        )
        vector_store: Chroma = Chroma(
            collection_name=current_thread,
            embedding_function=embeddings,
            persist_directory=VECTOR_DB_PATH,
        )
        retriever: VectorStoreRetriever = vector_store.as_retriever(
            **PARAMS_CONFIGS.get("RETRIEVER", {})
        )

        res: list[Document] = retriever.invoke(input=query)
        content: list[str] = [doc.page_content for doc in res]
        metadata: list[Dict[Any, Any]] = [doc.metadata for doc in res]

        logging.info(f"Finished executing rag_tool for {query}.")
        return {
            "status": "success",
            "content": content,
            "metadata": metadata,
        }

    except Exception as e:
        logging.error(f"Failed to execute rag_tool : {e}")
        raise MyException(e, sys) from e
