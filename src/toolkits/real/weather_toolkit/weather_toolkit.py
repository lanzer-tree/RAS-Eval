from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import requests
import datetime
import os


mcp = FastMCP('weather_toolkit')
url = 'https://api.openweathermap.org/data/2.5/weather'


appid = os.getenv('OPENWEATHERMAP_API_KEY')


def get_weather(city: str) -> dict[str, str]:
    """
    Get the weather, temperature of a city at the current time.

    Args:
        city (str): The city to get the weather of. e.g. "beijing"

    Returns:
        dict[str, str]: The weather, temperature, date, country information of the city.
    """
    params = {'q': city, 'appid': appid, 'units': 'metric'}
    response = requests.get(url, params=params)
    weather_data = response.json()
    time_str = datetime.datetime.fromtimestamp(weather_data['dt']).strftime('%Y-%m-%d %H:%M:%S')
    return {'date': time_str, 'country': weather_data['sys']['country'], 'temperature': weather_data['main']['temp'], 'weather': weather_data['weather'][0]['main']}


@tool(parse_docstring=True)
def langgraph_get_weather(city: str) -> dict[str, str]:
    """
    Get the weather, temperature of a city at the current time.

    Args:
        city (str): The city to get the weather of. e.g. "beijing"

    Returns:
        dict[str, str]: The weather, temperature, date, country information of the city.
    """
    return get_weather(city=city)


@mcp.tool()
def mcp_get_weather(city: str) -> dict[str, str]:
    """
    Get the weather, temperature of a city at the current time.

    Args:
        city (str): The city to get the weather of. e.g. "beijing"

    Returns:
        dict[str, str]: The weather, temperature, date, country information of the city.
    """
    return get_weather(city=city)


