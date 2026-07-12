import os
import sys

import streamlit as st
import yaml

from src.core.capabilities.rag import ingestion_pipeline
from src.core.workflow.graph import checkpointer
from src.exception import MyException
from src.infra.config import ROOT_DIR, get_conn
from src.logger import logging

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    PROMPTS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/prompts.yaml").read_text())

except Exception as e:
    logging.error(f"Failed to load configurations: {e}")
    raise MyException(e, sys) from e


def load_conversations():
    try:
        logging.info("Retrieving conversation history from database...")

        threads = list(
            {
                checkpoint.config["configurable"]["thread_id"]
                for checkpoint in checkpointer.list(None)
            }
        )

        logging.info("Conversation history retrieved.")
        return threads

    except Exception as e:
        logging.error(f"Failed to retrieve conversations from database: {e}")
        raise MyException(e, sys) from e


def load_thread_mapping():
    try:
        logging.info("Retrieving thread mappings from database...")
        conn = get_conn(
            db_path=PARAMS_CONFIGS.get("FILES", {}).get("MAPPING_DB_FILEPATH")
        )
        cursor = conn.cursor()

        cursor.execute(PROMPTS_CONFIGS.get("CREATE_TABLE"))
        cursor.execute(PROMPTS_CONFIGS.get("LOAD_ROWS"))
        thread_mappings = dict(cursor.fetchall())

        conn.commit()
        logging.info("Thread mappings retrieved.")
        return thread_mappings

    except Exception as e:
        logging.error(f"Failed to retrieve thread mappings from database: {e}")
        raise MyException(e, sys) from e


def save_row(thread_id, thread_name):
    try:
        logging.info(f"Inserting thread mapping into database for {thread_name}...")
        conn = get_conn(
            db_path=PARAMS_CONFIGS.get("FILES", {}).get("MAPPING_DB_FILEPATH")
        )
        cursor = conn.cursor()

        cursor.execute(PROMPTS_CONFIGS.get("CREATE_TABLE"))
        cursor.execute(
            PROMPTS_CONFIGS.get("INSERT_ROW"),
            (thread_id, thread_name),
        )
        conn.commit()
        logging.info(f"Thread mapping inserted for {thread_name}.")

    except Exception as e:
        logging.error(f"Failed to insert thread mapping: {e}")
        raise MyException(e, sys) from e


def save_file(file):
    try:
        if file:
            logging.info(f"Saving uploaded file locally: {file.name}...")
            FILES_DIRPATH = ROOT_DIR / PARAMS_CONFIGS.get("FILES", {}).get(
                "FILES_DIRNAME", ""
            )
            FILES_DIRPATH.mkdir(parents=True, exist_ok=True)

            filepath = FILES_DIRPATH / file.name

            with open(filepath, "wb") as f:
                f.write(file.getbuffer())

            with st.status(f"Processing `{file.name}` ...", expanded=True) as status:
                results = ingestion_pipeline(
                    filepath=str(filepath),
                    **PARAMS_CONFIGS.get("INGESTION_PIPELINE", {}),
                )

                if results:
                    status.update(
                        label=f"Successfully processed `{file.name}`",
                        state="complete",
                        expanded=False,
                    )
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        st.warning(f"Could not delete temporary file: {e}")
                else:
                    status.update(
                        label=f"Error processing `{file.name}`!", state="error"
                    )
            logging.info(f"File processed and saved: {file.name}.")

    except Exception as e:
        logging.error(f"Failed to save uploaded file: {e}")
        raise MyException(e, sys) from e
