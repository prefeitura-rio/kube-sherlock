from langchain_mcp_adapters.client import Connection, MultiServerMCPClient

from .settings import settings


def get_mcp_client() -> MultiServerMCPClient:
    """Get the MCP server parameters for the Go implementation."""
    servers: dict[str, Connection] = {
        "kubernetes-mcp-server": {
            "command": "mcp-k8s-go",
            "args": ["--readonly"],
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
