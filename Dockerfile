FROM ghcr.io/astral-sh/uv:trixie-slim

ARG DEBUG=false

ARG MCP_VERSION=0.0.49

WORKDIR /app

RUN apt-get update && apt-get install -y apt-transport-https ca-certificates curl tar gnupg lsb-release unzip --no-install-recommends

# install Google Cloud CLI and kubectl
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install google-cloud-cli kubectl google-cloud-cli-gke-gcloud-auth-plugin -y \
    && rm -rf /var/lib/apt/lists/*

# install k8s MCP server
RUN curl -L https://github.com/containers/kubernetes-mcp-server/releases/download/v${MCP_VERSION}/kubernetes-mcp-server-linux-amd64 -o /usr/local/bin/kubernetes-mcp-server && chmod +x /usr/local/bin/kubernetes-mcp-server

COPY pyproject.toml uv.lock main.py system-prompt.txt .

COPY src src

RUN if [ "$DEBUG" = "true" ]; then uv sync --frozen --group debug; else uv sync --frozen; fi

COPY discord-certificate.crt /usr/local/share/ca-certificates/discord-certificate.crt

COPY entrypoint.sh /entrypoint.sh

RUN update-ca-certificates && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["uv", "run", "python", "main.py"]
