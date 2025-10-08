from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.abc import Messageable, MessageableChannel

from .constants import MessageState, constants
from .logger import logger
from .utils import split_content


@dataclass
class MessageStateMachine:
    """Main message state machine that coordinates validation and processing."""

    current: MessageState = field(default_factory=lambda: MessageState.INCOMING_MESSAGE)

    def validate(self, message: discord.Message, whitelisted_users: set[str]) -> MessageState:
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

    def process_state(self, message: discord.Message, whitelisted_users: set[str]) -> None:
        """Process message state using validation function."""
        logger.debug("Processing message from %s in %s", message.author.name, type(message.channel).__name__)

        self.current = self.validate(message, whitelisted_users)

        logger.debug("State transition: %s -> %s (%s)", MessageState.INCOMING_MESSAGE, self.current, self.current.value)

    async def process_message(self, message: discord.Message) -> str | None:
        """Process message based on its state and extract question if valid"""
        match self.state:
            case MessageState.DM_MESSAGE_NOT_IN_WHITELIST:
                await message.channel.send(constants.WHITELIST_DENIED_MESSAGE)
                return None
            case MessageState.NO_WHITELIST:
                await message.channel.send(constants.DM_DISABLED_MESSAGE)
                return None
            case MessageState.CHANNEL_MESSAGE:
                if not message.content.startswith(constants.SHERLOCK_COMMAND):
                    return None

                return message.content.replace(constants.SHERLOCK_COMMAND, "").strip()
            case MessageState.VALID_DM_MESSAGE:
                return message.content.strip()
            case _:
                return None


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


async def send_long_message(channel: "Messageable", content: str, max_length: int = constants.DISCORD_CHAR_LIMIT):
    """Send a long message in chunks to avoid Discord's character limit."""
    chunks = split_content(content, max_length)

    for i, chunk in enumerate(chunks):
        logger.debug("Sending chunk %d/%d: %d chars", i + 1, len(chunks), len(chunk))
        await channel.send(chunk)
