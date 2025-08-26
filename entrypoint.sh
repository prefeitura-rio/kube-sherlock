#!/usr/bin/env bash

set -euo pipefail

for file in /app/sa/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .json)

        if [[ $filename =~ ^(.+)_(.+)_(.+)$ ]]; then
            project="${BASH_REMATCH[1]}"
            cluster="${BASH_REMATCH[2]}"
            zone="${BASH_REMATCH[3]}"

            echo "Activating service account for project: $project, cluster: $cluster, zone: $zone"

            gcloud auth activate-service-account --key-file="$file"
            gcloud container clusters get-credentials "$cluster" --zone "$zone" --project "$project"
        else
            echo "Warning: Filename $filename does not match expected pattern project_cluster_zone"

            gcloud auth activate-service-account --key-file="$file"
        fi
    fi
done

exec "$@"
