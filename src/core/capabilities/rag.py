import sys
from pathlib import Path
from typing import Any, Dict

import chromadb
from langchain_core.vectorstores.base import VectorStoreRetriever
import streamlit as st
import yaml
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langsmith import traceable

from src.exception import MyException
from src.infra.config import ROOT_DIR, get_embeddings
from src.logger import logging

try:
    LANGUAGE_MAP = {
        ".md": Language.MARKDOWN,
        ".py": Language.PYTHON,
        ".java": Language.JAVA,
        ".cpp": Language.CPP,
        ".js": Language.JS,
        ".ts": Language.TS,
        ".html": Language.HTML,
    }

    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    VECTOR_DB_PATH = str(
        ROOT_DIR / PARAMS_CONFIGS.get("FILES", {}).get("VECTOR_DB_PATH", "")
    )

except Exception as e:
    raise MyException(e, sys) from e


def get_retriever(thread_id: str) -> VectorStoreRetriever:
    try:
        logging.info(f"Configuring retriever for thread {thread_id}...")
        if thread_id in st.session_state["retrievers"]:
            res = st.session_state["retrievers"].get(thread_id, {})
            logging.info(
                f"Retriever configuration loaded from session for thread {thread_id}."
            )
            return res

        embeddings = get_embeddings(params=PARAMS_CONFIGS.get("EMBEDDINGS", {}))
        vector_store = Chroma(
            collection_name=thread_id,
            embedding_function=embeddings,
            persist_directory=VECTOR_DB_PATH,
        )

        retriever = vector_store.as_retriever(**PARAMS_CONFIGS.get("RETRIEVER", {}))
        st.session_state["retrievers"][thread_id] = retriever

        logging.info(f"Retriever configured for thread {thread_id}.")
        return retriever

    except Exception as e:
        logging.error(f"Failed to configure retriever for thread {thread_id}: {e}")
        raise MyException(e, sys) from e


@traceable(name="ingestion_pipeline")
def ingestion_pipeline(
    filepath: str, chunk_size: int, chunk_overlap: int
) -> Dict[str, Any]:
    try:
        logging.info(f"Starting ingestion pipeline for {filepath}...")
        current_thread = st.session_state["current_thread"]
        ext = Path(filepath).suffix.lower()

        if ext == ".pdf":
            loader = PyPDFLoader(file_path=filepath)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
            )
        else:
            loader = TextLoader(file_path=filepath)
            docs = loader.load()

            if ext in LANGUAGE_MAP:
                splitter = RecursiveCharacterTextSplitter.from_language(
                    language=LANGUAGE_MAP[ext],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", " ", ""],
                )

        chunks = splitter.split_documents(documents=docs)

        embeddings = get_embeddings(params=PARAMS_CONFIGS.get("EMBEDDINGS", {}))

        try:
            client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            client.delete_collection(name=current_thread)
        except Exception as e:
            logging.warning(f"Bypassed collection deletion: {e}")

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH,
            collection_name=current_thread,
        )

        retriever = vector_store.as_retriever(**PARAMS_CONFIGS.get("RETRIEVER", {}))

        st.session_state["retrievers"][current_thread] = retriever
        st.session_state["metadatas"][current_thread] = {
            "filepath": str(filepath),
            "docs": len(docs),
            "chunks": len(chunks),
        }

        logging.info(f"Ingestion pipeline completed for {filepath}.")
        return {
            "filepath": str(filepath),
            "docs": len(docs),
            "chunks": len(chunks),
        }

    except Exception as e:
        logging.error(f"Failed to run ingestion pipeline for {filepath}: {e}")
        raise MyException(e, sys) from e
