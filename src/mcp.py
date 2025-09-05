from langchain_mcp_adapters.client import Connection, MultiServerMCPClient


def get_mcp_client() -> MultiServerMCPClient:
    """Get the MCP server parameters for the Go implementation."""
    servers: dict[str, Connection] = {
        "mcp-k8s-go": {
            "command": "mcp-k8s-go",
            "args": ["--readonly"],
            "transport": "stdio",
        },
    }

    return MultiServerMCPClient(servers)
