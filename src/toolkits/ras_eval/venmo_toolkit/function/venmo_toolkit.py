import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/venmo.json'
INIT_PATH = 'environment/initial/venmo_init.json'

INIT = False


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


def _new_txn_id() -> str:
    return secrets.token_hex(8)


def _utc_now() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _find_user(data: Dict[str, Any], username: str) -> Dict[str, Any]:
    for u in data.get('users', []):
        if u.get('username') == username:
            return u
    return {}


def _find_account(data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
    for a in data.get('linked_accounts', []):
        if a.get('account_id') == account_id:
            return a
    return {}


def SendMoney(recipient_username: str, amount: float, note: str = '') -> Dict[str, Any]:
    """Send money to a user.
    
    Args:
        recipient_username (str): The username of the recipient.
        amount (float): The amount of money to send, must be positive.
        note (str): Optional note for the transaction.
    """
    if not recipient_username or not amount:
        raise InvalidRequestException("The 'recipient_username' or 'amount' parameter is not provided or invalid.")
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidRequestException("The 'amount' must be a valid number.")
    if amount <= 0:
        raise InvalidRequestException("The 'amount' is negative or exceeds the user's balance.")
    data = _load_data()
    if not _find_user(data, recipient_username):
        raise NotFoundException("The 'recipient_username' does not exist.")
    balance = data.get('balance', 0.0)
    if amount > balance:
        raise InvalidRequestException("The 'amount' is negative or exceeds the user's balance.")
    data['balance'] = round(balance - amount, 2)
    txn_id = _new_txn_id()
    txn = {
        'transaction_id': txn_id,
        'type': 'send',
        'date': _utc_now(),
        'amount': amount,
        'note': note or '',
        'status': 'completed',
        'is_starter': True,
        'other_user': recipient_username
    }
    data.setdefault('transactions', []).append(txn)
    _save_data(data)
    return {'result': {'success': True, 'transaction_id': txn_id, 'error_message': ''}}


def RequestMoney(requestee_username: str, amount: float, note: str = '') -> Dict[str, Any]:
    """Request money from a user.
    
    Args:
        requestee_username (str): The username of the user to request money from.
        amount (float): The amount of money to request, must be positive.
        note (str): Optional note for the transaction.
    """
    if not requestee_username or not amount:
        raise InvalidRequestException("The 'requestee_username' or 'amount' parameter is not provided or invalid.")
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidRequestException("The 'amount' must be a valid number.")
    if amount <= 0:
        raise InvalidRequestException("The 'amount' is negative.")
    data = _load_data()
    if not _find_user(data, requestee_username):
        raise NotFoundException("The 'requestee_username' does not exist.")
    txn_id = _new_txn_id()
    txn = {
        'transaction_id': txn_id,
        'type': 'request',
        'date': _utc_now(),
        'amount': amount,
        'note': note or '',
        'status': 'pending',
        'is_starter': True,
        'other_user': requestee_username
    }
    data.setdefault('transactions', []).append(txn)
    _save_data(data)
    return {'result': {'success': True, 'transaction_id': txn_id, 'error_message': ''}}


def HandleRequest(transaction_id: str, action: str, note: str = '') -> Dict[str, Any]:
    """Handle a pending money request by confirming or declining it.
    
    Args:
        transaction_id (str): The transaction ID of the pending request.
        action (str): The action to take, either 'confirm' or 'decline'.
        note (str): Optional note for the transaction.
    """
    if not transaction_id or not action:
        raise InvalidRequestException("The 'transaction_id' or 'action' parameter is not provided or invalid.")
    if action not in ['confirm', 'decline']:
        raise InvalidRequestException("The 'action' is not 'confirm' or 'decline', or the transaction is not a pending request, or the user is the starter of the transaction.")
    data = _load_data()
    target = None
    for t in data.get('transactions', []):
        if t.get('transaction_id') == transaction_id:
            target = t
            break
    if not target:
        raise NotFoundException("The 'transaction_id' does not exist.")
    if target.get('type') != 'request' or target.get('status') != 'pending':
        raise InvalidRequestException("The 'action' is not 'confirm' or 'decline', or the transaction is not a pending request, or the user is the starter of the transaction.")
    if target.get('is_starter'):
        raise InvalidRequestException("The 'action' is not 'confirm' or 'decline', or the transaction is not a pending request, or the user is the starter of the transaction.")
    if action == 'confirm':
        balance = data.get('balance', 0.0)
        if target.get('amount', 0) > balance:
            raise InvalidRequestException("The 'amount' is negative or exceeds the user's balance.")
        data['balance'] = round(balance - target['amount'], 2)
        target['status'] = 'confirmed'
    else:
        target['status'] = 'declined'
    target['note'] = note or target.get('note', '')
    _save_data(data)
    return {'result': {'success': True, 'error_message': ''}}


def CheckBalance() -> Dict[str, Any]:
    """Check the current account balance."""
    data = _load_data()
    return {'balance': data.get('balance', 0.0)}


def AddMoney(amount: float, account_id: str) -> Dict[str, Any]:
    """Add money to the account from a linked account.
    
    Args:
        amount (float): The amount of money to add, must be positive.
        account_id (str): The ID of the linked account to add money from.
    """
    if not amount or not account_id:
        raise InvalidRequestException("The 'amount' or 'account_id' parameter is not provided or invalid.")
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidRequestException("The 'amount' must be a valid number.")
    if amount <= 0:
        raise InvalidRequestException("The 'amount' is negative.")
    data = _load_data()
    if not _find_account(data, account_id):
        raise NotFoundException("The 'account_id' does not exist.")
    data['balance'] = round(data.get('balance', 0.0) + amount, 2)
    txn_id = _new_txn_id()
    txn = {
        'transaction_id': txn_id,
        'type': 'add',
        'date': _utc_now(),
        'amount': amount,
        'note': '',
        'status': 'completed',
        'is_starter': True,
        'other_user': '',
        'account_id': account_id
    }
    data.setdefault('transactions', []).append(txn)
    _save_data(data)
    return {'result': {'success': True, 'transaction_id': txn_id, 'error_message': ''}}


def WithdrawMoney(amount: float, account_id: str) -> Dict[str, Any]:
    """Withdraw money from the account to a linked account.
    
    Args:
        amount (float): The amount of money to withdraw, must be positive.
        account_id (str): The ID of the linked account to withdraw money to.
    """
    if not amount or not account_id:
        raise InvalidRequestException("The 'amount' or 'account_id' parameter is not provided or invalid.")
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidRequestException("The 'amount' must be a valid number.")
    if amount <= 0:
        raise InvalidRequestException("The 'amount' is negative or exceeds the user's balance.")
    data = _load_data()
    if not _find_account(data, account_id):
        raise NotFoundException("The 'account_id' does not exist.")
    balance = data.get('balance', 0.0)
    if amount > balance:
        raise InvalidRequestException("The 'amount' is negative or exceeds the user's balance.")
    data['balance'] = round(balance - amount, 2)
    txn_id = _new_txn_id()
    txn = {
        'transaction_id': txn_id,
        'type': 'withdraw',
        'date': _utc_now(),
        'amount': amount,
        'note': '',
        'status': 'completed',
        'is_starter': True,
        'other_user': '',
        'account_id': account_id
    }
    data.setdefault('transactions', []).append(txn)
    _save_data(data)
    return {'result': {'success': True, 'transaction_id': txn_id, 'error_message': ''}}


def SearchVenmoTransactions(username: str = '', query: str = '', transaction_type: str = 'all', max_results: int = 5) -> Dict[str, Any]:
    """Search for Venmo transactions with optional filters.
    
    Args:
        username (str): Filter by other user's username.
        query (str): Search query to match against transaction notes or usernames.
        transaction_type (str): Filter by transaction type, 'all' for no filter.
        max_results (int): Maximum number of results to return, between 1 and 10.
    """
    data = _load_data()
    try:
        max_results = int(max_results) if max_results else 5
    except ValueError:
        max_results = 5
    max_results = max(1, min(max_results, 10))
    if username and not _find_user(data, username):
        raise InvalidRequestException("The 'username' does not exist.")
    txns = []
    for t in data.get('transactions', []):
        if transaction_type not in ['all', '', None]:
            if t.get('type') != transaction_type:
                continue
        if username and t.get('other_user') != username:
            continue
        if query:
            note = t.get('note', '').lower()
            other = (t.get('other_user') or '').lower()
            if query.lower() not in note and query.lower() not in other:
                continue
        txns.append(t)
        if len(txns) >= max_results:
            break
    return {'transactions': txns}


def ViewFriendsList() -> Dict[str, Any]:
    """
    View the friends list.
    """
    data = _load_data()
    return {'friends': data.get('friends', [])}


def SearchUsers(query: str) -> Dict[str, Any]:
    """
    Search for users by username or display name.

    Args:
        query (str): The search query.
    """
    if query is None:
        raise InvalidRequestException("The 'query' parameter is required.")
    data = _load_data()
    results = []
    for u in data.get('users', []):
        if query.lower() in u.get('username', '').lower() or query.lower() in u.get('display_name', '').lower():
            results.append(u)
    return {'users': results}


def ListLinkedAccounts() -> Dict[str, Any]:
    """
    List linked accounts.
    """
    data = _load_data()
    return {'accounts': data.get('linked_accounts', [])}
