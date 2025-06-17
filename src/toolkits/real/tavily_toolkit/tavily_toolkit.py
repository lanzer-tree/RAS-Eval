from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import os


mcp = FastMCP('tavily_toolkit')
def tavily_search(query: str) -> list:
    """
    Search Tavily for the given query and return the results.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list containing the results.
    """
    client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    try:
        response = client.search(query)['results']
        return response
    except Exception as e:
        return {'error': str(e)}


@tool(parse_docstring=True)
def langgraph_tavily_search(query: str) -> list:
    """
    Search Tavily for the given query and return the results.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list containing the results.
    """
    return tavily_search(query=query)


@mcp.tool()
def mcp_tavily_search(query: str) -> list:
    """
    Search Tavily for the given query and return the results.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list containing the results.
    """
    return tavily_search(query=query)


