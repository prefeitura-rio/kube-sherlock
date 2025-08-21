# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord bot for debugging Kubernetes issues, named "kube-sherlock". The bot responds to `!sherlock` commands with Kubernetes troubleshooting advice in Brazilian Portuguese. It uses Google's Gemini AI model via LangChain and maintains conversation memory per Discord channel using SQLite.

## Essential Commands

### Development
- `just watch` - Run development server with hot reload (Docker Compose with --watch)
- `just up` - Build and run the bot (Docker Compose)
- `just down` - Stop and clean up containers
- `just test` - Run pytest test suite
- `just typecheck` - Run mypy type checking

### Direct UV Commands
- `uv run pytest` - Run tests directly
- `uv run mypy .` - Type check codebase
- `uv run ruff check` - Lint code
- `uv run ruff format` - Format code

## Architecture

### Core Components

**Main Entry Point** (`main.py`):
- Minimal bootstrap that connects Discord and LangChain components
- Environment validation (GOOGLE_API_KEY, DISCORD_BOT_TOKEN required)
- Event handler registration for Discord messages

**LangChain Integration** (`src/langchain.py`):
- `LimitedSQLChatMessageHistory`: Custom SQLite-backed memory that keeps only last 50 messages per session
- `create_chat_chain()`: Factory for RunnableWithMessageHistory chain using Google Genai
- System prompt loaded from `system-prompt.txt` (Portuguese Kubernetes expert persona)

**Discord Integration** (`src/discord.py`):
- Message splitting logic for Discord's 2000 character limit
- Sequential message sending to preserve order
- Session management using `channel_{channel_id}` pattern

**Settings** (`src/settings.py`):
- Pydantic-based configuration with environment variable support
- Default model: "gemini-2.5-flash"

### Memory Architecture

The bot maintains **per-channel conversation memory**:
- Each Discord channel gets unique session ID: `f"channel_{message.channel.id}"`
- SQLite database (`memory.db`) stores conversation history
- `LimitedSQLChatMessageHistory` automatically truncates to last 50 messages per channel
- Memory persists between bot restarts

### Message Flow

1. Discord message starting with `!sherlock` triggers handler
2. Question extracted, session ID generated from channel ID
3. LangChain retrieves conversation history for that channel
4. Google Gemini processes question with history context
5. Response split into chunks if >2000 chars, sent sequentially

## Development Notes

### Environment Variables
Required:
- `GOOGLE_API_KEY` - Google AI API key for Gemini model
- `DISCORD_BOT_TOKEN` - Discord bot token

Optional:
- `LOG_LEVEL` - Defaults to "INFO"
- `MODEL_NAME` - Defaults to "gemini-2.5-flash"

### Type Checking
Uses `TYPE_CHECKING` imports to avoid Discord.py compatibility issues:
```python
if TYPE_CHECKING:
    from discord.abc import Messageable
```

### Code Quality Tools
- **Ruff**: Linting and formatting (120 char line length)
- **MyPy**: Type checking with basedpyright configuration
- **Python 3.13+**: Required minimum version

### Docker Development
The project uses Docker Compose with file watching for development. The `just watch` command provides hot reload during development.