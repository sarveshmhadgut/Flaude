import sys

import yaml
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from src.exception import MyException
from src.infra.config import ROOT_DIR, get_llm
from src.infra.database import save_row
from src.logger import logging

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    PROMPTS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/prompts.yaml").read_text())
    load_dotenv()

    MODEL = get_llm(params=PARAMS_CONFIGS.get("LLM", {}))
    PARSER = StrOutputParser()

    PROMPT = ChatPromptTemplate(
        [
            ("system", PROMPTS_CONFIGS.get("GENERATE_TITLE", {}).get("SYSTEM")),
            ("user", PROMPTS_CONFIGS.get("GENERATE_TITLE", {}).get("USER")),
        ]
    )
    CHAIN = PROMPT | MODEL | PARSER

except Exception as e:
    raise MyException(e, sys) from e


@traceable(name="title_generator")
def generate_title(thread_id: str, conversation_history: str) -> str:
    try:
        logging.info(f"Generating title for thread {thread_id}...")

        if not conversation_history:
            logging.info(
                f"Empty conversation history; skipping title generation for thread {thread_id}."
            )
            return "New Conversation"

        res = CHAIN.invoke(input={"conversation_history": conversation_history})
        save_row(thread_id=thread_id, thread_name=res)

        logging.info(f"Generated title for thread {thread_id}: '{res}'.")
        return res

    except Exception as e:
        logging.error(f"Failed to generate title for thread {thread_id}: {e}")
        raise MyException(e, sys) from e
