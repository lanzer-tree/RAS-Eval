import os
from polygon import RESTClient
import json


def _load_client():
    key = os.environ.get('POLYGON_API_KEY')
    if not key:
        raise ValueError("API key not found. Set the POLYGON_API_KEY environment variable.")
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
        response = {"success": True, "data": []}
        for agg in aggs:
            response["data"].append({
                "open": agg.open,
                "close": agg.close,
                "high": agg.high,
                "low": agg.low,
                "volume": agg.volume,
                "timestamp": agg.timestamp
            })
        return response
    except Exception as e:
        return {"success": False, "message": str(e)}
    

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
        response = {"success": True, "data": []}
        for agg in aggs:
            response["data"].append({
                "open": agg.open,
                "close": agg.close,
                "high": agg.high,
                "low": agg.low,
                "volume": agg.volume,
                "timestamp": agg.timestamp  
            })
        return response
    except Exception as e:
        return {"success": False, "message": str(e)}
    

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
        response = {"success": True, "data": []}
        for agg in aggs:
            response["data"].append({
                "ticker": agg.ticker,
                "open": agg.open,
                "close": agg.close,
                "high": agg.high,
                "low": agg.low,
                "volume": agg.volume,
                "timestamp": agg.timestamp
            })
        return response 
    except Exception as e:
        return {"success": False, "message": str(e)}
    

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
        response = {
            "success": True,
            "open": agg.open,
            "close": agg.close,
            "high": agg.high,
            "low": agg.low,
            "volume": agg.volume,
        }
        return response
    except Exception as e:
        return {"success": False, "message": str(e)}
    

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
        response = {
            "success": True,
            "open": agg.open,
            "close": agg.close,
            "high": agg.high,
            "low": agg.low,
            "volume": agg.volume,
        }
        return response
    except Exception as e:
        return {"success": False, "message": str(e)}
    

# def list_trades(ticker: str, from_: str, to: str) -> dict:
#     """
#     List trades for a specific ticker over a given date range.

#     Args:
#         ticker (str): The ticker symbol of the stock.
#         from_ (str): The start date for the data. Format: YYYY-MM-DD
#         to (str): The end date for the data. Format: YYYY-MM-DD

#     Returns:
#         dict: A dictionary containing the trade data and success status.
#     """
#     try:
#         client = _load_client()
#         trades = client.list_trades(ticker, timestamp_gte=from_, timestamp_lte=to)
#         response = {"success": True, "data": []}
#         for trade in trades:
#             response["data"].append({
#                 "price": trade.price,
#                 "size": trade.size,
#                 "timestamp": trade.timestamp
#             })
#         return response
#     except Exception as e:
#         return {"success": False, "message": str(e)}
    

# def get_last_trade(ticker: str) -> dict:
#     """
#     Get the most recent trade for a ticker symbol.

#     Args:
#         ticker (str): The ticker symbol of the stock.

#     Returns:
#         dict: A dictionary containing the last trade data and success status.
#     """
#     try:
#         client = _load_client()
#         trade = client.get_last_trade(ticker)
#         response = {
#             "success": True,
#             "price": trade.price,
#             "size": trade.size,
#             "timestamp": trade.timestamp
#         }
#         return response
#     except Exception as e:
#         return {"success": False, "message": str(e)}
    

# def list_quotes(ticker: str, from_: str, to: str) -> dict:
#     """
#     List quotes for a specific ticker over a given date range.

#     Args:
#         ticker (str): The ticker symbol of the stock.
#         from_ (str): The start date for the data. Format: YYYY-MM-DD
#         to (str): The end date for the data. Format: YYYY-MM-DD

#     Returns:
#         dict: A dictionary containing the quote data and success status.
#     """
#     try:
#         client = _load_client()
#         quotes = client.list_quotes(ticker, timestamp_gte=from_, timestamp_lte=to)
#         response = {"success": True, "data": []}
#         for quote in quotes:
#             response["data"].append({
#                 "bid_price": quote.bid_price,
#                 "bid_size": quote.bid_size,
#                 "ask_price": quote.ask_price,
#                 "ask_size": quote.ask_size,
#                 "timestamp": quote.timestamp
#             })
#         return response
#     except Exception as e:
#         return {"success": False, "message": str(e)}


# def get_real_time_currency_conversation(from_currency: str, to_currency: str) -> dict:
#     """
#     Get the real-time currency conversion rate.

#     Args:
#         from_currency (str): The currency to convert from.
#         to_currency (str): The currency to convert to.

#     Returns:
#         dict: A dictionary containing the conversion rate and success status.
#     """
#     try:
#         client = _load_client()
#         conversion = client.get_real_time_currency_conversion(from_currency, to_currency)
#         response = {
#             "success": True,
#             "rate": conversion.rate,
#             "timestamp": conversion.timestamp
#         }
#         return response
#     except Exception as e:
#         return {"success": False, "message": str(e)}



