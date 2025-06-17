import tushare
import datetime
import os


def get_stock_data(ts_code: str, trade_date: str) -> dict:
    """
    A tool that provides real-time access to market data, including opening price, closing price,
    maximum price, bottom price, volume, turnover, change.

    Args:
        ts_code (str): The stock code. e.g. "000001.SZ" for the Shanghai Stock Exchange.
        trade_date (str): The date of the market data, e.g. "2023-02-07".

    Returns:
        dict: success status and the detail information.
    """
    try:
        api = tushare.pro_api(os.getenv("TUSHARE_TOKEN"))
        trade_date = datetime.datetime.strptime(trade_date, "%Y-%m-%d")
        trade_date = datetime.datetime.strftime(trade_date, "%Y%m%d")
        data = api.query("daily", ts_code=ts_code, trade_date=str(trade_date)).to_dict(orient="records")
        result = {
            "success": True,
            "ts_code": data[0]['ts_code'],  
            "trade_date": data[0]['trade_date'],
            "opening_price": data[0]['open'],
            "closing_price": data[0]['close'],
            "maximum_price": data[0]['high'],
            "bottom_price": data[0]['low'],
            "stock_volume": data[0]['vol'],
            "stock_turnover": data[0]['amount'],
            "change": data[0]['change'],
        }
        return result
    except Exception as error:
        return {"success": False, "error": str(error)}

