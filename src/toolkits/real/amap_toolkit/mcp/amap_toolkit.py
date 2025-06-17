from mcp.server.fastmcp import FastMCP
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_geocode
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_regeocode
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_direction_walking
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_direction_transit
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_direction_driving
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_direction_bicycling
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_get_distance
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_ip_location
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_transform_location
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_search_detail
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_around_search
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_get_weather
from src.toolkits.real.amap_toolkit.function.amap_toolkit import amap_get_weather_forecast
import os
import requests
from typing import Optional


mcp = FastMCP('amap_toolkit')


@mcp.tool()
def _amap_geocode(address: str, city: Optional[str]=None) -> dict:
    """
    Get the latitude and longitude and administrative division of a address.

    Args:
        address (str): The address to get the latitude and longitude of.
        city (str): The city of the address.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_geocode(address=address, city=city)


@mcp.tool()
def _amap_regeocode(location: str) -> dict:
    """
    Get the address and administrative division of a latitude and longitude.

    Args:
        location (str): The langitude and latitude of the address, separated by a comma. e.g. "120.123612,30.266521".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_regeocode(location=location)


@mcp.tool()
def _amap_direction_walking(origin: str, destination: str) -> dict:
    """
    Get the walking route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_walking(origin=origin, destination=destination)


@mcp.tool()
def _amap_direction_transit(origin: str, destination: str, city: str, cityd: Optional[str]=None) -> dict:
    """
    Get the transit route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".
        city (str): The city of the origin.
        cityd (str): The city of the destination.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_transit(origin=origin, destination=destination, city=city, cityd=cityd)


@mcp.tool()
def _amap_direction_driving(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_driving(origin=origin, destination=destination)


@mcp.tool()
def _amap_direction_bicycling(origin: str, destination: str) -> dict:
    """
    Get the driving route from origin to destination.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_direction_bicycling(origin=origin, destination=destination)


@mcp.tool()
def _amap_get_distance(origin: str, destination: str) -> dict:
    """
    Get the distance between two points.

    Args:
        origin (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521
        destination (str): The langitude and latitude of the destination, separated by a comma. e.g. "120.123700,30.266501".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_distance(origin=origin, destination=destination)


@mcp.tool()
def _amap_ip_location(ip: str) -> dict:
    """
    Get the location of an IP address.

    Args:
        ip (str): The IP address to get the location of.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_ip_location(ip=ip)


@mcp.tool()
def _amap_transform_location(location: str, coordtype: str) -> dict:
    """
    Transform the location from one coordinate system to another.

    Args:
        location (str): The langitude and latitude of the origin, separated by a comma. e.g. "120.123612,30.266521".
        coordtype (str): The coordinate system of the location. e.g. "gps", "baidu".

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_transform_location(location=location, coordtype=coordtype)


@mcp.tool()
def _amap_search_detail(keywords: str) -> dict:
    """
    Get the detail information of a place.

    Args:
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_search_detail(keywords=keywords)


@mcp.tool()
def _amap_around_search(location: str, keywords: str) -> dict:
    """
    Get the surrounding places of a location.

    Args:
        location (str): The langitude and latitude of the location, separated by a comma. e.g. "120.123612,30.266521".
        keywords (str): The keywords to search for.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_around_search(location=location, keywords=keywords)


@mcp.tool()
def _amap_get_weather(address_code: str) -> dict:
    """
    Get the weather of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather(address_code=address_code)


@mcp.tool()
def _amap_get_weather_forecast(address_code: str) -> dict:
    """
    Get the weather forecast of a location.

    Args:
        address_code (str): The address code of the location.

    Returns:
        dict: A dictionary containing success status the detail information.
    """
    return amap_get_weather_forecast(address_code=address_code)


if __name__ == '__main__':
    mcp.run('stdio')
