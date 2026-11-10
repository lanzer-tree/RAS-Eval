from tavily import TavilyClient
import os


def tavily_search(query: str) -> dict:
    """
    Search Tavily for the given query and return the results.

    Args:
        query (str): The query to search for.

    Returns:
        dict: A dictionay containing the results.
    """
    client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    try:
        response = client.search(query)['results']
        return {"success": True, "results": response}
    except Exception as e:
        return {'error': str(e)}
    
    