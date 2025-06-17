from langchain_core.tools import tool
from src.toolkits.real.weather_toolkit.function.weather_toolkit import get_weather
import requests
import datetime
import os


url = 'https://api.openweathermap.org/data/2.5/weather'
appid = os.getenv('OPENWEATHERMAP_API_KEY')


@tool(parse_docstring=True)
def _get_weather(city: str) -> dict[str, str]:
    """
    Get the weather, temperature of a city at the current time.

    Args:
        city (str): The city to get the weather of. e.g. "beijing"

    Returns:
        dict[str, str]: The weather, temperature, date, country information of the city.
    """
    return get_weather(city=city)


