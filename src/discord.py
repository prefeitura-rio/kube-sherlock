from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.abc import Messageable, MessageableChannel

from .logger import logger
from .utils import split_content

DISCORD_CHAR_LIMIT = 2000


class MessageState(Enum):
    INCOMING_MESSAGE = "incoming_message"
    CHANNEL_MESSAGE = "channel_message"
    DM_MESSAGE_NOT_IN_WHITELIST = "dm_message_not_in_whitelist"
    NO_WHITELIST = "no_whitelist"
    VALID_DM_MESSAGE = "valid_dm_message"


@dataclass
class MessageStateMachine:
    current_state = MessageState.INCOMING_MESSAGE

    def process_message(self, message: discord.Message, whitelisted_users: set[str]) -> MessageState:
        logger.debug("Processing message from %s in %s", message.author.name, type(message.channel).__name__)

        match message.channel:
            case discord.DMChannel():
                if not whitelisted_users:
                    self.current_state = MessageState.NO_WHITELIST

                    logger.debug(
                        "State transition: %s -> %s (no whitelist)",
                        MessageState.INCOMING_MESSAGE,
                        self.current_state,
                    )

                    return self.current_state

                if message.author.name not in whitelisted_users:
                    self.current_state = MessageState.DM_MESSAGE_NOT_IN_WHITELIST

                    logger.debug(
                        "State transition: %s -> %s (user not in whitelist)",
                        MessageState.INCOMING_MESSAGE,
                        self.current_state,
                    )

                    return self.current_state

                self.current_state = MessageState.VALID_DM_MESSAGE
                logger.debug("State transition: %s -> %s (valid DM)", MessageState.INCOMING_MESSAGE, self.current_state)
                return self.current_state
            case _:
                self.current_state = MessageState.CHANNEL_MESSAGE

                logger.debug(
                    "State transition: %s -> %s (channel message)",
                    MessageState.INCOMING_MESSAGE,
                    self.current_state,
                )

                return self.current_state


async def send_long_message(channel: "Messageable", content: str, max_length: int = DISCORD_CHAR_LIMIT):
    """Send a long message in chunks to avoid Discord's character limit."""
    chunks = split_content(content, max_length)

    for i, chunk in enumerate(chunks):
        logger.debug("Sending chunk %d/%d: %d chars", i + 1, len(chunks), len(chunk))
        await channel.send(chunk)


async def handle_sherlock_message(channel: "MessageableChannel", response: str):
    """Handle a !sherlock command message with pre-generated response"""
    if len(response) < DISCORD_CHAR_LIMIT:
        logger.info("Sending single message (under limit)")
        await channel.send(response)
        return

    logger.info("Sending as multiple chunks (over limit)")
    await send_long_message(channel, response)


def create_discord_client() -> discord.Client:
    """Create and configure Discord client with event handlers"""
    intents = discord.Intents.default()
    intents.message_content = True

    return discord.Client(intents=intents)
