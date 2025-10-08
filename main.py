import asyncio
import sys

import mlflow
import uvloop
from mlflow import pydantic_ai

import discord
from src.agent import agent
from src.discord import MessageStateMachine, handle_sherlock_message
from src.healthcheck import run_http_server
from src.logger import logger
from src.settings import settings

mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
pydantic_ai.autolog()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
state = MessageStateMachine()


@client.event
async def on_ready():
    logger.info("%s has connected to Discord", client.user)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    state.process_state(message, settings.whitelisted_users)

    question = await state.process_message(message)

    if not question:
        return

    async with message.channel.typing():
        response = await agent.run(question)
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

    await asyncio.gather(run_http_server(), client.start(settings.DISCORD_BOT_TOKEN))


if __name__ == "__main__":
    uvloop.run(main())
