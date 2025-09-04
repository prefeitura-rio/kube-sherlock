from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.abc import Messageable, MessageableChannel

from .constants import MessageState, constants
from .logger import logger
from .utils import split_content


def validate_message(message: discord.Message, whitelisted_users: set[str]) -> MessageState:
    """Validate message and return appropriate state."""
    match message.channel:
        case discord.DMChannel():
            if not whitelisted_users:
                return MessageState.NO_WHITELIST

            if message.author.name not in whitelisted_users:
                return MessageState.DM_MESSAGE_NOT_IN_WHITELIST

            return MessageState.VALID_DM_MESSAGE
        case _:
            return MessageState.CHANNEL_MESSAGE


@dataclass
class MessageStateMachine:
    """Main message state machine that coordinates validation and processing."""

    current_state: MessageState = field(default_factory=lambda: MessageState.INCOMING_MESSAGE)

    def process_state(self, message: discord.Message, whitelisted_users: set[str]) -> MessageState:
        """Process message state using validation function."""
        logger.debug("Processing message from %s in %s", message.author.name, type(message.channel).__name__)

        new_state = validate_message(message, whitelisted_users)

        logger.debug("State transition: %s -> %s (%s)", MessageState.INCOMING_MESSAGE, new_state, new_state.value)

        self.current_state = new_state

        return new_state


async def send_long_message(channel: "Messageable", content: str, max_length: int = constants.DISCORD_CHAR_LIMIT):
    """Send a long message in chunks to avoid Discord's character limit."""
    chunks = split_content(content, max_length)

    for i, chunk in enumerate(chunks):
        logger.debug("Sending chunk %d/%d: %d chars", i + 1, len(chunks), len(chunk))
        await channel.send(chunk)


async def handle_sherlock_message(channel: "MessageableChannel", response: str):
    """Handle a !sherlock command message with pre-generated response"""
    safe_limit = constants.DISCORD_CHAR_LIMIT - 50

    if len(response) < safe_limit:
        logger.info("Sending single message (under limit)")

        try:
            await channel.send(response)
        except Exception as e:
            logger.warning(f"Single message failed ({len(response)} chars), splitting: {e}")
            await send_long_message(channel, response)
        return

    logger.info("Sending as multiple chunks (over limit)")
    await send_long_message(channel, response)
