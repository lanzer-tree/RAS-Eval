import json
import os
import shutil
from datetime import date, datetime
from typing import Any, Dict, List, Optional

INIT_PATH = 'environment/initial/investment_init.json'
DATA_PATH = 'environment/reports/investment.json'

INIT = False


class InvalidRequestException(Exception):
    """Raised when the caller provides invalid arguments for a tool."""


class NotFoundException(Exception):
    """Raised when a requested investment or holding cannot be located."""


class InsufficientFundsException(Exception):
    """Raised when an account lacks enough cash to complete a purchase."""


class NegativeHoldingException(Exception):
    """Raised when a sell request would result in a negative holding balance."""


def _ensure_work_env() -> None:
    """Ensure the working environment file exists by copying from the init file when needed."""
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


def _parse_date(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError as error:
        raise InvalidRequestException(f'Date must be yyyy-mm-dd: {date_str}') from error


def _record_transaction(data: Dict[str, Any], transaction: Dict[str, Any]) -> None:
    data.setdefault('transactions', []).append(transaction)


def _normalize_account(account: str) -> str:
    """Normalize account name to lowercase for case-insensitive lookup."""
    return account.strip().lower()


def get_holdings_information(account: str) -> Dict[str, Any]:
    """Retrieve holdings and the cash balance for a specific account.

    Args:
        account (str): The account identifier to query.

    Returns:
        Dict[str, Any]: Holdings information and the available cash balance.

    Raises:
        InvalidRequestException: When the provided account is unsupported.
    """
    _ensure_work_env()
    data = _load_data()
    normalized = _normalize_account(account)
    account_data = data.get('accounts', {}).get(normalized)
    if not account_data:
        raise InvalidRequestException(f"Unsupported account: {account}")
    holdings = account_data.get('holdings', [])
    cash_balance = round(account_data.get('cash', 0.0), 2)
    return {'holdings': holdings, 'cash_balance': cash_balance}


def list_transactions(
    account: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: Optional[int] = 10,
) -> Dict[str, Any]:
    """List the transactions for an account filtered by date range and result count.

    Args:
        account (str): Account type to look up.
        start_date (Optional[str]): Start of the search window (yyyy-mm-dd).
        end_date (Optional[str]): End of the search window (yyyy-mm-dd).
        max_results (Optional[int]): Maximum number of transactions to return.

    Returns:
        Dict[str, Any]: Matching transactions and metadata about the request.

    Raises:
        InvalidRequestException: When the request parameters are invalid.
    """
    _ensure_work_env()
    data = _load_data()
    normalized = _normalize_account(account)
    account_data = data.get('accounts', {}).get(normalized)
    if not account_data:
        raise InvalidRequestException(f"Unsupported account: {account}")
    if max_results is None:
        max_results = 10
    if not (1 <= max_results <= 50):
        raise InvalidRequestException('max_results must be between 1 and 50.')
    transactions = [
        tx for tx in data.get('transactions', []) if tx.get('account') == normalized
    ]
    if start_date:
        start_boundary = _parse_date(start_date)
    elif transactions:
        start_boundary = min(_parse_date(tx['date']) for tx in transactions)
    else:
        start_boundary = date.today().replace(day=1)
    if end_date:
        end_boundary = _parse_date(end_date)
    else:
        end_boundary = date.today()
    if start_boundary > end_boundary:
        raise InvalidRequestException('start_date cannot be after end_date.')
    filtered = [
        tx for tx in transactions
        if start_boundary <= _parse_date(tx['date']) <= end_boundary
    ]
    filtered.sort(key=lambda tx: _parse_date(tx['date']), reverse=True)
    return {
        'transactions': filtered[:max_results],
        'total_matches': len(filtered),
        'start_date': start_boundary.strftime('%Y-%m-%d'),
        'end_date': end_boundary.strftime('%Y-%m-%d'),
    }


def search_investments(query: str, type: str, max_results: Optional[int] = 5) -> Dict[str, Any]:
    """Search the available investment options based on keyword and investment type.

    Args:
        query (str): Keyword to match against investment names and descriptions.
        type (str): The investment type to filter on (mutual_fund, ETF, or GIC).
        max_results (Optional[int]): Maximum number of results to return.

    Returns:
        Dict[str, Any]: Matching investment options along with the search parameters.

    Raises:
        InvalidRequestException: When inputs are empty or outside the allowed ranges.
    """
    if not query.strip():
        raise InvalidRequestException('query cannot be empty.')
    normalized_type = type.strip().lower()
    supported_types = {'mutual_fund', 'etf', 'gic'}
    if normalized_type not in supported_types:
        raise InvalidRequestException('type must be one of [mutual_fund, ETF, GIC].')
    if max_results is None:
        max_results = 5
    if max_results < 1 or max_results > 10:
        raise InvalidRequestException('max_results must be between 1 and 10.')
    _ensure_work_env()
    data = _load_data()
    options = data.get('investment_options', [])
    matches: List[Dict[str, Any]] = []
    lowered_query = query.lower()
    for option in options:
        option_type = option.get('type', '').lower()
        if option_type != normalized_type:
            continue
        name = option.get('name', '')
        description = option.get('description', '')
        if lowered_query in name.lower() or lowered_query in description.lower():
            matches.append(option)
        if len(matches) >= max_results:
            break
    return {'investment_options': matches[:max_results], 'query': query, 'type': type}


def make_transaction(account: str, action: str, name: str, amount: float) -> Dict[str, Any]:
    """Execute a buy or sell transaction for a specified investment.

    Args:
        account (str): The account in which to trade.
        action (str): Either 'buy' or 'sell'.
        name (str): The investment option or holding name.
        amount (float): The USD amount to trade.

    Returns:
        Dict[str, Any]: The updated cash balance and a descriptive message.

    Raises:
        InvalidRequestException: When required parameters are missing or invalid.
        NotFoundException: When the investment or holding cannot be located.
        InsufficientFundsException: When a buy would exceed the cash balance.
        NegativeHoldingException: When a sell would drop holdings below zero.
    """
    if not account.strip():
        raise InvalidRequestException('account cannot be empty.')
    normalized_action = action.strip().lower()
    if normalized_action not in {'buy', 'sell'}:
        raise InvalidRequestException("action must be 'buy' or 'sell'.")
    if not name.strip():
        raise InvalidRequestException('name cannot be empty.')
    if amount <= 0:
        raise InvalidRequestException('amount must be greater than zero.')
    _ensure_work_env()
    data = _load_data()
    normalized = _normalize_account(account)
    account_data = data.get('accounts', {}).get(normalized)
    if not account_data:
        raise InvalidRequestException(f"Unsupported account: {account}")
    holdings = account_data.setdefault('holdings', [])
    cash_balance = account_data.setdefault('cash', 0.0)
    today_str = date.today().strftime('%Y-%m-%d')
    if normalized_action == 'buy':
        option = next(
            (
                opt for opt in data.get('investment_options', [])
                if opt.get('name', '').lower() == name.lower()
            ),
            None,
        )
        if not option:
            raise NotFoundException(f'Investment option not found: {name}')
        min_amount = option.get('min_purchase_amount', 0.0)
        if amount < min_amount:
            raise InvalidRequestException(f'Amount must be at least {min_amount}.')
        if cash_balance < amount:
            raise InsufficientFundsException('Insufficient cash for this purchase.')
        cash_balance -= amount
        holding = next((h for h in holdings if h.get('name', '').lower() == name.lower()), None)
        if holding:
            holding['amount'] = round(holding.get('amount', 0.0) + amount, 2)
            holding['return'] = option.get('return', holding.get('return', 0.0))
        else:
            holdings.append({
                'type': option.get('type', 'unknown'),
                'name': option.get('name', name),
                'amount': round(amount, 2),
                'return': option.get('return', 0.0),
            })
        account_data['cash'] = round(cash_balance, 2)
        _record_transaction(data, {
            'date': today_str,
            'account': normalized,
            'type': option.get('type', 'unknown'),
            'name': option.get('name', name),
            'action': 'buy',
            'amount': round(amount, 2),
        })
        _save_data(data)
        return {
            'success': True,
            'cash_balance': account_data['cash'],
            'message': f'Bought {amount} USD of {name}.',
        }
    holding = next((h for h in holdings if h.get('name', '').lower() == name.lower()), None)
    if not holding:
        raise NotFoundException(f'Holding not found: {name}')
    if holding.get('amount', 0.0) < amount:
        raise NegativeHoldingException('Cannot sell more than the current holding amount.')
    holding['amount'] = round(holding.get('amount', 0.0) - amount, 2)
    if holding['amount'] <= 0:
        holdings.remove(holding)
    account_data['cash'] = round(cash_balance + amount, 2)
    _record_transaction(data, {
        'date': today_str,
        'account': normalized,
        'type': holding.get('type', 'unknown'),
        'name': holding.get('name', name),
        'action': 'sell',
        'amount': round(amount, 2),
    })
    _save_data(data)
    return {
        'success': True,
        'cash_balance': account_data['cash'],
        'message': f'Sold {amount} USD of {name}.',
    }
