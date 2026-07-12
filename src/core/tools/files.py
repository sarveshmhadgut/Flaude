import sys
from pathlib import Path
from typing import Any, Dict

from langchain_core.tools import tool

from src.exception import MyException
from src.logger import logging


@tool(name_or_callable="file_search")
def file_search(filename: str) -> Dict[str, Any]:
    """
    Search for a file in the current directory tree and return its contents.
    Args:
        filename: Name of the file to locate.
    Returns:
        A dictionary containing the file contents if found, otherwise None.
    """
    try:
        logging.info(f"Executing file_search tool for {filename}...")

        current = Path.cwd()
        contents = []

        for filepath in current.rglob(filename):
            if filepath.is_file():
                contents.append(f"{filepath.name}\n{filepath.read_text()}\n")

        logging.info(f"Finished executing file_search tool for {filename}.")
        return {
            "status": "success",
            "filename": filename,
            "contents": "\n\n".join(contents)
            if contents
            else "No matching files found.",
        }

    except Exception as e:
        logging.error(f"Failed to execute file_search tool: {e}")
        raise MyException(e, sys) from e
