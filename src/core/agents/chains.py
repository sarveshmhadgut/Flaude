import os
import sys

import yaml
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.core.capabilities.memory import DecisionSchema
from src.core.tools import available_tools
from src.exception import MyException
from src.infra.config import ROOT_DIR, get_llm

try:
    PARAMS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/params.yaml").read_text())
    PROMPTS_CONFIGS = yaml.safe_load((ROOT_DIR / "configs/prompts.yaml").read_text())

    load_dotenv()
    DB_URI = os.getenv(key="DB_URI")

    # model
    MODEL = get_llm(params=PARAMS_CONFIGS.get("LLM", {}))
    BOUND_MODEL = MODEL.bind_tools(tools=available_tools)
    PARSER = StrOutputParser()

    # memory prompt
    MEMORY_PROMPT = ChatPromptTemplate(
        [
            ("system", PROMPTS_CONFIGS["MEMORY"]["SYSTEM"]),
            ("user", PROMPTS_CONFIGS["MEMORY"]["USER"]),
        ]
    )
    MEMORY_MODEL = MODEL.with_structured_output(schema=DecisionSchema)
    MEMORY_CHAIN = MEMORY_PROMPT | MEMORY_MODEL

    # chat prompt
    CHAT_PROMPT = ChatPromptTemplate(
        [
            ("system", PROMPTS_CONFIGS.get("CHAT", {}).get("SYSTEM")),
            ("user", PROMPTS_CONFIGS.get("CHAT", {}).get("USER")),
            ("placeholder", "{messages}"),
        ]
    )
    CHAT_CHAIN = CHAT_PROMPT | BOUND_MODEL

    # summary prompt and chain
    SUMMARY_PROMPT = ChatPromptTemplate(
        [
            ("system", PROMPTS_CONFIGS.get("SUMMARIZE", {}).get("SYSTEM")),
            ("placeholder", "{messages}"),
            ("user", PROMPTS_CONFIGS.get("SUMMARIZE", {}).get("USER")),
        ]
    )
    SUMMARY_CHAIN = SUMMARY_PROMPT | MODEL | PARSER


except Exception as e:
    raise MyException(e, sys) from e
