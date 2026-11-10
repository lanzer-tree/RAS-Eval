from __future__ import annotations

import copy
import datetime as dt
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import StrEnum
from typing import Any


class SharingPermission(StrEnum):
    r = "r"
    rw = "rw"


class EventStatus(StrEnum):
    confirmed = "confirmed"
    canceled = "canceled"


class EmailStatus(StrEnum):
    sent = "sent"
    received = "received"
    draft = "draft"


class ReservationType(StrEnum):
    HOTEL = "hotel"
    CAR = "car"
    RESTAURANT = "restaurant"


def parse_datetime(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, "%Y-%m-%d %H:%M")


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return value


class SerializableState:
    def snapshot(self) -> dict[str, Any]:
        return to_plain(self)

    def clone(self):
        return copy.deepcopy(self)


@dataclass
class Transaction(SerializableState):
    id: int
    sender: str
    recipient: str
    amount: float
    subject: str
    date: str
    recurring: bool


@dataclass
class BankAccount(SerializableState):
    balance: float
    iban: str
    transactions: list[Transaction] = field(default_factory=list)
    scheduled_transactions: list[Transaction] = field(default_factory=list)


@dataclass
class Filesystem(SerializableState):
    files: dict[str, str] = field(default_factory=dict)


@dataclass
class UserAccount(SerializableState):
    first_name: str
    last_name: str
    street: str
    city: str
    password: str


@dataclass
class Message(SerializableState):
    sender: str
    recipient: str
    body: str


@dataclass
class SlackState(SerializableState):
    users: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    user_channels: dict[str, list[str]] = field(default_factory=dict)
    user_inbox: dict[str, list[Message]] = field(default_factory=dict)
    channel_inbox: dict[str, list[Message]] = field(default_factory=dict)


@dataclass
class WebState(SerializableState):
    web_content: dict[str, str] = field(default_factory=dict)
    web_requests: list[str] = field(default_factory=list)


@dataclass
class CloudDriveFile(SerializableState):
    id_: str
    filename: str
    content: str
    owner: str
    last_modified: dt.datetime
    shared_with: dict[str, SharingPermission | str] = field(default_factory=dict)
    size: int = 0

    def __post_init__(self) -> None:
        self.size = len(self.content)


@dataclass
class CalendarEvent(SerializableState):
    id_: str
    title: str
    description: str
    start_time: dt.datetime
    end_time: dt.datetime
    location: str | None
    participants: list[str]
    all_day: bool = False
    status: EventStatus | str = EventStatus.confirmed


@dataclass
class EmailContact(SerializableState):
    email: str
    name: str


@dataclass
class Email(SerializableState):
    id_: str
    sender: str
    recipients: list[str]
    subject: str
    body: str
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    status: EmailStatus | str = EmailStatus.sent
    read: bool = False
    timestamp: dt.datetime = field(default_factory=dt.datetime.now)
    attachments: list[Any] = field(default_factory=list)


@dataclass
class InboxState(SerializableState):
    account_email: str
    initial_emails: list[Email] = field(default_factory=list)
    emails: dict[str, Email] = field(default_factory=dict)
    contact_list: list[EmailContact] = field(default_factory=list)
    trash: dict[str, Email] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.emails:
            ids = [email.id_ for email in self.initial_emails]
            duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
            if duplicates:
                raise ValueError(f"Email IDs must be unique. Duplicates: {duplicates}")
            self.emails = {email.id_: email for email in self.initial_emails}
        existing_contacts: set[str] = {contact.email for contact in self.contact_list}
        for email in self.initial_emails:
            for address in [*email.recipients, email.sender, *email.cc, *email.bcc]:
                if address not in existing_contacts:
                    name = address.split("@")[0].replace(".", " ").title()
                    self.contact_list.append(EmailContact(email=address, name=name))
                    existing_contacts.add(address)

    @property
    def received(self) -> list[Email]:
        return [email for email in self.emails.values() if email.status == EmailStatus.received]

    @property
    def sent(self) -> list[Email]:
        return [email for email in self.emails.values() if email.status == EmailStatus.sent]

    @property
    def drafts(self) -> list[Email]:
        return [email for email in self.emails.values() if email.status == EmailStatus.draft]

    def next_id(self) -> str:
        return str(max((int(key) for key in self.emails.keys()), default=0) + 1)


@dataclass
class CalendarState(SerializableState):
    current_day: dt.date
    account_email: str
    initial_events: list[CalendarEvent] = field(default_factory=list)
    events: dict[str, CalendarEvent] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.events:
            ids = [event.id_ for event in self.initial_events]
            duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
            if duplicates:
                raise ValueError(f"Event IDs must be unique. Duplicates: {duplicates}")
            self.events = {event.id_: event for event in self.initial_events}

    def next_id(self) -> str:
        return str(max((int(key) for key in self.events.keys()), default=0) + 1)


@dataclass
class CloudDriveState(SerializableState):
    account_email: str
    initial_files: list[CloudDriveFile] = field(default_factory=list)
    files: dict[str, CloudDriveFile] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.files:
            ids = [file.id_ for file in self.initial_files]
            duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
            if duplicates:
                raise ValueError(f"File IDs must be unique. Duplicates: {duplicates}")
            self.files = {file.id_: file for file in self.initial_files}

    def next_id(self) -> str:
        return str(max((int(key) for key in self.files.keys()), default=0) + 1)


@dataclass
class User(SerializableState):
    first_name: str
    last_name: str
    ID_number: str
    email: str
    phone_number: str
    address: str
    passport_number: str
    bank_account_number: str
    credit_card_number: str


@dataclass
class Hotel(SerializableState):
    name: str
    city: str
    rating: float
    price_min: float
    price_max: float
    address: str
    reviews: list[str]


@dataclass
class Hotels(SerializableState):
    hotel_list: list[Hotel] = field(default_factory=list)


@dataclass
class Flight(SerializableState):
    airline: str
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_time: dt.datetime
    arrival_time: dt.datetime
    price: float
    contact_information: str


@dataclass
class Flights(SerializableState):
    flight_list: list[Flight] = field(default_factory=list)


@dataclass
class Reservation(SerializableState):
    reservation_type: ReservationType | str | None
    title: str
    start_time: dt.datetime
    end_time: dt.datetime
    contact_information: str


@dataclass
class Restaurant(SerializableState):
    name: str
    city: str
    address: str
    rating: float
    price_per_person: float
    operating_hours: str
    reviews: list[str]
    contact_information: str
    cuisine_type: str
    dietary_restrictions: str


@dataclass
class Restaurants(SerializableState):
    restaurant_list: list[Restaurant] = field(default_factory=list)


@dataclass
class CarRentalCompany(SerializableState):
    name: str
    city: str
    address: str
    rating: float
    price_per_day: float
    reviews: list[str]
    contact_information: str
    car_types_available: list[str]
    fuel_options: list[str]


@dataclass
class CarRental(SerializableState):
    company_list: list[CarRentalCompany] = field(default_factory=list)
