from langchain_mcp_adapters.client import Connection, MultiServerMCPClient


def get_mcp_client() -> MultiServerMCPClient:
    """Get the MCP server parameters for the Go implementation."""
    servers: dict[str, Connection] = {
        "kubernetes-mcp-server": {
            "command": "kubernetes-mcp-server",
            "args": ["--disable-destructive"],
            "transport": "stdio",
        },
        "shell": {
            "command": "uv",
            "args": ["run", "mcp-shell-server"],
            "transport": "stdio",
            "env": {"ALLOW_COMMANDS": "cat,grep,echo,ls,find,du,kubectl,gcloud"},
        },
    }

    return MultiServerMCPClient(servers)
