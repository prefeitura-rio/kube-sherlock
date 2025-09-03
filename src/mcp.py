from langchain_mcp_adapters.client import Connection, MultiServerMCPClient

from .constants import constants
from .settings import settings


def get_mcp_client() -> MultiServerMCPClient:
    """Get the MCP server parameters for the Go implementation."""
    servers: dict[str, Connection] = {
        "kubernetes-mcp-server": {
            "command": "kubernetes-mcp-server",
            "args": ["--disable-destructive", "--kubeconfig", constants.KUBECONFIG_MCP_PATH],
            "transport": "stdio",
        },
        "shell": {
            "command": "uv",
            "args": ["run", "mcp-shell-server"],
            "transport": "stdio",
            "env": {"ALLOW_COMMANDS": settings.ALLOWED_SHELL_COMMANDS},
        },
    }

    return MultiServerMCPClient(servers)
