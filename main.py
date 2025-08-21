import sys

from langgraph.checkpoint.memory import InMemorySaver

import discord
from src.agent import create_agent, get_llm_response
from src.discord import handle_sherlock_message
from src.logger import logger
from src.mcp import get_mcp_client
from src.settings import Settings


class SherlockBot(discord.Client):
    def __init__(self, settings: Settings, intents: discord.Intents):
        super().__init__(intents=intents)

        self.settings = settings
        self.client = get_mcp_client()
        self.checkpointer = InMemorySaver()
        self.agent = None
        self.tools = None

    async def on_ready(self):
        logger.info("%s has connected to Discord", self.user)
        logger.info("Initializing MCP agent...")

        self.tools = await self.client.get_tools()

        self.agent = await create_agent(self.checkpointer, self.tools)

        logger.info("Agent initialization complete.")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not message.content.startswith("!sherlock"):
            return

        if self.agent is None:
            await message.channel.send("Bot is still initializing, please wait...")
            return

        question = message.content.replace("!sherlock", "").strip()
        thread_id = f"channel_{message.channel.id}"

        response = await get_llm_response(
            agent=self.agent,
            question=question,
            thread_id=thread_id,
        )

        await handle_sherlock_message(message.channel, response)


if __name__ == "__main__":
    settings = Settings()
    logger.info("Starting Discord bot...")

    if not settings.GOOGLE_API_KEY:
        logger.error("`GOOGLE_API_KEY` is not set. Please add to the environment.")
        sys.exit(1)

    if not settings.DISCORD_BOT_TOKEN:
        logger.error("`DISCORD_BOT_TOKEN` is not set. Please add to the environment.")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    bot = SherlockBot(settings, intents)
    bot.run(settings.DISCORD_BOT_TOKEN, log_handler=None)
