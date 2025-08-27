#!/usr/bin/env bash

set -euo pipefail

echo "🚀 Starting entrypoint.sh - setting up kubeconfig..."

mkdir -p /root/.kube

echo "apiVersion: v1
kind: Config
clusters: []
contexts: []
users: []
current-context: \"\"" > /root/.kube/config

echo "🔑 Activating service account..."
SERVICE_ACCOUNT_FILE="${SERVICE_ACCOUNT_FILE:-/app/service-account.json}"

if [ -f "$SERVICE_ACCOUNT_FILE" ]; then
    gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_FILE"
    echo "✅ Service account activated successfully"
else
    echo "❌ Service account file not found at $SERVICE_ACCOUNT_FILE"
    exit 1
fi

echo "🔍 Processing cluster configurations from CLUSTERS env var..."
if [ "$CLUSTERS" = "" ]; then
    echo "❌ CLUSTERS environment variable is not set"
    exit 1
fi

echo "$CLUSTERS" | jq -r 'to_entries[] | "\(.key) \(.value.cluster) \(.value.region)"' | while read -r project cluster region; do
    echo "🔗 Configuring access -> cluster: $cluster, project: $project, region: $region"

    if gcloud container clusters get-credentials "$cluster" --project "$project" --region="$region"; then
        echo "✅ Successfully configured access to $cluster in project $project"
    else
        echo "❌ Failed to configure access to $cluster in project $project"
    fi
done

if [ -f "/root/.kube/config" ]; then
    echo "✅ Kubeconfig created successfully at /root/.kube/config"
    echo "📋 Configured contexts:"
    kubectl config get-contexts --no-headers -o name || echo "❌ No contexts found"
else
    echo "❌ Failed to create kubeconfig!"
    exit 1
fi

echo "🎯 Entrypoint setup complete. Starting application..."

exec "$@"
