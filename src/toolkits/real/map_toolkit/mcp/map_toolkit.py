from mcp.server.fastmcp import FastMCP
from src.toolkits.real.map_toolkit.function.map_toolkit import location_encode
from src.toolkits.real.map_toolkit.function.map_toolkit import location_decode
import requests
import os


mcp = FastMCP('map_toolkit')


@mcp.tool()
def _location_encode(location: str) -> dict:
    """
    Get the latitude and longitude of a location.

    Args:
        location (str): The location to get the latitude and longitude of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_encode(location=location)


@mcp.tool()
def _location_decode(latitude: float, longitude: float) -> dict:
    """
    Get the address information including country, city and address based on a latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_decode(latitude=latitude, longitude=longitude)


if __name__ == '__main__':
    mcp.run('stdio')
