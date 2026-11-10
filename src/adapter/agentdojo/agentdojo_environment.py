from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from typing import Any


from src.toolkits.agentdojo.common import (
    BankAccount,
    CalendarEvent,
    CalendarState,
    CarRental,
    CarRentalCompany,
    CloudDriveFile,
    CloudDriveState,
    Email,
    EmailContact,
    Filesystem,
    Flight,
    Flights,
    Hotel,
    Hotels,
    InboxState,
    Message,
    Reservation,
    Restaurant,
    Restaurants,
    SlackState,
    Transaction,
    User,
    UserAccount,
    WebState,
)
from src.toolkits.agentdojo.banking_toolkit.function import banking_toolkit as banking
from src.toolkits.agentdojo.slack_toolkit.function import slack_toolkit as slack
from src.toolkits.agentdojo.workspace_toolkit.function import workspace_toolkit as workspace
from src.toolkits.agentdojo.travel_toolkit.function import travel_toolkit as travel

REPO_ROOT = Path(__file__).resolve().parents[1]
# SUITE_DATA_ROOT = REPO_ROOT / "data" / "agentdojo" / "suites"


def _coerce_datetime(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time())
    return dt.datetime.fromisoformat(str(value))


def _coerce_date(value: Any) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


# def _load_suite_yaml(suite_name: str, injections: dict[str, str]) -> dict[str, Any]:
#     suite_dir = SUITE_DATA_ROOT / suite_name

#     class IncludeLoader(yaml.SafeLoader):
#         pass

#     def include(loader: IncludeLoader, node: yaml.Node) -> Any:
#         relative = loader.construct_scalar(node)
#         included_path = suite_dir / relative
#         text = included_path.read_text().format(**injections)
#         nested_loader = IncludeLoader(text)
#         nested_loader.name = str(included_path)
#         try:
#             return nested_loader.get_single_data()
#         finally:
#             nested_loader.dispose()

#     IncludeLoader.add_constructor("!include", include)
#     text = (suite_dir / "environment.yaml").read_text().format(**injections)
#     loader = IncludeLoader(text)
#     loader.name = str(suite_dir / "environment.yaml")
#     try:
#         return loader.get_single_data() or {}
#     finally:
#         loader.dispose()


def _make_transactions(items: list[dict[str, Any]]) -> list[Transaction]:
    return [Transaction(**item) for item in items]


def _make_emails(items: list[dict[str, Any]]) -> list[Email]:
    emails: list[Email] = []
    for item in items:
        data = dict(item)
        data["timestamp"] = _coerce_datetime(data.get("timestamp", dt.datetime.now()))
        emails.append(Email(**data))
    return emails


def _make_calendar_events(items: list[dict[str, Any]]) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    for item in items:
        data = dict(item)
        data["start_time"] = _coerce_datetime(data["start_time"])
        data["end_time"] = _coerce_datetime(data["end_time"])
        events.append(CalendarEvent(**data))
    return events


def _make_inbox(data: dict[str, Any]) -> InboxState:
    contacts = [EmailContact(**item) for item in data.get("contact_list", [])]
    return InboxState(
        account_email=data["account_email"],
        initial_emails=_make_emails(data.get("initial_emails", [])),
        contact_list=contacts,
        trash={},
    )


def _make_calendar(data: dict[str, Any]) -> CalendarState:
    return CalendarState(
        current_day=_coerce_date(data["current_day"]),
        account_email=data["account_email"],
        initial_events=_make_calendar_events(data.get("initial_events", [])),
    )


def _make_cloud_drive(data: dict[str, Any]) -> CloudDriveState:
    files = []
    for item in data.get("initial_files", []):
        file_data = {key: value for key, value in item.items() if key in {"id_", "filename", "content", "owner", "last_modified", "shared_with"}}
        file_data["last_modified"] = _coerce_datetime(file_data["last_modified"])
        files.append(CloudDriveFile(**file_data))
    return CloudDriveState(account_email=data["account_email"], initial_files=files)


# def _load_injection_defaults(suite_name: str) -> dict[str, str]:
#     """Load injection placeholder values from ``injection_vectors.yaml``.

#     Each entry is a mapping with ``description`` and ``default`` keys. Only the
#     ``default`` string is used to fill the placeholders in ``environment.yaml``;
#     passing the whole mapping would splice a Python dict repr into the YAML and
#     break parsing.
#     """
#     path = SUITE_DATA_ROOT / suite_name / "injection_vectors.yaml"
#     raw = yaml.safe_load(path.read_text()) or {}
#     return {key: value.get("default", "") for key, value in raw.items()}


# def load_suite_environment_data(suite_name: str) -> dict[str, Any]:
#     """Load the injection-filled environment data dict for a suite from YAML.

#     This is only used offline (e.g. by the dataset merge script) to bake the
#     environment into each sample's ``meta``. The result is JSON-safe so it can be
#     embedded directly into a JSONL row.
#     """
#     injections = _load_injection_defaults(suite_name)
#     data = _load_suite_yaml(suite_name, injections)
#     return to_plain(data)


# def make_environment(suite_name: str, sample: dict[str, Any]) -> Any:
#     meta = sample.get("meta", {})
#     if "environment" not in meta:
#         raise KeyError(
#             "sample.meta.environment is missing; regenerate the dataset so the "
#             "environment data is embedded in meta (see scripts/merge_agentdojo_env.py)"
#         )
#     return build_environment(suite_name, meta["environment"])


def build_environment(suite_name: str, data: dict[str, Any]) -> Any:
    if suite_name == "banking":
        return banking.BankingEnvironment(
            bank_account=BankAccount(
                balance=data["bank_account"]["balance"],
                iban=data["bank_account"]["iban"],
                transactions=_make_transactions(data["bank_account"].get("transactions", [])),
                scheduled_transactions=_make_transactions(data["bank_account"].get("scheduled_transactions", [])),
            ),
            filesystem=Filesystem(files=data["filesystem"].get("files", {})),
            user_account=UserAccount(**data["user_account"]),
        )
    if suite_name == "workspace":
        return workspace.WorkspaceEnvironment(
            inbox=_make_inbox(data["inbox"]),
            calendar=_make_calendar(data["calendar"]),
            cloud_drive=_make_cloud_drive(data["cloud_drive"]),
        )
    if suite_name == "slack":
        slack_data = data["slack"]
        return slack.SlackEnvironment(
            slack=SlackState(
                users=slack_data.get("users", []),
                channels=slack_data.get("channels", []),
                user_channels=slack_data.get("user_channels", {}),
                user_inbox={key: [Message(**item) for item in value] for key, value in slack_data.get("user_inbox", {}).items()},
                channel_inbox={key: [Message(**item) for item in value] for key, value in slack_data.get("channel_inbox", {}).items()},
            ),
            web=WebState(**data["web"]),
        )
    if suite_name == "travel":
        return travel.TravelEnvironment(
            hotels=Hotels([Hotel(**item) for item in data["hotels"].get("hotel_list", [])]),
            restaurants=Restaurants([Restaurant(**item) for item in data["restaurants"].get("restaurant_list", [])]),
            car_rental=CarRental([CarRentalCompany(**item) for item in data["car_rental"].get("company_list", [])]),
            flights=Flights([
                Flight(**{**item, "departure_time": _coerce_datetime(item["departure_time"]), "arrival_time": _coerce_datetime(item["arrival_time"])})
                for item in data["flights"].get("flight_list", [])
            ]),
            user=User(**data["user"]),
            calendar=_make_calendar(data["calendar"]),
            reservation=Reservation(
                reservation_type=data["reservation"].get("reservation_type"),
                title=data["reservation"].get("title", ""),
                start_time=_coerce_datetime(data["reservation"].get("start_time", dt.datetime.now())),
                end_time=_coerce_datetime(data["reservation"].get("end_time", dt.datetime.now())),
                contact_information=data["reservation"].get("contact_information", ""),
            ),
            inbox=_make_inbox(data["inbox"]),
        )
    raise ValueError(f"Unsupported AgentDojo suite: {suite_name}")


def dump_environment(environment: Any, dump_dir: Path) -> None:
    dump_dir = Path(dump_dir)
    dump_dir.mkdir(parents=True, exist_ok=True)
    for name, value in environment.snapshot().items():
        (dump_dir / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def suite_tools(suite_name: str) -> list[Any]:
    if suite_name == "banking":
        return banking.TOOLS
    if suite_name == "workspace":
        return workspace.TOOLS
    if suite_name == "slack":
        return slack.TOOLS
    if suite_name == "travel":
        return travel.TOOLS
    raise ValueError(f"Unsupported AgentDojo suite: {suite_name}")
