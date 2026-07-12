import sys
from typing import Any, Dict

from langchain_core.tools import tool
from sympy import sympify

from src.exception import MyException
from src.logger import logging


@tool(name_or_callable="math_eval")
def math_eval(expression: str) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression and return the result.
    Args:
        expression: Mathematical expression to evaluate.
    Returns:
        A dictionary containing the evaluation result or an error message.
    """
    try:
        logging.info(f"Executing math_eval tool for {expression}...")

        res = sympify(expression)

        logging.info(f"Finished executing math_eval tool for {expression}.")
        return {
            "status": "success",
            "expression": expression,
            "result": res,
        }

    except Exception as e:
        logging.error(f"Failed to execute math_eval tool : {e}")
        raise MyException(e, sys) from e
