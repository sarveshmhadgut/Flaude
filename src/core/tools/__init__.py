import sys

from src.exception import MyException
from src.logger import logging

try:
    logging.info("Loading tools module...")
    from .files import file_search
    from .math import math_eval
    from .rag import rag_tool
    from .web import get_conversion_rate, web_search

    available_tools = [
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
