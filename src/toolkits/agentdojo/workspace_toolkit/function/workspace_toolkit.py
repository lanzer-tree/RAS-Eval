from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from src.toolkits.agentdojo.common import (
    CalendarEvent,
    CalendarState,
    CloudDriveFile,
    CloudDriveState,
    Email,
    EmailContact,
    EmailStatus,
    EventStatus,
    InboxState,
    SharingPermission,
    parse_datetime,
)


@dataclass
class WorkspaceEnvironment:
    inbox: InboxState
    calendar: CalendarState
    cloud_drive: CloudDriveState

    def snapshot(self) -> dict[str, Any]:
        return {
            "inbox": self.inbox.snapshot(),
            "calendar": self.calendar.snapshot(),
            "cloud_drive": self.cloud_drive.snapshot(),
        }


def _email_by_status(inbox: InboxState, status: EmailStatus) -> list[Email]:
    return [email for email in inbox.emails.values() if email.status == status]


def _send_email(
    inbox: InboxState,
    recipients: list[str],
    subject: str,
    body: str,
    attachments: list[Any] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> Email:
    email = Email(
        id_=inbox.next_id(),
        sender=inbox.account_email,
        recipients=recipients,
        subject=subject,
        body=body,
        status=EmailStatus.sent,
        timestamp=dt.datetime.now(),
        attachments=[] if attachments is None else attachments,
        cc=[] if cc is None else cc,
        bcc=[] if bcc is None else bcc,
        read=True,
    )
    inbox.emails[email.id_] = email
    return email


def get_unread_emails(environment: WorkspaceEnvironment) -> list[Email]:
    """Return all unread emails and mark them as read.

    Returns:
        The unread emails before the call.
    """
    unread = [email for email in environment.inbox.emails.values() if not email.read]
    for email in unread:
        email.read = True
    return unread


def send_email(
    environment: WorkspaceEnvironment,
    recipients: list[str],
    subject: str,
    body: str,
    attachments: list[dict] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> Email:
    """Send an email with the given body to the given recipients.

    Args:
        recipients: Email addresses of the recipients.
        subject: The email subject.
        body: The email body.
        attachments: Optional file or event attachment dictionaries.
        cc: Optional CC recipients.
        bcc: Optional BCC recipients.

    Returns:
        The created sent email.
    """
    parsed_attachments: list[Any] | None = None
    if attachments is not None:
        parsed_attachments = []
        for attachment in attachments:
            if not isinstance(attachment, dict):
                raise ValueError("Attachments must be dictionaries.")
            if "type" not in attachment:
                raise ValueError("Attachment must have a 'type' field.")
            if attachment["type"] == "file" or "file_id" in attachment:
                if "file_id" not in attachment:
                    raise ValueError("Attachment of type 'file' must have a 'file_id' field.")
                parsed_attachments.append(attachment["file_id"])
            else:
                if "event_details" not in attachment:
                    raise ValueError("Attachment of type 'event' must have an 'event_details' field.")
                details = attachment["event_details"]
                parsed_attachments.append(
                    CalendarEvent(
                        id_=details["id_"],
                        title=details["title"],
                        description=details["description"],
                        start_time=dt.datetime.fromisoformat(details["start_time"]),
                        end_time=dt.datetime.fromisoformat(details["end_time"]),
                        location=details.get("location"),
                        participants=details["participants"],
                    )
                )
    return _send_email(environment.inbox, recipients, subject, body, parsed_attachments, cc, bcc)


def search_emails(environment: WorkspaceEnvironment, query: str, sender: str | None = None) -> list[Email]:
    """Search emails by query, optionally restricting to a sender.

    Args:
        query: Query to search in subject or body.
        sender: Optional sender email address.

    Returns:
        Matching emails.

    Raises:
        ValueError: If no emails match.
    """
    emails = environment.inbox.emails.values()
    if sender is not None:
        emails = [email for email in emails if email.sender.lower() == sender.lower()]
    matches = [email for email in emails if query.lower() in email.subject.lower() or query.lower() in email.body.lower()]
    if not matches:
        raise ValueError("No emails found. Try with a different query.")
    return matches


def delete_email(environment: WorkspaceEnvironment, email_id: str) -> str:
    """Delete an email from the inbox.

    Args:
        email_id: The ID of the email to delete.

    Returns:
        A confirmation message.
    """
    if email_id not in environment.inbox.emails:
        raise ValueError(f"Email with ID '{email_id}' not found.")
    environment.inbox.trash[email_id] = environment.inbox.emails.pop(email_id)
    return f"Email with id {email_id} deleted successfully."


def get_sent_emails(environment: WorkspaceEnvironment) -> list[Email]:
    """Return all sent emails."""
    return _email_by_status(environment.inbox, EmailStatus.sent)


def get_received_emails(environment: WorkspaceEnvironment) -> list[Email]:
    """Return all received emails."""
    return _email_by_status(environment.inbox, EmailStatus.received)


def get_draft_emails(environment: WorkspaceEnvironment) -> list[Email]:
    """Return all draft emails."""
    return _email_by_status(environment.inbox, EmailStatus.draft)


def search_contacts_by_name(environment: WorkspaceEnvironment, query: str) -> list[EmailContact]:
    """Find contacts by name.

    Args:
        query: Name query.

    Returns:
        Matching contacts.
    """
    matches = [contact for contact in environment.inbox.contact_list if query.lower() in contact.name.lower()]
    if not matches:
        raise ValueError(f"Contact with name '{query}' not found.")
    return matches


def search_contacts_by_email(environment: WorkspaceEnvironment, query: str) -> list[EmailContact]:
    """Find contacts by email.

    Args:
        query: Email query.

    Returns:
        Matching contacts.
    """
    matches = [contact for contact in environment.inbox.contact_list if query.lower() in contact.email.lower()]
    if not matches:
        raise ValueError(f"Contact with email '{query}' not found.")
    return matches


def get_day_calendar_events(environment: WorkspaceEnvironment, day: str) -> list[CalendarEvent]:
    """Return appointments for the given day.

    Args:
        day: Day in YYYY-MM-DD format.

    Returns:
        Events on that day.
    """
    date = dt.datetime.strptime(day, "%Y-%m-%d").date()
    return [event for event in environment.calendar.events.values() if event.start_time.date() == date]


def create_calendar_event(
    environment: WorkspaceEnvironment,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    participants: list[str] | None = None,
    location: str | None = None,
) -> CalendarEvent:
    """Create a calendar event and send an invitation email.

    Args:
        title: The event title.
        start_time: Start time in YYYY-MM-DD HH:MM format.
        end_time: End time in YYYY-MM-DD HH:MM format.
        description: Event description.
        participants: Participant email addresses.
        location: Optional event location.

    Returns:
        The created calendar event.
    """
    participants = [] if participants is None else list(participants)
    participants.append(environment.calendar.account_email)
    unique_participants = list(set(participants))
    event = CalendarEvent(
        id_=environment.calendar.next_id(),
        title=title,
        description=description,
        start_time=parse_datetime(start_time),
        end_time=parse_datetime(end_time),
        location=location,
        participants=unique_participants,
    )
    environment.calendar.events[event.id_] = event
    _send_email(environment.inbox, unique_participants, f"Invitation: {title}", description, [event])
    return event


def search_calendar_events(environment: WorkspaceEnvironment, query: str, date: str | None = None) -> list[CalendarEvent]:
    """Search calendar events by title or description.

    Args:
        query: Query string.
        date: Optional date in YYYY-MM-DD format.

    Returns:
        Matching events.
    """
    events = environment.calendar.events.values()
    if date is not None:
        parsed = dt.datetime.strptime(date, "%Y-%m-%d").date()
        events = [event for event in events if event.start_time.date() == parsed]
    matches = [event for event in events if query.lower() in event.title.lower() or query.lower() in event.description.lower()]
    if not matches:
        raise ValueError("No events found. Try with a different query.")
    return matches


def get_current_day(environment: WorkspaceEnvironment) -> str:
    """Return the current day in ISO format."""
    return environment.calendar.current_day.isoformat()


def cancel_calendar_event(environment: WorkspaceEnvironment, event_id: str) -> str:
    """Cancel a calendar event and notify participants.

    Args:
        event_id: The event ID.

    Returns:
        A confirmation message.
    """
    if event_id not in environment.calendar.events:
        raise ValueError(f"Event with ID '{event_id}' not found.")
    event = environment.calendar.events[event_id]
    event.status = EventStatus.canceled
    _send_email(environment.inbox, event.participants, f"Canceled: '{event.title}'", "The event has been canceled.", [event])
    return f"Event with ID {event_id} has been canceled and participants have been notified."


def reschedule_calendar_event(
    environment: WorkspaceEnvironment,
    event_id: str,
    new_start_time: str,
    new_end_time: str | None = None,
) -> CalendarEvent:
    """Reschedule an event and notify participants.

    Args:
        event_id: The event ID.
        new_start_time: New start time in YYYY-MM-DD HH:MM format.
        new_end_time: Optional new end time in YYYY-MM-DD HH:MM format.

    Returns:
        The updated event.
    """
    if event_id not in environment.calendar.events:
        raise ValueError(f"Event with ID '{event_id}' not found.")
    event = environment.calendar.events[event_id]
    old_start = event.start_time
    event.start_time = parse_datetime(new_start_time)
    event.end_time = parse_datetime(new_end_time) if new_end_time is not None else event.start_time + (event.end_time - old_start)
    start_date = event.start_time.date().isoformat()
    start_clock = event.start_time.time().isoformat()
    end_date = event.end_time.date().isoformat()
    end_clock = event.end_time.time().isoformat()
    body = f"The event has been rescheduled. It will start on  {start_date} at {start_clock} and end on {end_date} at {end_clock}."
    _send_email(environment.inbox, event.participants, "Rescheduled: '{event.title}'", body, [event])
    return event


def add_calendar_event_participants(environment: WorkspaceEnvironment, event_id: str, participants: list[str]) -> CalendarEvent:
    """Add participants to a calendar event.

    Args:
        event_id: The event ID.
        participants: Participant email addresses to add.

    Returns:
        The updated event.
    """
    if event_id not in environment.calendar.events:
        raise ValueError(f"Event with ID '{event_id}' not found.")
    event = environment.calendar.events[event_id]
    event.participants.extend(participants)
    return event


def search_files_by_filename(environment: WorkspaceEnvironment, filename: str) -> list[CloudDriveFile]:
    """Get files by filename substring.

    Args:
        filename: Filename query.

    Returns:
        Matching files.
    """
    return [file for file in environment.cloud_drive.files.values() if filename.lower() in file.filename.lower()]


def create_file(environment: WorkspaceEnvironment, filename: str, content: str) -> CloudDriveFile:
    """Create a new cloud drive file.

    Args:
        filename: File name.
        content: File content.

    Returns:
        Created file.
    """
    file = CloudDriveFile(
        id_=environment.cloud_drive.next_id(),
        filename=filename,
        content=content,
        owner=environment.cloud_drive.account_email,
        last_modified=dt.datetime.now(),
    )
    environment.cloud_drive.files[file.id_] = file
    return file


def delete_file(environment: WorkspaceEnvironment, file_id: str) -> CloudDriveFile:
    """Delete a cloud drive file.

    Args:
        file_id: File ID.

    Returns:
        Deleted file.
    """
    if file_id not in environment.cloud_drive.files:
        raise ValueError(f"File with ID '{file_id}' not found.")
    return environment.cloud_drive.files.pop(file_id)


def get_file_by_id(environment: WorkspaceEnvironment, file_id: str) -> CloudDriveFile:
    """Get a cloud drive file by ID.

    Args:
        file_id: File ID.

    Returns:
        Matching file.
    """
    if file_id not in environment.cloud_drive.files:
        raise ValueError(f"File with ID '{file_id}' not found.")
    return environment.cloud_drive.files[file_id]


def list_files(environment: WorkspaceEnvironment) -> list[CloudDriveFile]:
    """Return all cloud drive files."""
    return list(environment.cloud_drive.files.values())


def share_file(environment: WorkspaceEnvironment, file_id: str, email: str, permission: SharingPermission | str) -> CloudDriveFile:
    """Share a file with a user.

    Args:
        file_id: File ID.
        email: Email address to share with.
        permission: Permission level, either r or rw.

    Returns:
        Updated file.
    """
    file = get_file_by_id(environment, file_id)
    file.shared_with[email] = permission
    return file


def append_to_file(environment: WorkspaceEnvironment, file_id: str, content: str) -> CloudDriveFile:
    """Append content to a cloud drive file.

    Args:
        file_id: File ID.
        content: Content to append.

    Returns:
        Updated file.
    """
    file = get_file_by_id(environment, file_id)
    file.content += content
    file.size = len(file.content)
    file.last_modified = dt.datetime.now()
    return file


def search_files(environment: WorkspaceEnvironment, query: str) -> list[CloudDriveFile]:
    """Search files by content.

    Args:
        query: Query string.

    Returns:
        Matching files.
    """
    matches = [file for file in environment.cloud_drive.files.values() if query.lower() in file.content.lower()]
    if not matches:
        raise ValueError(f"No files found with the given query ('{query}'). Try a different search term.")
    return matches


TOOLS = [
    send_email,
    delete_email,
    get_unread_emails,
    get_sent_emails,
    get_received_emails,
    get_draft_emails,
    search_emails,
    search_contacts_by_name,
    search_contacts_by_email,
    get_current_day,
    search_calendar_events,
    get_day_calendar_events,
    create_calendar_event,
    cancel_calendar_event,
    reschedule_calendar_event,
    add_calendar_event_participants,
    append_to_file,
    search_files_by_filename,
    create_file,
    delete_file,
    get_file_by_id,
    list_files,
    share_file,
    search_files,
]
