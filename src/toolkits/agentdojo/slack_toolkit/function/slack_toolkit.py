from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.toolkits.agentdojo.common import Message, SlackState, WebState


@dataclass
class SlackEnvironment:
    slack: SlackState
    web: WebState

    def snapshot(self) -> dict[str, Any]:
        return {"slack": self.slack.snapshot(), "web": self.web.snapshot()}


def _standardize_url(url: str) -> str:
    if url.startswith("https://"):
        url = url[8:]
    if url.startswith("http://"):
        url = url[7:]
    return url


def get_channels(environment: SlackEnvironment) -> list[str]:
    """Get the list of channels in Slack.

    Returns:
        Channel names.
    """
    return environment.slack.channels


def add_user_to_channel(environment: SlackEnvironment, user: str, channel: str) -> None:
    """Add a user to a channel.

    Args:
        user: User to add.
        channel: Channel to add the user to.

    Raises:
        ValueError: If user or channel is unknown.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    environment.slack.user_channels.setdefault(user, []).append(channel)


def read_channel_messages(environment: SlackEnvironment, channel: str) -> list[Message]:
    """Read messages from a channel.

    Args:
        channel: Channel to read from.

    Returns:
        Messages in the channel.
    """
    if channel not in environment.slack.channels:
        raise ValueError("Channel does not exist!")
    return environment.slack.channel_inbox.get(channel, [])


def read_inbox(environment: SlackEnvironment, user: str) -> list[Message]:
    """Read messages from a user inbox.

    Args:
        user: User whose inbox should be read.

    Returns:
        User inbox messages.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    return environment.slack.user_inbox.get(user, [])


def send_direct_message(environment: SlackEnvironment, recipient: str, body: str) -> None:
    """Send a direct message from bot to a recipient.

    Args:
        recipient: Recipient user.
        body: Message body.
    """
    if recipient not in environment.slack.users:
        raise ValueError(f"Recipient {recipient} not found in the users list")
    message = Message(sender="bot", recipient=recipient, body=body)
    environment.slack.user_inbox.setdefault(recipient, []).append(message)


def send_channel_message(environment: SlackEnvironment, channel: str, body: str) -> None:
    """Send a channel message from bot.

    Args:
        channel: Channel to send to.
        body: Message body.
    """
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    message = Message(sender="bot", recipient=channel, body=body)
    environment.slack.channel_inbox.setdefault(channel, []).append(message)


def get_users_in_channel(environment: SlackEnvironment, channel: str) -> list[str]:
    """Get users in a channel.

    Args:
        channel: Channel to inspect.

    Returns:
        Users that belong to the channel.
    """
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    return [user for user, channels in environment.slack.user_channels.items() if channel in channels]


def invite_user_to_slack(environment: SlackEnvironment, user: str, user_email: str) -> None:
    """Invite a user to the Slack workspace.

    Args:
        user: User name to invite.
        user_email: Email where the invite is sent.
    """
    if user in environment.slack.users:
        raise ValueError(f"User {user} already in the users list")
    environment.slack.users.append(user)
    environment.slack.user_inbox[user] = []
    environment.slack.user_channels[user] = []


def remove_user_from_slack(environment: SlackEnvironment, user: str) -> None:
    """Remove a user from the Slack workspace.

    Args:
        user: User to remove.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    environment.slack.users.remove(user)
    del environment.slack.user_inbox[user]
    del environment.slack.user_channels[user]


def get_webpage(environment: SlackEnvironment, url: str) -> str | None:
    """Return the content of a webpage.

    Args:
        url: URL of the webpage.

    Returns:
        Page content or 404 Not Found.
    """
    standardized = _standardize_url(url)
    environment.web.web_requests.append(standardized)
    if standardized not in environment.web.web_content:
        return "404 Not Found"
    return environment.web.web_content.get(standardized)


def post_webpage(environment: SlackEnvironment, url: str, content: str) -> None:
    """Post a webpage at a URL.

    Args:
        url: URL of the webpage.
        content: Page content.
    """
    standardized = _standardize_url(url)
    environment.web.web_requests.append(standardized)
    environment.web.web_content[standardized] = content


TOOLS = [
    get_channels,
    add_user_to_channel,
    read_channel_messages,
    read_inbox,
    send_direct_message,
    send_channel_message,
    get_users_in_channel,
    invite_user_to_slack,
    remove_user_from_slack,
    get_webpage,
    post_webpage,
]
