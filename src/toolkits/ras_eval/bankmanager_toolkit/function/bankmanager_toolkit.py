import os
import json
import shutil
import re
from datetime import datetime
from typing import Any, Dict, List

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..', '..', '..'))
_init_candidate = os.path.join(_WORKSPACE_ROOT, 'environment', 'initial', 'bankmanager_init.json')
if not os.path.exists(_init_candidate) and os.path.exists('/workspace/environment/initial/bankmanager_init.json'):
    _WORKSPACE_ROOT = '/workspace'

DATA_PATH = os.path.join(_WORKSPACE_ROOT, 'environment', 'reports', 'bankmanager.json')
INIT_PATH = os.path.join(_WORKSPACE_ROOT, 'environment', 'initial', 'bankmanager_init.json')

INIT = False
ACCOUNT_PATTERN = re.compile(r'^[A-Za-z\d-]+$')
PAYEE_PATTERN = re.compile(r'^(P-\d{6}|[A-Z]+-\d{3,})$')
VALID_ACCOUNT_TYPES = {
    'checking',
    'savings',
    'mutual fund TFSA',
    'mutual fund non-registered',
    'self-directed TFSA',
    'self-directed non-registered',
    'mortgage',
    'credit_card'
}


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
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
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _validate_account_number(account_number: str):
    if not ACCOUNT_PATTERN.match(account_number):
        raise InvalidRequestException("The 'account_number' parameter is not in the correct format.")


def _validate_account_type(account_type: str):
    if account_type not in VALID_ACCOUNT_TYPES:
        raise InvalidRequestException("The 'account_type' parameter is invalid.")


def _validate_payee_id(payee_id: str):
    if not PAYEE_PATTERN.match(payee_id):
        raise InvalidRequestException("The 'payee_id' parameter is invalid.")


def _normalize_acct_num(account_number: str) -> str:
    return account_number.replace('-', '')


def _get_account(data: Dict[str, Any], account_number: str) -> Dict[str, Any]:
    _validate_account_number(account_number)
    normalized_input = _normalize_acct_num(account_number)
    account = next((a for a in data.get('accounts', []) if _normalize_acct_num(a.get('account_number', '')) == normalized_input), None)
    if not account:
        raise NotFoundException('Account not found.')
    return account


def _record_transaction(data: Dict[str, Any], account_number: str, description: str, amount: float, balance: float):
    key = _normalize_acct_num(account_number)
    tx = {
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'description': description,
        'amount': round(amount, 2),
        'balance': round(balance, 2)
    }
    transactions = data.setdefault('transactions', {})
    transactions.setdefault(key, []).append(tx)


def GetAccountInformation(account_type: str) -> Dict[str, Any]:
    """Retrieves account information for a specific account type.

    Args:
        account_type (str): The type of account to retrieve information for.
    """
    _validate_account_type(account_type)
    data = _load_data()
    accounts = [a for a in data.get('accounts', []) if a.get('type') == account_type]
    return {'accounts': accounts}


def TransferFunds(from_account_number: str, to_account_number: str, amount: float) -> Dict[str, Any]:
    """Transfers funds from one account to another.

    Args:
        from_account_number (str): The account number to transfer funds from.
        to_account_number (str): The account number to transfer funds to.
        amount (float): The amount of funds to transfer.
    """
    try:
        amount_val = float(amount)
    except Exception:
        raise InvalidRequestException("The 'amount' parameter is not valid.")
    if amount_val <= 0:
        raise InvalidRequestException("The 'amount' parameter is not valid.")
    data = _load_data()
    from_acct = _get_account(data, from_account_number)
    to_acct = _get_account(data, to_account_number)
    if not from_acct.get('owned_by_user', False):
        raise InvalidRequestException("The 'from_account_number' is not owned by the user.")
    if from_acct.get('balance', 0) < amount_val:
        raise InvalidRequestException('Insufficient funds.')
    from_acct['balance'] = round(from_acct.get('balance', 0) - amount_val, 2)
    to_acct['balance'] = round(to_acct.get('balance', 0) + amount_val, 2)
    _record_transaction(data, from_account_number, f'Transfer to {to_account_number}', -amount_val, from_acct['balance'])
    _record_transaction(data, to_account_number, f'Transfer from {from_account_number}', amount_val, to_acct['balance'])
    _save_data(data)
    return {'success': True}


def SearchPayee(keywords: str) -> Dict[str, Any]:
    """Searches for payees by keywords.

    Args:
        keywords (str): The keywords to search for, can be a string or list of strings.
    """
    if isinstance(keywords, str):
        keywords = keywords.split()
    if not isinstance(keywords, list):
        raise InvalidRequestException("The 'keywords' parameter is invalid.")
    keywords_lower = [k.lower() for k in keywords if isinstance(k, str) and k.strip()]
    if not keywords_lower:
        return {'payees': []}
    data = _load_data()
    payees = []
    for p in data.get('payees', []):
        name_lower = p.get('payee_name', '').lower()
        if any(k in name_lower for k in keywords_lower):
            payees.append({'payee_id': p.get('payee_id'), 'payee_name': p.get('payee_name')})
    return {'payees': payees}


def PayBill(from_account_number: str, payee_id: str, service_account_number: str, payment_date: str, amount: float) -> Dict[str, Any]:
    """Pays a bill to a payee from a user account.

    Args:
        from_account_number (str): The account number to pay the bill from.
        payee_id (str): The ID of the payee to pay.
        service_account_number (str): The service account number for the bill.
        payment_date (str): The date of the payment.
        amount (float): The amount to pay.
    """
    try:
        amount_val = float(amount)
    except Exception:
        raise InvalidRequestException("The 'amount' parameter is not valid.")
    if amount_val <= 0:
        raise InvalidRequestException("The 'amount' parameter is not valid.")
    if not service_account_number:
        raise InvalidRequestException("The 'service_account_number' parameter is not valid.")
    data = _load_data()
    from_acct = _get_account(data, from_account_number)
    if not from_acct.get('owned_by_user', False):
        raise InvalidRequestException("The 'from_account_number' is not owned by the user.")
    _validate_payee_id(payee_id)
    payee = next((p for p in data.get('payees', []) if p.get('payee_id') == payee_id), None)
    if not payee:
        raise NotFoundException('Payee not found.')
    if from_acct.get('balance', 0) < amount_val:
        raise InvalidRequestException('Insufficient funds.')
    from_acct['balance'] = round(from_acct.get('balance', 0) - amount_val, 2)
    desc = f"Bill payment to {payee.get('payee_name')} ({payee_id}) ref {service_account_number}"
    _record_transaction(data, from_account_number, desc, -amount_val, from_acct['balance'])
    payments = data.setdefault('bill_payments', [])
    payments.append({
        'from_account_number': from_account_number,
        'payee_id': payee_id,
        'service_account_number': service_account_number,
        'payment_date': payment_date,
        'amount': round(amount_val, 2)
    })
    _save_data(data)
    return {'success': True}


def GetAccountStatement(account_number: str, start_date: str, end_date: str, download: bool = False) -> Dict[str, Any]:
    """Retrieves account statement for a specific date range.

    Args:
        account_number (str): The account number to retrieve statement for.
        start_date (str): The start date of the statement period.
        end_date (str): The end date of the statement period.
        download (bool): Whether to download the statement as a CSV file.
    """
    _validate_account_number(account_number)
    data = _load_data()
    _get_account(data, account_number)
    normalized = _normalize_acct_num(account_number)
    txs = data.get('transactions', {}).get(normalized, [])
    filtered = [t for t in txs if start_date <= t.get('date', '') <= end_date]
    statement_path = ''
    if download:
        if not os.path.exists(os.path.dirname(DATA_PATH)):
            os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        filename = f"bankmanager_statement_{account_number.replace('-', '')}.csv"
        statement_path = os.path.join(os.path.dirname(DATA_PATH), filename)
        lines = ['date,description,amount,balance']
        for t in filtered:
            lines.append(f"{t.get('date','')},{t.get('description','').replace(',', ' ')},{t.get('amount','')},{t.get('balance','')}")
        with open(statement_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    return {'transactions': filtered, 'statement_file_path': statement_path}


def GetBalance(account: str) -> Dict[str, Any]:
    """Return the available balance for the specified account.

    Args:
        account (str): The account type or account number to query balance for.
    """
    if not account:
        raise InvalidRequestException("The 'account' parameter is required.")
    data = _load_data()
    account_lower = account.strip().lower()
    if account_lower.endswith(' account'):
        account_lower = account_lower[:-8].strip()
    for acct in data.get('accounts', []):
        if acct.get('account_number') == account:
            return {'balance': round(float(acct.get('balance', 0.0)), 2)}
        if acct.get('type', '').lower() == account_lower:
            return {'balance': round(float(acct.get('balance', 0.0)), 2)}
    raise InvalidRequestException("The 'account' parameter is not in the correct format.")


def SearchTransactions(account_number: str, keyword: str = '', min_amount: float = None, max_amount: float = None) -> Dict[str, Any]:
    """Searches for bank transactions by keyword and amount range.

    Args:
        account_number (str): The account number to search transactions for.
        keyword (str): The keyword to search for in transaction descriptions.
        min_amount (float): The minimum amount to filter by.
        max_amount (float): The maximum amount to filter by.
    """
    data = _load_data()
    _get_account(data, account_number)
    normalized = _normalize_acct_num(account_number)
    txs = data.get('transactions', {}).get(normalized, [])
    results = []
    for t in txs:
        amount = abs(float(t.get('amount', 0)))
        if keyword and keyword.lower() not in t.get('description', '').lower():
            continue
        if min_amount is not None:
            try:
                if amount < float(min_amount):
                    continue
            except Exception:
                raise InvalidRequestException("The 'min_amount' parameter is not valid.")
        if max_amount is not None:
            try:
                if amount > float(max_amount):
                    continue
            except Exception:
                raise InvalidRequestException("The 'max_amount' parameter is not valid.")
        results.append(t)
    return {'transactions': results}
