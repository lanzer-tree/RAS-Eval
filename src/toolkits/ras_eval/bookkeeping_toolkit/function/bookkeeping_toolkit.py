import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List

DATA_PATH = "environment/reports/bookkeeping.json"
INIT_PATH = "environment/initial/bookkeeping_init.json"

INIT = False


class InvalidRequestException(Exception):
    """Raise when request parameters are missing or malformed."""


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


def AddTransaction(date: str, description: str, amount: float, category: str = "") -> str:
    """
    Add a new financial transaction to the bookkeeping system.

    Args:
        date: The date of the transaction in YYYY-MM-DD format.
        description: A description of the transaction.
        amount: The amount of the transaction. Positive for income, negative for expense.
        category: The category of the transaction.
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise InvalidRequestException("Date must be in YYYY-MM-DD format.")

    if not isinstance(amount, (int, float)):
        raise InvalidRequestException("Amount must be a number.")

    data = _load_data()
    transaction_id = f"txn_{len(data['transactions']) + 1:03d}"
    transaction = {
        "transaction_id": transaction_id,
        "date": date,
        "description": description,
        "amount": amount,
        "category": category
    }
    data["transactions"].append(transaction)
    data["balance"] += amount
    _save_data(data)
    return transaction_id


def GetTransactions(start_date: str = "", end_date: str = "", category: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve a list of transactions based on filters.

    Args:
        start_date: The start date for filtering in YYYY-MM-DD format.
        end_date: The end date for filtering in YYYY-MM-DD format.
        category: The category to filter by.
        limit: The maximum number of transactions to retrieve.
    """
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidRequestException("Start date must be in YYYY-MM-DD format.")
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidRequestException("End date must be in YYYY-MM-DD format.")
    if limit is None:
        limit = 10
    if limit <= 0:
        raise InvalidRequestException("Limit must be a positive integer.")

    data = _load_data()
    transactions = data["transactions"]

    # Filter by date
    if start_date:
        transactions = [t for t in transactions if t["date"] >= start_date]
    if end_date:
        transactions = [t for t in transactions if t["date"] <= end_date]

    # Filter by category
    if category:
        transactions = [t for t in transactions if t["category"] == category]

    # Sort by date descending
    transactions.sort(key=lambda x: x["date"], reverse=True)

    # Limit
    transactions = transactions[:limit]

    return transactions


def bookkeeping_GetBalance(date: str = "", account: str='') -> float:
    """
    Calculate the balance up to a specific date or current balance.

    Args:
        date: The date up to which to calculate the balance in YYYY-MM-DD format.
        account: The account type to query balance for (e.g., 'checking', 'savings'). If not provided, returns the overall balance.
    """
    if date:
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise InvalidRequestException('Date must be in YYYY-MM-DD format.')
    data = _load_data()
    # For simplicity, we'll return the overall balance regardless of account type
    # In a real system, you would have separate account balances
    if not date:
        return {'balance': data['balance'], 'account': account if account else 'all'}
    balance = 0.0
    for transaction in data['transactions']:
        if transaction['date'] <= date:
            balance += transaction['amount']
    return {'balance': balance, 'account': account if account else 'all'}


def GenerateReport(start_date: str, end_date: str, report_type: str = "summary") -> str:
    """
    Generate a financial report for a given period.

    Args:
        start_date: The start date of the report period in YYYY-MM-DD format.
        end_date: The end date of the report period in YYYY-MM-DD format.
        report_type: The type of report: 'summary' or 'detailed'.

    Raises:
        InvalidRequestException: If parameters are invalid.
    """
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise InvalidRequestException("Dates must be in YYYY-MM-DD format.")

    if report_type not in ["summary", "detailed"]:
        raise InvalidRequestException("Report type must be 'summary' or 'detailed'.")

    transactions = GetTransactions(start_date=start_date, end_date=end_date, limit=1000)

    total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    total_expenses = sum(t["amount"] for t in transactions if t["amount"] < 0)
    net = total_income + total_expenses

    if report_type == "summary":
        report = f"Report from {start_date} to {end_date}\n"
        report += f"Total Income: ${total_income:.2f}\n"
        report += f"Total Expenses: ${-total_expenses:.2f}\n"
        report += f"Net Change: ${net:.2f}\n"
    else:
        report = f"Detailed Report from {start_date} to {end_date}\n\n"
        report += "Transactions:\n"
        for t in transactions:
            report += f"{t['date']}: {t['description']} - ${t['amount']:.2f} ({t['category']})\n"
        report += f"\nTotal Income: ${total_income:.2f}\n"
        report += f"Total Expenses: ${-total_expenses:.2f}\n"
        report += f"Net Change: ${net:.2f}\n"

    return report


def DeleteTransaction(transaction_id: str) -> bool:
    """
    Delete a transaction from the bookkeeping system.

    Args:
        transaction_id: The unique identifier of the transaction to delete.

    Raises:
        NotFoundException: If the transaction_id does not exist.
    """
    data = _load_data()
    for i, transaction in enumerate(data["transactions"]):
        if transaction["transaction_id"] == transaction_id:
            amount = transaction["amount"]
            data["balance"] -= amount  # Reverse the effect on balance
            del data["transactions"][i]
            _save_data(data)
            return True
    raise Exception("Transaction not found.")


def UpdateTransaction(transaction_id: str, date: str = "", description: str = "", amount: float = None, category: str = "") -> bool:
    """
    Update an existing transaction in the bookkeeping system.

    Args:
        transaction_id: The unique identifier of the transaction to update.
        date: The new date of the transaction in YYYY-MM-DD format.
        description: The new description of the transaction.
        amount: The new amount of the transaction. Positive for income, negative for expense.
        category: The new category of the transaction.

    Raises:
        NotFoundException: If the transaction_id does not exist.
        InvalidRequestException: If parameters are invalid.
    """
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise InvalidRequestException("Date must be in YYYY-MM-DD format.")

    if amount is not None and not isinstance(amount, (int, float)):
        raise InvalidRequestException("Amount must be a number.")

    data = _load_data()
    for transaction in data["transactions"]:
        if transaction["transaction_id"] == transaction_id:
            old_amount = transaction["amount"]
            if date:
                transaction["date"] = date
            if description:
                transaction["description"] = description
            if amount is not None:
                transaction["amount"] = amount
                data["balance"] += amount - old_amount  # Adjust balance
            if category:
                transaction["category"] = category
            _save_data(data)
            return True
    raise Exception("Transaction not found.")


def GetCategorySummary(category: str, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
    """
    Get a summary of transactions for a specific category within a date range.

    Args:
        category: The category to summarize.
        start_date: The start date for the summary in YYYY-MM-DD format.
        end_date: The end date for the summary in YYYY-MM-DD format.

    Returns:
        An object containing 'total_income', 'total_expenses', 'net_amount', and 'transaction_count'.

    Raises:
        InvalidRequestException: If dates are invalid.
    """
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidRequestException("Start date must be in YYYY-MM-DD format.")
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidRequestException("End date must be in YYYY-MM-DD format.")

    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            raise InvalidRequestException('Start date must be in YYYY-MM-DD format.')
    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise InvalidRequestException('End date must be in YYYY-MM-DD format.')

    data = _load_data()
    transactions = data['transactions']
    if start_date:
        transactions = [t for t in transactions if t['date'] >= start_date]
    if end_date:
        transactions = [t for t in transactions if t['date'] <= end_date]
    if category:
        transactions = [t for t in transactions if t['category'] == category]
    transactions.sort(key=lambda x: x['date'], reverse=True)
    total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    total_expenses = sum(t["amount"] for t in transactions if t["amount"] < 0)
    net_amount = total_income + total_expenses
    transaction_count = len(transactions)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_amount": net_amount,
        "transaction_count": transaction_count
    }