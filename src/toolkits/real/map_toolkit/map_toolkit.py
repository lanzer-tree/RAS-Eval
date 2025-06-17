from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import requests
import os


mcp = FastMCP('map_toolkit')
def location_encode(location: str) -> dict:
    """
    Get the latitude and longitude of a location.

    Args:
        location (str): The location to get the latitude and longitude of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://api.map.baidu.com/geocoding/v3'
    ak = os.getenv('BAIDU_MAP_AK')
    params = {'address': location, 'output': 'json', 'ak': ak}
    response = requests.get(url, params=params)
    if response:
        res = {'success': True, 'latitude': response.json()['result']['location']['lat'], 'longitude': response.json()['result']['location']['lng'], 'precise': response.json()['result']['precise'], 'confidence': response.json()['result']['confidence'], 'comprehension': response.json()['result']['comprehension'], 'level': response.json()['result']['level']}
        return res
    else:
        return {'success': False, 'description': f'Cannot get information of location: {location}'}


@tool(parse_docstring=True)
def langgraph_location_encode(location: str) -> dict:
    """
    Get the latitude and longitude of a location.

    Args:
        location (str): The location to get the latitude and longitude of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_encode(location=location)


@mcp.tool()
def mcp_location_encode(location: str) -> dict:
    """
    Get the latitude and longitude of a location.

    Args:
        location (str): The location to get the latitude and longitude of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_encode(location=location)


def location_decode(latitude: float, longitude: float) -> dict:
    """
    Get the address information including country, city and address based on a latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    url = 'https://api.map.baidu.com/reverse_geocoding/v3'
    ak = os.getenv('BAIDU_MAP_AK')
    params = {'output': 'json', 'ak': ak, 'coordtype': 'bd09ll', 'extensions_poi': '1', 'location': f'{latitude},{longitude}'}
    response = requests.get(url, params=params)
    if response:
        res = {'success': True, 'address': response.json()['result']['formatted_address'], 'country': response.json()['result']['addressComponent']['country'], 'city': response.json()['result']['addressComponent']['city']}
        return res
    else:
        return {'success': False, 'description': f'Cannot get information of location: {latitude}, {longitude}'}


@tool(parse_docstring=True)
def langgraph_location_decode(latitude: float, longitude: float) -> dict:
    """
    Get the address information including country, city and address based on a latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_decode(latitude=latitude, longitude=longitude)


@mcp.tool()
def mcp_location_decode(latitude: float, longitude: float) -> dict:
    """
    Get the address information including country, city and address based on a latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return location_decode(latitude=latitude, longitude=longitude)


