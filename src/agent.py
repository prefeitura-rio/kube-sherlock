from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from .settings import settings

provider = GoogleProvider(vertexai=True)

mcp_k8s_go = MCPServerStdio("mcp-k8s-go", args=["--readonly"], timeout=settings.MCP_TIMEOUT)

kube_sherlock = Agent(
    FallbackModel(
        GoogleModel(settings.MODEL, provider=provider),
        GoogleModel(settings.MODEL_FALLBACK, provider=provider),
    ),
    instructions=Path("prompts/instructions.md").read_text(),
    toolsets=[mcp_k8s_go],
)
