import sys
from typing import Any, Dict

from langchain_core.tools import tool
from sympy import Basic, sympify

from src.exception import MyException
from src.logger import logging


@tool(name_or_callable="math_eval")
def math_eval(expression: str) -> Dict[str, Any]:
    """
    Evaluates a mathematical expression using sympy.

    Args:
        expression (str): The mathematical expression to evaluate (e.g., '2 + 2').

    Returns:
        Dict[str, Any]:
            - A dictionary containing the result of the evaluation.

    Raises:
        MyException: If the mathematical evaluation fails.
    """
    try:
        logging.info(f"Executing math_eval tool for {expression}...")

        res: Basic = sympify(expression)

        logging.info(f"Finished executing math_eval tool for {expression}.")
        return {
            "status": "success",
            "expression": expression,
            "result": res,
        }

    except Exception as e:
        logging.error(f"Failed to execute math_eval tool : {e}")
        raise MyException(e, sys) from e
