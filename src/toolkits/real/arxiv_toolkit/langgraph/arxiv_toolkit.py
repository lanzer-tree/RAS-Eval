from langchain_core.tools import tool
from src.toolkits.real.arxiv_toolkit.function.arxiv_toolkit import is_arxiv_identifier
from src.toolkits.real.arxiv_toolkit.function.arxiv_toolkit import search_identifier
import arxiv
from typing import Optional
import re


ARXIV_MAX_QUERY_LENGTH: int = 300
TOP_K_RESULTS: int = 3
LOAD_MAX_DOCS: int = 100
DOC_CONTENT_CHARS_MAX: Optional[int] = 4000


@tool(parse_docstring=True)
def _is_arxiv_identifier(identifier: str) -> bool:
    """
    Check if the given identifier is a valid arXiv identifier.

    Args:
        identifier (str): The identifier to check.

    Returns:
        bool: True if the identifier is a valid arXiv identifier, False otherwise.
    """
    return is_arxiv_identifier(identifier=identifier)


@tool(parse_docstring=True)
def _search_identifier(identifier: str) -> list[dict[str, str]]:
    """
    Search for arXiv papers based on the given identifier.

    Args:
        identifier (str): The identifier to search for.
    """
    return search_identifier(identifier=identifier)


