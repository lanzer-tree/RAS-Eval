from mcp.server.fastmcp import FastMCP
from src.toolkits.real.tavily_toolkit.function.tavily_toolkit import tavily_search
from tavily import TavilyClient
import os


mcp = FastMCP('tavily_toolkit')


@mcp.tool()
def _tavily_search(query: str) -> list:
    """
    Search Tavily for the given query and return the results.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list containing the results.
    """
    return tavily_search(query=query)


if __name__ == '__main__':
    mcp.run('stdio')
