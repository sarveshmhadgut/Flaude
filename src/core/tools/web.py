import os
import sys
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from src.exception import MyException
from src.logger import logging

try:
    load_dotenv()
    EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")
except Exception as e:
    raise MyException(e, sys) from e


@tool(name_or_callable="web_search")
def web_search(search_query: str) -> Dict[str, Any]:
    """
    Search the web for information related to a query.
    Args:
        search_query: Search query.
    Returns:
        A dictionary containing the search results.
    """
    try:
        logging.info(f"Executing web_search tool for {search_query}...")

        engine = DuckDuckGoSearchRun()
        res = engine.invoke(search_query)

        logging.info(f"Finished executing web_search tool for {search_query}.")
        return {
            "status": "success",
            "query": search_query,
            "response": res,
        }

    except Exception as e:
        logging.error(f"Failed to execute web_search tool : {e}")
        raise MyException(e, sys) from e


@tool(name_or_callable="get_conversion_rate")
def get_conversion_rate(base_currency: str, target_currency: str) -> Dict[str, Any]:
    """
    MUST be used to get real-time, up-to-date currency exchange rates.
    Do NOT guess or approximate rates.
    Always call this tool when asked for current conversion rates.
    """
    try:
        logging.info(
            f"Executing get_conversion_rate tool for {base_currency} -> {target_currency}..."
        )
        if not EXCHANGE_RATE_KEY:
            raise ValueError("EXCHANGE_RATE_KEY not found")

        URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/pair/{base_currency}/{target_currency}"

        res = requests.get(url=URL, timeout=10)
        res.raise_for_status()

        data = res.json()
        if data["result"] != "success":
            raise ValueError(data.get("error-type", "Unknown API error"))

        logging.info(
            f"Finished executing get_conversion_rate tool for {base_currency} -> {target_currency}."
        )
        return {
            "status": "success",
            "base_currency": base_currency,
            "target_currency": target_currency,
            "conversion_rate": data["conversion_rate"],
        }

    except Exception as e:
        logging.error(f"Failed to execute get_conversion_rate tool : {e}")
        raise MyException(e, sys) from e
