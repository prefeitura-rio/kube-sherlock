import asyncio
import sys
from pathlib import Path

import uvloop
from langchain_core.tools import BaseTool
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.redis.aio import AsyncRedisStore

import discord
from src.agent import create_agent, get_llm_response
from src.discord import MessageState, MessageStateMachine, handle_sherlock_message
from src.healthcheck import run_http_server
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
        self.state = MessageStateMachine()

    async def delete_memory(self, thread_id: str):
        """Delete conversation memory for a given thread_id"""
        try:
            await self.checkpointer.adelete_thread(thread_id)
            logger.info("Successfully deleted memory for thread: %s", thread_id)
        except Exception as e:
            logger.error("Failed to delete memory for thread %s: %s", thread_id, e)
            raise

    async def handle_reset_command(self, message: discord.Message, question: str, thread_id: str) -> bool:
        """Handle reset command. Returns True if reset was processed."""
        if question.startswith("reset"):
            try:
                await self.delete_memory(thread_id)
                await message.channel.send("✅ Conversa resetada! Histórico apagado.")
            except Exception as e:
                await message.channel.send(f"❌ Erro ao resetar conversa. Erro: {e}")
            return True
        return False

    async def process_llm_question(self, message: discord.Message, question: str, thread_id: str):
        """Process question through LLM and send response"""
        async with message.channel.typing():
            response = await get_llm_response(
                agent=self.agent,
                question=question,
                thread_id=thread_id,
            )

        await handle_sherlock_message(message.channel, response)

    async def process_message(self, message: discord.Message, state: MessageState) -> str | None:
        """Process message based on its state and extract question if valid"""
        match state:
            case MessageState.DM_MESSAGE_NOT_IN_WHITELIST:
                await message.channel.send("Você não está autorizado a usar este bot.")
                return None
            case MessageState.NO_WHITELIST:
                await message.channel.send("DMs não estão habilitadas para este bot.")
                return None
            case MessageState.CHANNEL_MESSAGE:
                if not message.content.startswith("!sherlock"):
                    return None
                return message.content.replace("!sherlock", "").strip()
            case MessageState.VALID_DM_MESSAGE:
                return message.content.strip()
            case _:
                return None

    async def on_ready(self):
        logger.info("%s has connected to Discord", self.user)
        logger.info("Initializing MCP agent...")

        self.tools = await self.client.get_tools()
        self.agent = await create_agent(self.store, self.checkpointer, self.tools)

        logger.info("Agent initialization complete.")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if self.agent is None:
            await message.channel.send("Bot está inicializando...")
            return

        state = self.state.process_state(message, settings.whitelisted_users)

        question = await self.process_message(message, state)

        if not question:
            await message.channel.send("Por favor, forneça uma pergunta após o comando !sherlock.")
            return

        thread_id = f"channel_{message.channel.id}"

        if await self.handle_reset_command(message, question, thread_id):
            return

        await self.process_llm_question(message, question, thread_id)


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

    for attempt in range(settings.MAX_WAIT):
        if Path(settings.KUBECONFIG_PATH).exists():
            logger.info("Kubeconfig found at %s", settings.KUBECONFIG_PATH)
            break

        if attempt == 0:
            logger.info("Waiting for kubeconfig at %s...", settings.KUBECONFIG_PATH)

        await asyncio.sleep(1)
    else:
        logger.error("Kubeconfig not found at %s after %d seconds", settings.KUBECONFIG_PATH, settings.MAX_WAIT)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    async with (
        AsyncRedisStore.from_conn_string(settings.REDIS_URL) as store,
        AsyncRedisSaver.from_conn_string(settings.REDIS_URL) as checkpointer,
    ):
        bot = SherlockBot(intents, store, checkpointer)

        await asyncio.gather(run_http_server(), bot.start(settings.DISCORD_BOT_TOKEN))


if __name__ == "__main__":
    uvloop.run(main())
