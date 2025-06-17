from langchain_core.tools import tool
from src.toolkits.real.stock_toolkit.function.stock_toolkit import get_stock_data
import tushare
import datetime
import os




@tool(parse_docstring=True)
def _get_stock_data(ts_code: str, trade_date: str) -> dict:
    """
    A tool that provides real-time access to market data, including opening price, closing price,
    maximum price, bottom price, volume, turnover, change.

    Args:
        ts_code (str): The stock code. e.g. "000001.SZ" for the Shanghai Stock Exchange.
        trade_date (str): The date of the market data, e.g. "2023-02-07".

    Returns:
        dict: success status and the detail information.
    """
    return get_stock_data(ts_code=ts_code, trade_date=trade_date)


