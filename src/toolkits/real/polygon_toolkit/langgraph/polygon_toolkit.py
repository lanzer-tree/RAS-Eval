from langchain_core.tools import tool
from src.toolkits.real.polygon_toolkit.function.polygon_toolkit import get_aggs
from src.toolkits.real.polygon_toolkit.function.polygon_toolkit import list_aggs
from src.toolkits.real.polygon_toolkit.function.polygon_toolkit import get_grouped_daily_aggs
from src.toolkits.real.polygon_toolkit.function.polygon_toolkit import get_daily_open_close_agg
from src.toolkits.real.polygon_toolkit.function.polygon_toolkit import get_previous_close_agg
import os
from polygon import RESTClient
import json




@tool(parse_docstring=True)
def _get_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
    """
    List aggregate bars for a ticker over a given date range in custom time window sizes.

    Args:
        ticker (str): The ticker symbol of the stock.
        multiplier (int): The size of the timespan multiplier.
        timespan (str): The size of the time window.
        from_ (str): The start date for the data. Format: YYYY-MM-DD
        to (str): The end date for the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the aggregate data and success status.
    """
    return get_aggs(ticker=ticker, multiplier=multiplier, timespan=timespan, from_=from_, to=to)


@tool(parse_docstring=True)
def _list_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
    """
    Iterate through aggregate bars for a ticker over a given date range.

    Args:
        ticker (str): The ticker symbol of the stock.
        multiplier (int): The size of the timespan multiplier.
        timespan (str): The size of the time window.
        from_ (str): The start date for the data. Format: YYYY-MM-DD
        to (str): The end date for the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the aggregate data and success status.
    """
    return list_aggs(ticker=ticker, multiplier=multiplier, timespan=timespan, from_=from_, to=to)


@tool(parse_docstring=True)
def _get_grouped_daily_aggs(date: str) -> dict:
    """
    Get grouped daily bars for entire market for a specific date.

    Args:
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the grouped daily data and success status.
    """
    return get_grouped_daily_aggs(date=date)


@tool(parse_docstring=True)
def _get_daily_open_close_agg(ticker: str, date: str) -> dict:
    """
    Get the daily open and close aggregate for a specific ticker and date.

    Args:
        ticker (str): The ticker symbol of the stock.
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:    
        dict: A dictionary containing the open and close prices and success status.
    """
    return get_daily_open_close_agg(ticker=ticker, date=date)


@tool(parse_docstring=True)
def _get_previous_close_agg(ticker: str) -> dict:
    """
    Get the previous close aggregate for a specific ticker.

    Args:
        ticker (str): The ticker symbol of the stock.

    Returns:
        dict: A dictionary containing the previous close data and success status.
    """
    return get_previous_close_agg(ticker=ticker)


