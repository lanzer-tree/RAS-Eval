import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List

DATA_PATH = "environment/reports/Ameritrade.json"
INIT_PATH = "environment/initial/Ameritrade_init.json"

INIT = False


class InvalidRequestException(Exception):
    """Raise when request parameters are missing or malformed."""


class NotFoundException(Exception):
    """Raise when requested data cannot be located."""


def _ensure_work_env() -> None:
    """Ensure the working environment exists by copying the init file if necessary."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f"Init file not found: {INIT_PATH}")
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    """Load the current working environment."""
    _ensure_work_env()
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    """Persist the current working environment."""
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _match_account(data: Dict[str, Any], account: str) -> Dict[str, Any]:
    """Find the account dictionary that matches the provided account type."""
    target_type = account.strip().lower()
    for entry in data.get("accounts", []):
        if entry.get("account_type", "").strip().lower() == target_type:
            return entry
    return {}


def _normalize_ticker(ticker: str) -> str:
    """Normalize a ticker to uppercase."""
    return ticker.strip().upper()


def _find_market_entry(data: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    """Retrieve market metadata for a ticker."""
    normalized = _normalize_ticker(ticker)
    return data.get("market_data", {}).get(normalized, {})


def _record_trade(data: Dict[str, Any], account_type: str, action: str, ticker: str, quantity: float, price: float, order_type: str) -> None:
    """Append a trade record for auditing."""
    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_type": account_type,
        "action": action,
        "ticker": ticker,
        "quantity": quantity,
        "price": price,
        "order_type": order_type,
    }
    data.setdefault("trade_history", []).append(entry)


def GetHoldingsInformation(account: str) -> Dict[str, Any]:
    """Retrieve the USD value of every holding in the specified account.

    Args:
        account (str): The account type to query holdings for.
    """
    if not account:
        raise InvalidRequestException("The 'account' parameter is required.")
    data = _load_data()
    account_entry = _match_account(data, account)
    if not account_entry:
        raise InvalidRequestException("The 'account' parameter is not in the correct format.")
    holdings_summary: List[Dict[str, Any]] = []
    total_value = 0.0
    market = data.get("market_data", {})
    for position in account_entry.get("holdings", []):
        ticker = _normalize_ticker(position.get("ticker", ""))
        shares = float(position.get("shares", 0))
        if shares <= 0:
            continue
        quote = market.get(ticker)
        if not quote:
            continue
        average_price = (quote.get("bid", 0.0) + quote.get("ask", 0.0)) / 2
        usd_value = round(shares * average_price, 2)
        total_value += usd_value
        holdings_summary.append({"ticker": ticker, "usd_value": usd_value})
    return {"holdings": holdings_summary, "total_value": round(total_value, 2)}


def GetBalance(account: str) -> Dict[str, Any]:
    """Return the available cash balance for the specified account.

    Args:
        account (str): The account type to query balance for.
    """
    if not account:
        raise InvalidRequestException("The 'account' parameter is required.")
    data = _load_data()
    account_entry = _match_account(data, account)
    if not account_entry:
        raise InvalidRequestException("The 'account' parameter is not in the correct format.")
    balance = round(float(account_entry.get("cash_balance", 0.0)), 2)
    return {"balance": balance}

def GetStockInformation(ticker: str) -> Dict[str, Any]:
    """Retrieve up-to-date quote data for the requested ticker.

    Args:
        ticker (str): The stock ticker symbol to query.
    """
    if not ticker:
        raise InvalidRequestException("The 'ticker' parameter is required.")
    data = _load_data()
    quote = _find_market_entry(data, ticker)
    if not quote:
        raise InvalidRequestException("The ticker is invalid.")
    bid = quote.get("bid", 0.0)
    ask = quote.get("ask", 0.0)
    spread = round(abs(ask - bid), 2)
    stock_info = {
        "bid": bid,
        "bid_lot_size": quote.get("bid_lot_size", 0),
        "ask": ask,
        "ask_lot_size": quote.get("ask_lot_size", 0),
        "daily_volume": quote.get("daily_volume", 0),
        "spread": spread,
    }
    return {"stock_info": stock_info}


def TradeStock(account: str, action: str, order_type: str, ticker: str, quantity: float, price_limit: float | None = None) -> Dict[str, Any]:
    """Submit a buy or sell order and update the account holdings and cash.

    Args:
        account (str): The account type to execute the trade in.
        action (str): The trade action, must be 'buy' or 'sell'.
        order_type (str): The order type, must be 'limit_order' or 'market_order'.
        ticker (str): The stock ticker symbol to trade.
        quantity (float): The number of shares to trade.
        price_limit (float | None): The limit price for limit orders, optional for market orders.
    """
    if not all([account, action, order_type, ticker]):
        raise InvalidRequestException("All required parameters must be provided.")
    normalized_action = action.lower()
    if normalized_action not in ["buy", "sell"]:
        raise InvalidRequestException("The 'action' parameter must be 'buy' or 'sell'.")
    normalized_order = order_type.lower()
    if normalized_order not in ["limit_order", "market_order"]:
        raise InvalidRequestException("The 'order_type' parameter must be 'limit_order' or 'market_order'.")
    try:
        quantity_value = float(quantity)
    except (TypeError, ValueError):
        raise InvalidRequestException("The 'quantity' must be a valid number.")
    if quantity_value <= 0:
        raise InvalidRequestException("The 'quantity' must be greater than zero.")
    data = _load_data()
    account_entry = _match_account(data, account)
    if not account_entry:
        raise InvalidRequestException("The 'account' parameter is not in the correct format.")
    quote = _find_market_entry(data, ticker)
    if not quote:
        raise InvalidRequestException("The ticker is invalid.")
    ticker_key = _normalize_ticker(ticker)
    execution_price = 0.0
    if normalized_order == "market_order":
        execution_price = quote.get("ask", 0.0) if normalized_action == "buy" else quote.get("bid", 0.0)
    else:
        if price_limit is None:
            raise InvalidRequestException("price_limit is required for limit orders.")
        try:
            price_limit_value = float(price_limit)
        except (TypeError, ValueError):
            raise InvalidRequestException("The 'price_limit' must be a valid number.")
        if normalized_action == "buy":
            if price_limit_value < quote.get("ask", 0.0):
                raise InvalidRequestException("The limit price is below the current ask.")
        else:
            if price_limit_value > quote.get("bid", 0.0):
                raise InvalidRequestException("The limit price is above the current bid.")
        execution_price = quote.get("ask", 0.0) if normalized_action == "buy" else quote.get("bid", 0.0)
    if execution_price <= 0:
        raise InvalidRequestException("Unable to determine execution price.")
    cash_balance = float(account_entry.get("cash_balance", 0.0))
    holdings = account_entry.setdefault("holdings", [])
    if normalized_action == "buy":
        cost = round(execution_price * quantity_value, 2)
        if cost > cash_balance:
            raise InvalidRequestException("Insufficient funds: the cost exceeds the available balance.")
        account_entry["cash_balance"] = round(cash_balance - cost, 2)
        for position in holdings:
            if _normalize_ticker(position.get("ticker", "")) == ticker_key:
                position["shares"] = round(position.get("shares", 0.0) + quantity_value, 6)
                break
        else:
            holdings.append({"ticker": ticker_key, "shares": round(quantity_value, 6)})
        _record_trade(data, account_entry.get("account_type", ""), "buy", ticker_key, quantity_value, execution_price, normalized_order)
    else:
        position = next((p for p in holdings if _normalize_ticker(p.get("ticker", "")) == ticker_key), None)
        if not position or position.get("shares", 0.0) < quantity_value:
            raise InvalidRequestException("Not enough shares are available to sell.")
        proceeds = round(execution_price * quantity_value, 2)
        account_entry["cash_balance"] = round(cash_balance + proceeds, 2)
        position["shares"] = round(position.get("shares", 0.0) - quantity_value, 6)
        if position["shares"] <= 0:
            holdings.remove(position)
        _record_trade(data, account_entry.get("account_type", ""), "sell", ticker_key, quantity_value, execution_price, normalized_order)
    _save_data(data)
    return {
        "success": True,
        "ticker": ticker_key,
        "quantity": quantity_value,
        "executed_price": execution_price,
        "order_type": normalized_order,
        "account_balance": round(float(account_entry.get("cash_balance", 0.0)), 2),
    }