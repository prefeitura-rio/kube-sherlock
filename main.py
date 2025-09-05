import asyncio
import sys

import mlflow
import uvloop
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from mlflow import langchain

import discord
from src.agent import SupervisorWorkerSystem
from src.constants import MessageState, constants
from src.discord import MessageStateMachine, handle_sherlock_message
from src.healthcheck import run_http_server
from src.logger import logger
from src.mcp import get_mcp_client
from src.settings import settings

mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
langchain.autolog()


class SherlockBot(discord.Client):
    def __init__(self, intents: discord.Intents, checkpointer: AsyncRedisSaver):
        super().__init__(intents=intents)

        self.client = get_mcp_client()
        self.checkpointer = checkpointer
        self.supervisor_system: SupervisorWorkerSystem | None = None
        self.tools: list[BaseTool] | None = None
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
        if question == constants.RESET_COMMAND:
            try:
                await self.delete_memory(thread_id)
                await message.channel.send(constants.RESET_SUCCESS_MESSAGE)
            except Exception as e:
                await message.channel.send(constants.RESET_ERROR_MESSAGE.format(error=e))
            return True
        return False

    async def handle_human_commands(self, message: discord.Message, question: str, thread_id: str) -> bool:
        """Handle human assistance responses. Returns True if command was processed."""
        try:
            if not self.supervisor_system or not self.supervisor_system.workflow:
                return False

            config = RunnableConfig(configurable={"thread_id": thread_id})
            state = await self.supervisor_system.workflow.aget_state(config)

            if state.next and len(state.next) > 0:
                command = Command(resume={"data": question})

                response_events = self.supervisor_system.workflow.astream(command, config, stream_mode="values")

                final_response = None

                async for event in response_events:
                    if "final_response" in event:
                        final_response = event["final_response"]

                if final_response:
                    await handle_sherlock_message(message.channel, final_response)
                else:
                    await message.channel.send("Processo concluído.")

                return True

        except Exception as e:
            logger.error(f"Error handling human command: {e}")

        return False

    async def process_llm_question(self, message: discord.Message, question: str, thread_id: str):
        """Process question through supervisor-worker system and send response"""
        if not self.supervisor_system:
            await message.channel.send(constants.AGENT_INITIALIZING_MESSAGE)
            return

        async with message.channel.typing():
            try:
                response = await self.supervisor_system.process_question(question, thread_id)
                await handle_sherlock_message(message.channel, response)
            except Exception as e:
                match e:
                    case GraphInterrupt():
                        interrupt_data = getattr(e, "value", {})
                        query = interrupt_data.get("query", "Assistência humana solicitada")
                        await message.channel.send(
                            f"🤖 Assistência humana solicitada:"
                            f"\n\n{query}\n\n"
                            f"Responda com sua orientação para continuar."
                        )
                    case _:
                        await message.channel.send(f"Erro ao processar solicitação: {e!s}")
                        logger.error(f"Error in process_llm_question: {e}")

    async def process_message(self, message: discord.Message, state: MessageState) -> str | None:
        """Process message based on its state and extract question if valid"""
        match state:
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

    async def on_ready(self):
        logger.info("%s has connected to Discord", self.user)
        logger.info("Initializing Redis and MCP agent...")

        try:
            await self.checkpointer.setup()

            self.tools = await self.client.get_tools()

            if self.supervisor_system is None:
                self.supervisor_system = SupervisorWorkerSystem(self.checkpointer, self.tools)

            logger.info("Supervisor-worker system initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize supervisor system: {e}")
            self.supervisor_system = None

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if self.supervisor_system is None:
            await message.channel.send(constants.AGENT_INITIALIZING_MESSAGE)
            return

        state = self.state.process_state(message, settings.whitelisted_users)

        question = await self.process_message(message, state)

        if not question:
            return

        thread_id = f"channel_{message.channel.id}"

        if await self.handle_reset_command(message, question, thread_id):
            return

        if await self.handle_human_commands(message, question, thread_id):
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

    intents = discord.Intents.default()
    intents.message_content = True

    async with AsyncRedisSaver.from_conn_string(settings.REDIS_URL) as checkpointer:
        bot = SherlockBot(intents, checkpointer)

        await asyncio.gather(run_http_server(), bot.start(settings.DISCORD_BOT_TOKEN))


if __name__ == "__main__":
    uvloop.run(main())
