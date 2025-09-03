import asyncio
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from .errors import AgentErrorMessages, InvalidResponseError
from .logger import logger
from .settings import settings


def split_content(content: str, max_length: int) -> list[str]:
    """
    Split text into chunks at word boundaries (assumes content > max_length)

    If no space found, split at `max_length`
    """
    split_point = content.rfind(" ", 0, max_length)
    split_point = max_length if split_point == -1 else split_point

    chunk = content[:split_point]
    remaining = content[split_point:].lstrip()

    if len(remaining) <= max_length:
        return [chunk, remaining] if remaining else [chunk]

    return [chunk, *split_content(remaining, max_length)]


async def invoke_agent(
    agent: CompiledStateGraph,
    question: str,
    thread_id: str,
    agent_timeout: int | None = None,
) -> dict[str, Any]:
    """Invoke agent with consistent configuration and error handling."""
    logger.info("Agent input - Question: %s", question)

    config = RunnableConfig(
        configurable={"thread_id": thread_id},
        recursion_limit=settings.RECURSION_LIMIT,
    )

    timeout_value = agent_timeout or settings.AGENT_TIMEOUT

    try:
        model_response = await asyncio.wait_for(
            agent.ainvoke(
                input={"messages": [{"role": "user", "content": question}]},
                config=config,
            ),
            timeout=timeout_value,
        )

        logger.info("Raw model response keys: %s", list(model_response.keys()))

        if "structured_response" not in model_response:
            logger.error("No `structured_response` in model response: %s", model_response)
            raise InvalidResponseError(AgentErrorMessages.STRUCTURED_RESPONSE_NOT_FOUND.value)

        return model_response

    except asyncio.TimeoutError:
        logger.error("Agent invocation timed out after %d seconds", timeout_value)
        raise TimeoutError(f"Agent timed out after {timeout_value} seconds") from None
    except Exception as e:
        logger.error("Error invoking agent: %s", str(e))
        raise


def extract_response_content(model_response: dict[str, Any]) -> str:
    """Extract content from structured response."""
    response = model_response["structured_response"]
    content = response.content if response else ""

    if not content or not content.strip():
        logger.warning("Response content is empty")
        return AgentErrorMessages.EMPTY_RESPONSE.value

    logger.info("Response content length: %d chars", len(content))
    logger.info("Response preview: %s ... (truncated)", content[: settings.LOG_TRUNCATE_LENGTH])

    return content
