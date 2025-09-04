# Kube Sherlock

A Discord bot for debugging Kubernetes issues in Brazilian Portuguese. The bot responds to `!sherlock` commands with intelligent Kubernetes troubleshooting advice powered by Google's Gemini AI.

## Features

- **Kubernetes Troubleshooting**: Intelligent assistance in Brazilian Portuguese
- **Hallucination Prevention**: Dual-agent verification system with real cluster data validation
- **Conversation Memory**: Per-channel context with automatic cleanup and reset capability
- **MCP Integration**: Direct kubectl and shell access via Model Context Protocol
- **Planning System**: Intelligent step-by-step execution for complex diagnostics
- **Observability**: Built-in OpenTelemetry metrics and logging
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

The bot uses a sophisticated multi-agent system to ensure accurate and verified responses:

#### Main Agent

- **Purpose**: Primary Kubernetes troubleshooting assistant
- **Memory**: Maintains conversation context via Redis checkpointer
- **Tools**: Full access to MCP kubectl tools and shell commands
- **Language**: Responds in Brazilian Portuguese

#### Reflection Agent

- **Purpose**: Unbiased verification of main agent responses
- **Memory**: No conversation memory (stateless for objectivity)
- **Tools**: Same MCP tools as main agent for verification
- **Function**: Detects hallucinations and validates cluster data

#### Hybrid Reflection System

The bot implements a unique two-stage verification process:

1. **Main Agent Response**: Generates initial response using conversation context
2. **Verification Instruction**: Main agent creates specific verification tasks
3. **Independent Verification**: Reflection agent verifies using real cluster data
4. **Response Validation**: Checks for fabricated namespaces, pods, services
5. **Final Output**: Returns verified response or corrections

```python
# Example verification flow
Main Agent: "Namespaces: default, kube-system, dev-team-a"
Reflection Agent: kubectl get namespaces  # Verifies against real cluster
Real Output: "default, kube-system, monitoring"
Result: "CORRIJA: Os namespaces reais são: default, kube-system, monitoring"
```

#### Planning System

- **Intelligent Planning**: LLM decides when to use step-by-step vs direct execution
- **Step Execution**: Complex questions broken into verification steps
- **Conversational Output**: Technical reports converted to natural language

### Data Flow

```
Discord Message → Message Validation → Agent Selection → Tool Execution → Reflection → Response
     ↓                    ↓                    ↓              ↓            ↓           ↓
User Command → Whitelist Check → Main Agent → kubectl/shell → Verification → Discord
```

### Memory Management

- **Thread Isolation**: Separate Redis threads for main and reflection processes
- **Automatic Cleanup**: Reflection threads deleted after use to prevent memory leaks
- **Context Summarization**: Long conversations automatically summarized to fit token limits

### Error Handling

- **Graceful Degradation**: System fails safely without returning hallucinated data
- **Tool Failures**: Explicit handling when kubectl or shell commands fail
- **Timeout Protection**: Configurable timeouts prevent hanging operations

## Security & Reliability

### Hallucination Prevention

The bot implements a robust verification system to prevent AI hallucinations:

- **Real Data Verification**: All cluster information verified against actual kubectl output
- **Dual-Agent Architecture**: Separate verification agent with no conversation memory
- **Fail-Safe Design**: Returns errors rather than potentially incorrect information
- **Tool Validation**: Verifies kubectl commands before execution

### Example Verification

```
User Question: "Liste os namespaces"
Main Agent: "Os namespaces são: default, kube-system, dev-team-a, prod-team-b"
Reflection Agent: [Executes kubectl get namespaces]
Real Output: "default, kube-system, monitoring, cert-manager"
Final Response: "Os namespaces reais no cluster são: default, kube-system, monitoring, cert-manager"
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

# TODO

- Add human-in-the-loop escalation
- Implement response quality metrics
- Add comprehensive integration tests
- Performance optimization for large clusters
