import sys

from langchain_core.tools.base import BaseTool

from src.core.tools.files import file_search
from src.core.tools.math import math_eval
from src.core.tools.rag import rag_tool
from src.core.tools.web import get_conversion_rate, web_search
from src.exception import MyException
from src.logger import logging

try:
    logging.info("Loading tools module...")

    available_tools: list[BaseTool] = [
        math_eval,
        web_search,
        file_search,
        get_conversion_rate,
        rag_tool,
    ]
    logging.info("Tools module loading complete.")

except Exception as e:
    logging.error(f"Error loading tools module: {e}")
    raise MyException(e, sys) from e

__all__ = [
    "available_tools",
    "file_search",
    "get_conversion_rate",
    "math_eval",
    "rag_tool",
    "web_search",
]
