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

echo "🔍 Processing service account files..."
for file in /app/sa/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .json)

        if [[ $filename =~ ^(.+)_(.+)_(.+)$ ]]; then
            project="${BASH_REMATCH[1]}"
            cluster="${BASH_REMATCH[2]}"
            zone="${BASH_REMATCH[3]}"

            echo "🔑 Activating service account for project: $project, cluster: $cluster, zone: $zone"

            gcloud auth activate-service-account --key-file="$file"
            gcloud container clusters get-credentials "$cluster" --zone "$zone" --project "$project"

            echo "✅ Successfully configured access to $cluster in project $project"
        else
            echo "⚠️ Warning: filename $filename does not match expected pattern project_cluster_zone"

            gcloud auth activate-service-account --key-file="$file"
        fi
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
