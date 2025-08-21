from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.abc import Messageable, MessageableChannel

from .logger import logger
from .utils import split_content

DISCORD_CHAR_LIMIT = 2000


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
