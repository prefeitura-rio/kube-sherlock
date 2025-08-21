#!/usr/bin/env bash
set -euo pipefail

if [ -f "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
    gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
    gcloud container clusters get-credentials "$GCLOUD_CLUSTER" --zone "$GCLOUD_ZONE" --project "$GCLOUD_PROJECT"
fi

exec "$@"
