from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.toolkits.agentdojo.common import BankAccount, Filesystem, Transaction, UserAccount


@dataclass
class BankingEnvironment:
    bank_account: BankAccount
    filesystem: Filesystem
    user_account: UserAccount

    def snapshot(self) -> dict[str, Any]:
        return {
            "bank_account": self.bank_account.snapshot(),
            "filesystem": self.filesystem.snapshot(),
            "user_account": self.user_account.snapshot(),
        }


def _next_transaction_id(account: BankAccount) -> int:
    ids = [transaction.id for transaction in account.transactions]
    ids.extend(transaction.id for transaction in account.scheduled_transactions)
    return max(ids, default=0) + 1


def get_iban(environment: BankingEnvironment) -> str:
    """Get the IBAN of the current bank account.

    Returns:
        The account IBAN.
    """
    return environment.bank_account.iban


def send_money(environment: BankingEnvironment, recipient: str, amount: float, subject: str, date: str) -> dict[str, str]:
    """Send a transaction to the recipient.

    Args:
        recipient: IBAN of the recipient.
        amount: Amount of the transaction.
        subject: Subject of the transaction.
        date: Date of the transaction.

    Returns:
        A message describing the sent transaction.
    """
    account = environment.bank_account
    transaction = Transaction(
        id=_next_transaction_id(account),
        sender=account.iban,
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=False,
    )
    account.transactions.append(transaction)
    return {"message": f"Transaction to {recipient} for {amount} sent."}


def schedule_transaction(
    environment: BankingEnvironment,
    recipient: str,
    amount: float,
    subject: str,
    date: str,
    recurring: bool,
) -> dict[str, str]:
    """Schedule a transaction.

    Args:
        recipient: IBAN of the recipient.
        amount: Amount of the transaction.
        subject: Subject of the transaction.
        date: Next date of the transaction.
        recurring: Whether the transaction is recurring.

    Returns:
        A message describing the scheduled transaction.
    """
    account = environment.bank_account
    transaction = Transaction(
        id=_next_transaction_id(account),
        sender=account.iban,
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=recurring,
    )
    account.scheduled_transactions.append(transaction)
    return {"message": f"Transaction to {recipient} for {amount} scheduled."}


def update_scheduled_transaction(
    environment: BankingEnvironment,
    id: int,
    recipient: str | None = None,
    amount: float | None = None,
    subject: str | None = None,
    date: str | None = None,
    recurring: bool | None = None,
) -> dict[str, str]:
    """Update a scheduled transaction.

    Args:
        id: ID of the transaction to update.
        recipient: Optional new recipient IBAN.
        amount: Optional new amount.
        subject: Optional new subject.
        date: Optional new date.
        recurring: Optional new recurring flag.

    Returns:
        A message describing the update.

    Raises:
        ValueError: If the transaction ID does not exist.
    """
    transaction = next((item for item in environment.bank_account.scheduled_transactions if item.id == id), None)
    if transaction is None:
        raise ValueError(f"Transaction with ID {id} not found.")
    if recipient:
        transaction.recipient = recipient
    if amount:
        transaction.amount = amount
    if subject:
        transaction.subject = subject
    if date:
        transaction.date = date
    if recurring:
        transaction.recurring = recurring
    return {"message": f"Transaction with ID {id} updated."}


def get_balance(environment: BankingEnvironment) -> float:
    """Get the balance of the account.

    Returns:
        Current account balance.
    """
    return environment.bank_account.balance


def get_most_recent_transactions(environment: BankingEnvironment, n: int = 100) -> list[Transaction]:
    """Get the list of the most recent transactions.

    Args:
        n: Number of transactions to return.

    Returns:
        Most recent transactions in original order.
    """
    return [transaction for transaction in environment.bank_account.transactions[-int(n) :]]


def get_scheduled_transactions(environment: BankingEnvironment) -> list[Transaction]:
    """Get the list of scheduled transactions.

    Returns:
        Scheduled transactions.
    """
    return [transaction for transaction in environment.bank_account.scheduled_transactions]


def read_file(environment: BankingEnvironment, file_path: str) -> str:
    """Read the contents of the file at the given path.

    Args:
        file_path: The path to the file to read.

    Returns:
        File contents, or an empty string when the path is unknown.
    """
    return environment.filesystem.files.get(file_path, "")


def get_user_info(environment: BankingEnvironment) -> dict[str, str]:
    """Get the user information.

    Returns:
        Public user profile fields.
    """
    account = environment.user_account
    return {
        "first_name": account.first_name,
        "last_name": account.last_name,
        "street": account.street,
        "city": account.city,
    }


def update_password(environment: BankingEnvironment, password: str) -> dict[str, str]:
    """Update the user password.

    Args:
        password: New password for the user.

    Returns:
        A confirmation message.
    """
    environment.user_account.password = password
    return {"message": "Password updated."}


def update_user_info(
    environment: BankingEnvironment,
    first_name: str | None = None,
    last_name: str | None = None,
    street: str | None = None,
    city: str | None = None,
) -> dict[str, str]:
    """Update the user information.

    Args:
        first_name: Optional first name.
        last_name: Optional last name.
        street: Optional street.
        city: Optional city.

    Returns:
        Updated public user profile fields.
    """
    account = environment.user_account
    if first_name:
        account.first_name = first_name
    if last_name:
        account.last_name = last_name
    if street:
        account.street = street
    if city:
        account.city = city
    return get_user_info(environment)


TOOLS = [
    get_iban,
    send_money,
    schedule_transaction,
    update_scheduled_transaction,
    get_balance,
    get_most_recent_transactions,
    get_scheduled_transactions,
    read_file,
    get_user_info,
    update_password,
    update_user_info,
]
