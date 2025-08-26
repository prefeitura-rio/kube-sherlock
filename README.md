# Kube Sherlock

A Discord bot for debugging Kubernetes issues in Brazilian Portuguese. The bot responds to `!sherlock` commands with intelligent Kubernetes troubleshooting advice powered by Google's Gemini AI.

## Features

- Kubernetes troubleshooting assistance in Portuguese
- Per-channel conversation memory
- Powered by Google Gemini AI via LangChain

## Quick Start

### Prerequisites

- Docker and Docker Compose
- [Just](https://github.com/casey/just) command runner (optional but recommended)

### Environment Setup

1. Create environment variables:

```bash
touch .env
```

2. Configure required variables in `.env`:

```env
GOOGLE_API_KEY=your_google_api_key_here
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

### Service Account Configuration

The bot automatically authenticates with Google Cloud using service account files placed in `/app/sa/`. The service account filenames must follow the pattern:

```
project_cluster_zone.json
```

**Example:**

- `my-project-dev_web-cluster_us-east1.json`
  - Project: `my-project-dev`
  - Cluster: `web-cluster`
  - Zone: `us-east1`

The entrypoint script will:

1. Parse each service account filename to extract project, cluster, and zone information
2. Activate the service account with `gcloud auth activate-service-account`
3. Automatically connect to the corresponding Kubernetes cluster using `gcloud container clusters get-credentials`

This allows the bot to access multiple Kubernetes clusters across different projects and zones automatically.

**Note:** The entrypoint script allows only one cluster authentication per project. If multiple service account files exist for the same project, the last one processed will be the active cluster connection for that project.

### Development

Start the bot with hot reload:

```bash
just watch
```

Or using Docker Compose directly:

```bash
docker-compose -f docker-compose.debug.yaml up --watch
```

### Production

Build and run:

```bash
just up
```

## Usage

In Discord, use the `!sherlock` command followed by your Kubernetes question:

```
!sherlock Por que meu pod está em CrashLoopBackOff?
```

The bot will respond with troubleshooting advice in Portuguese, maintaining conversation context per channel.

## Development Commands

```bash
just watch      # Development server with hot reload
just up         # Build and run production
just down       # Stop containers
just test       # Run tests
just typecheck  # Type checking
```

## Architecture

- **Discord Integration**: Handles commands and message splitting
- **LangChain**: Manages AI conversation flow and memory
- **Redis Memory**: Persistent per-channel conversation history
- **Google Gemini**: AI model for generating responses

# TODO

- Add human-in-the-loop
- Allow the model to self-iterate over its messages
- Add tests
