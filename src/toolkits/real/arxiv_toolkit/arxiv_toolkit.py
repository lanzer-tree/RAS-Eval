from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import arxiv
from typing import Optional
import re


mcp = FastMCP('arxiv_toolkit')
ARXIV_MAX_QUERY_LENGTH: int = 300


TOP_K_RESULTS: int = 3


LOAD_MAX_DOCS: int = 100


DOC_CONTENT_CHARS_MAX: Optional[int] = 4000


def is_arxiv_identifier(identifier: str) -> bool:
    """
    Check if the given identifier is a valid arXiv identifier.

    Args:
        identifier (str): The identifier to check.

    Returns:
        bool: True if the identifier is a valid arXiv identifier, False otherwise.
    """
    res = True
    arxiv_identifier_pattern = '\\d{2}(0[1-9]|1[0-2])\\.\\d{4,5}(v\\d+|)|\\d{7}.*'
    for item in identifier[:ARXIV_MAX_QUERY_LENGTH].split():
        match_result = re.match(arxiv_identifier_pattern, item)
        if not match_result:
            res = False
        if match_result is None:
            res = False
        elif not match_result.group(0) == item:
            res = False
    return res


@tool(parse_docstring=True)
def langgraph_is_arxiv_identifier(identifier: str) -> bool:
    """
    Check if the given identifier is a valid arXiv identifier.

    Args:
        identifier (str): The identifier to check.

    Returns:
        bool: True if the identifier is a valid arXiv identifier, False otherwise.
    """
    return is_arxiv_identifier(identifier=identifier)


@mcp.tool()
def mcp_is_arxiv_identifier(identifier: str) -> bool:
    """
    Check if the given identifier is a valid arXiv identifier.

    Args:
        identifier (str): The identifier to check.

    Returns:
        bool: True if the identifier is a valid arXiv identifier, False otherwise.
    """
    return is_arxiv_identifier(identifier=identifier)


def search_identifier(identifier: str) -> list[dict[str, str]]:
    """
    Search for arXiv papers based on the given identifier.

    Args:
        identifier (str): The identifier to search for.
    """
    try:
        results = arxiv.Search(id_list=[identifier], max_results=TOP_K_RESULTS).results()
    except arxiv.ArxivError as error:
        exit()
    articles = []
    for result in results:
        article = {'identifier': identifier, 'published': str(result.updated.date()), 'title': str(result.title), 'authors': ', '.join((a.name for a in result.authors)), 'summary': str(result.summary), 'pdf_url': str(result.pdf_url)}
        articles.append(article)
    return articles


@tool(parse_docstring=True)
def langgraph_search_identifier(identifier: str) -> list[dict[str, str]]:
    """
    Search for arXiv papers based on the given identifier.

    Args:
        identifier (str): The identifier to search for.
    """
    return search_identifier(identifier=identifier)


@mcp.tool()
def mcp_search_identifier(identifier: str) -> list[dict[str, str]]:
    """
    Search for arXiv papers based on the given identifier.

    Args:
        identifier (str): The identifier to search for.
    """
    return search_identifier(identifier=identifier)


