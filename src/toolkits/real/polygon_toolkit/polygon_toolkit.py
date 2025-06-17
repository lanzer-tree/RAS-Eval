from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import os
from polygon import RESTClient
import json


mcp = FastMCP('polygon_toolkit')
def _load_client():
    key = os.environ.get('POLYGON_API_KEY')
    if not key:
        raise ValueError('API key not found. Set the POLYGON_API_KEY environment variable.')
    client = RESTClient(key)
    return client


def get_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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
    try:
        client = _load_client()
        aggs = client.get_aggs(ticker, multiplier, timespan, from_, to)
        response = {'success': True, 'data': []}
        for agg in aggs:
            response['data'].append({'open': agg.open, 'close': agg.close, 'high': agg.high, 'low': agg.low, 'volume': agg.volume, 'timestamp': agg.timestamp})
        return response
    except Exception as e:
        return {'success': False, 'message': str(e)}


@tool(parse_docstring=True)
def langgraph_get_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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


@mcp.tool()
def mcp_get_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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


def list_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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
    try:
        client = _load_client()
        aggs = client.list_aggs(ticker, multiplier, timespan, from_, to)
        response = {'success': True, 'data': []}
        for agg in aggs:
            response['data'].append({'open': agg.open, 'close': agg.close, 'high': agg.high, 'low': agg.low, 'volume': agg.volume, 'timestamp': agg.timestamp})
        return response
    except Exception as e:
        return {'success': False, 'message': str(e)}


@tool(parse_docstring=True)
def langgraph_list_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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


@mcp.tool()
def mcp_list_aggs(ticker: str, multiplier: int, timespan: str, from_: str, to: str) -> dict:
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


def get_grouped_daily_aggs(date: str) -> dict:
    """
    Get grouped daily bars for entire market for a specific date.

    Args:
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the grouped daily data and success status.
    """
    try:
        client = _load_client()
        aggs = client.get_grouped_daily_aggs(date)
        response = {'success': True, 'data': []}
        for agg in aggs:
            response['data'].append({'ticker': agg.ticker, 'open': agg.open, 'close': agg.close, 'high': agg.high, 'low': agg.low, 'volume': agg.volume, 'timestamp': agg.timestamp})
        return response
    except Exception as e:
        return {'success': False, 'message': str(e)}


@tool(parse_docstring=True)
def langgraph_get_grouped_daily_aggs(date: str) -> dict:
    """
    Get grouped daily bars for entire market for a specific date.

    Args:
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the grouped daily data and success status.
    """
    return get_grouped_daily_aggs(date=date)


@mcp.tool()
def mcp_get_grouped_daily_aggs(date: str) -> dict:
    """
    Get grouped daily bars for entire market for a specific date.

    Args:
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:
        dict: A dictionary containing the grouped daily data and success status.
    """
    return get_grouped_daily_aggs(date=date)


def get_daily_open_close_agg(ticker: str, date: str) -> dict:
    """
    Get the daily open and close aggregate for a specific ticker and date.

    Args:
        ticker (str): The ticker symbol of the stock.
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:    
        dict: A dictionary containing the open and close prices and success status.
    """
    try:
        client = _load_client()
        agg = client.get_daily_open_close_agg(ticker, date)
        response = {'success': True, 'open': agg.open, 'close': agg.close, 'high': agg.high, 'low': agg.low, 'volume': agg.volume}
        return response
    except Exception as e:
        return {'success': False, 'message': str(e)}


@tool(parse_docstring=True)
def langgraph_get_daily_open_close_agg(ticker: str, date: str) -> dict:
    """
    Get the daily open and close aggregate for a specific ticker and date.

    Args:
        ticker (str): The ticker symbol of the stock.
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:    
        dict: A dictionary containing the open and close prices and success status.
    """
    return get_daily_open_close_agg(ticker=ticker, date=date)


@mcp.tool()
def mcp_get_daily_open_close_agg(ticker: str, date: str) -> dict:
    """
    Get the daily open and close aggregate for a specific ticker and date.

    Args:
        ticker (str): The ticker symbol of the stock.
        date (str): The date for which to retrieve the data. Format: YYYY-MM-DD

    Returns:    
        dict: A dictionary containing the open and close prices and success status.
    """
    return get_daily_open_close_agg(ticker=ticker, date=date)


def get_previous_close_agg(ticker: str) -> dict:
    """
    Get the previous close aggregate for a specific ticker.

    Args:
        ticker (str): The ticker symbol of the stock.

    Returns:
        dict: A dictionary containing the previous close data and success status.
    """
    try:
        client = _load_client()
        agg = client.get_previous_close_agg(ticker)[0]
        response = {'success': True, 'open': agg.open, 'close': agg.close, 'high': agg.high, 'low': agg.low, 'volume': agg.volume}
        return response
    except Exception as e:
        return {'success': False, 'message': str(e)}


@tool(parse_docstring=True)
def langgraph_get_previous_close_agg(ticker: str) -> dict:
    """
    Get the previous close aggregate for a specific ticker.

    Args:
        ticker (str): The ticker symbol of the stock.

    Returns:
        dict: A dictionary containing the previous close data and success status.
    """
    return get_previous_close_agg(ticker=ticker)


@mcp.tool()
def mcp_get_previous_close_agg(ticker: str) -> dict:
    """
    Get the previous close aggregate for a specific ticker.

    Args:
        ticker (str): The ticker symbol of the stock.

    Returns:
        dict: A dictionary containing the previous close data and success status.
    """
    return get_previous_close_agg(ticker=ticker)


