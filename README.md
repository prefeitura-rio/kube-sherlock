# Kube Sherlock

A Discord bot for debugging Kubernetes issues in Brazilian Portuguese. The bot responds to `!sherlock` commands with intelligent Kubernetes troubleshooting advice powered by Google's Gemini AI.

## Features

- **Kubernetes Troubleshooting**: Intelligent assistance in Brazilian Portuguese
- **Supervisor-Worker Architecture**: Advanced planning and execution system with feedback loops
- **Human-in-the-Loop**: Interactive oversight for complex scenarios requiring human judgment
- **Conversation Memory**: Per-channel context with shared thread management
- **MCP Integration**: Direct kubectl and shell access via Model Context Protocol
- **Smart Planning**: Adaptive execution strategy based on task complexity
- **Type Safety**: Modern Python with enums, pattern matching, and comprehensive type checking
- **Access Control**: DM whitelist support and message validation

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
REDIS_URL=redis://localhost:6379  # For conversation memory

# opentelemetry (optional)
OTEL_SERVICE_NAME=kube-sherlock
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_TRACES_EXPORTER=none
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_INSECURE=true
```

### DM Whitelist (Optional)

The bot can be configured to accept direct messages only from whitelisted users. Configure the `WHITELIST` environment variable with comma-separated usernames:

- **No WHITELIST**: All DMs are blocked
- **With WHITELIST**: Only listed users can send DMs
- **Guild/Server channels**: Always allowed regardless of whitelist

**Example:**

```env
WHITELIST=admin,developer,support
```

This allows DMs from users named "admin", "developer", and "support" while blocking all other DM attempts.

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

### Commands

- `!sherlock <question>` - Ask a Kubernetes troubleshooting question
- `!reset` - Clear conversation memory for the current channel/DM
- **Human assistance responses** - When prompted by the system, provide guidance to continue

## Development Commands

```bash
just watch      # Development server with hot reload
just up         # Build and run production
just down       # Stop containers
just test       # Run tests
just typecheck  # Type checking
```

## Architecture

### Core Components

- **Discord Integration**: Handles commands, message validation, and response splitting
- **LangChain Agent System**: Multi-agent architecture with MCP tools for Kubernetes access
- **Redis Memory**: Persistent per-channel conversation history with automatic cleanup
- **Google Gemini**: AI model for generating responses
- **MCP Tools**: Model Context Protocol integration for kubectl and shell access

### Agent Architecture

The bot uses a sophisticated supervisor-worker system with human oversight:

#### Supervisor Agent

- **Purpose**: Strategic planning and evaluation of worker responses
- **Planning**: Creates structured task plans with kubectl commands and verification steps
- **Evaluation**: Reviews worker output for quality and completeness
- **Feedback Loop**: Refines plans based on execution results
- **Language**: Internal coordination in English for precision

#### Worker Agent

- **Purpose**: Kubernetes troubleshooting execution specialist
- **Memory**: Maintains conversation context via shared thread management
- **Tools**: Full access to MCP kubectl tools and shell commands
- **Expertise**: Comprehensive Kubernetes knowledge and diagnostic capabilities
- **Language**: Responds to users in Brazilian Portuguese

#### Human-in-the-Loop System

Interactive oversight for complex scenarios:

1. **Automatic Detection**: System identifies when human assistance is needed
2. **Context Provision**: Provides detailed context about the current situation
3. **Human Guidance**: User provides direction or approval
4. **Workflow Continuation**: Process resumes with human input integrated

```python
# Example human assistance flow
🤖 Assistência humana solicitada:

O sistema detectou uma situação complexa que requer avaliação humana.
Context: Pod em estado indefinido após múltiplas tentativas de diagnóstico.

Responda com sua orientação para continuar.
```

#### Supervisor-Worker Flow

1. **Plan Creation**: Supervisor analyzes question and creates execution plan
2. **Task Execution**: Worker agent executes plan with kubectl tools
3. **Result Evaluation**: Supervisor reviews output for quality
4. **Feedback Loop**: Refines plan if improvement needed
5. **Human Oversight**: Escalates complex cases for human review
6. **Final Response**: Delivers verified response to user

### Data Flow

```
Discord Message → Validation → Supervisor Planning → Worker Execution → Supervisor Evaluation → Response
     ↓               ↓               ↓                    ↓                  ↓              ↓
User Command → Whitelist → Create/Refine Plan → Execute with Tools → Quality Review → Discord
                                ↑                                           ↓
                            Feedback Loop ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

### Memory Management

- **Shared Thread Architecture**: Single thread per channel eliminates proliferation
- **Context Preservation**: Worker maintains conversation history for natural interaction
- **Supervisor Objectivity**: Planning and evaluation remain context-aware but unbiased
- **Automatic Cleanup**: `!reset` command clears conversation memory when needed

### Error Handling

- **Graceful Degradation**: System fails safely without returning hallucinated data
- **Tool Failures**: Explicit handling when kubectl or shell commands fail
- **Timeout Protection**: Configurable timeouts prevent hanging operations

## Security & Reliability

### Quality Assurance

The bot implements a robust quality control system:

- **Supervisor Evaluation**: All worker responses reviewed for quality and completeness
- **Feedback Loops**: Iterative refinement until responses meet quality standards
- **Human Oversight**: Complex scenarios escalated for human review and guidance
- **Real Data Integration**: Direct kubectl access ensures responses based on actual cluster state
- **Fail-Safe Design**: System gracefully handles errors without returning incorrect information

### Example Quality Control

```
User Question: "Por que meu pod está falhando?"
Supervisor Plan: "1. Check pod status, 2. Review logs, 3. Examine events"
Worker Execution: [Executes kubectl commands and analyzes output]
Supervisor Evaluation: "APROVADO - Response comprehensive and accurate"
Final Response: "Seu pod está falhando devido a erro de configuração..."
```

## Configuration

### Environment Variables

| Variable                | Required | Description                  | Default              |
| ----------------------- | -------- | ---------------------------- | -------------------- |
| `GOOGLE_API_KEY`        | Yes      | Google Gemini API key        | -                    |
| `DISCORD_BOT_TOKEN`     | Yes      | Discord bot token            | -                    |
| `REDIS_URL`             | Yes      | Redis connection string      | -                    |
| `WHITELIST`             | No       | Comma-separated DM whitelist | None (DMs disabled)  |
| `KUBECONFIG_PATH`       | No       | Path to kubeconfig file      | `/root/.kube/config` |
| `LOG_LEVEL`             | No       | Logging level                | `INFO`               |
| `AGENT_TIMEOUT`         | No       | Agent timeout in seconds     | `60`                 |
| `REFLECTION_ITERATIONS` | No       | Max reflection iterations    | `2`                  |

## Technical Implementation

### Modern Python Features

- **Type Safety**: Comprehensive type annotations with `TypedDict`, `Literal`, and custom type aliases
- **Pattern Matching**: Consistent use of `match-case` statements for clean control flow
- **Enums & Dataclasses**: Structured constants and configuration with `@dataclass(frozen=True)`
- **Async/Await**: Full async architecture for optimal Discord bot performance

### Architecture Patterns

- **LangGraph Workflows**: State-driven execution with conditional edges and checkpointing
- **MCP Integration**: Model Context Protocol for secure kubectl and shell access
- **Redis Persistence**: Reliable conversation memory with automatic cleanup
- **Error Handling**: Graceful degradation with comprehensive exception management

# TODO

- Implement response quality metrics and analytics
- Add comprehensive integration tests for supervisor-worker flows
- Performance optimization for large clusters
- Enhanced human-in-the-loop UI/UX improvements
