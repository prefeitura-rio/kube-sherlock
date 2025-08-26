import sys

import uvloop
from langchain_core.tools import BaseTool
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.redis.aio import AsyncRedisStore

import discord
from src.agent import create_agent, get_llm_response
from src.discord import handle_sherlock_message
from src.logger import logger
from src.mcp import get_mcp_client
from src.settings import settings


class SherlockBot(discord.Client):
    def __init__(self, intents: discord.Intents, store: AsyncRedisStore, checkpointer: AsyncRedisSaver):
        super().__init__(intents=intents)

        self.client = get_mcp_client()
        self.store = store
        self.checkpointer = checkpointer
        self.agent: CompiledStateGraph = None
        self.tools: list[BaseTool] = None

    async def on_ready(self):
        logger.info("%s has connected to Discord", self.user)
        logger.info("Initializing MCP agent...")

        self.tools = await self.client.get_tools()

        self.agent = await create_agent(self.store, self.checkpointer, self.tools)

        logger.info("Agent initialization complete.")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if not message.content.startswith("!sherlock"):
            return

        if self.agent is None:
            await message.channel.send("Bot is still initializing, please wait...")
            return

        question = message.content.replace("!sherlock", "").strip()
        thread_id = f"channel_{message.channel.id}"

        async with message.channel.typing():
            response = await get_llm_response(
                agent=self.agent,
                question=question,
                thread_id=thread_id,
            )

        await handle_sherlock_message(message.channel, response)


async def main():
    logger.info("Starting Discord bot...")

    if not settings.GOOGLE_API_KEY:
        logger.error("`GOOGLE_API_KEY` is not set. Please add to the environment.")
        sys.exit(1)

    if not settings.DISCORD_BOT_TOKEN:
        logger.error("`DISCORD_BOT_TOKEN` is not set. Please add to the environment.")
        sys.exit(1)

    if not settings.REDIS_URL:
        logger.error("`REDIS_URL` is not set. Please add to the environment.")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    async with (
        AsyncRedisStore.from_conn_string(settings.REDIS_URL) as store,
        AsyncRedisSaver.from_conn_string(settings.REDIS_URL) as checkpointer,
    ):
        await SherlockBot(intents, store, checkpointer).start(settings.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    uvloop.run(main())
