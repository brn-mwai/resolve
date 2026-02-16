#!/usr/bin/env bash
# Resolve - Create Elasticsearch indices with mappings
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a; source "$ROOT_DIR/.env"; set +a
else
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

if [ -z "${ES_URL:-}" ] || [ -z "${API_KEY:-}" ]; then
    echo "ERROR: ES_URL and API_KEY must be set in .env"
    exit 1
fi

MAPPINGS_DIR="$SCRIPT_DIR/mappings"

INDICES=(
    "resolve-logs"
    "resolve-metrics"
    "resolve-deployments"
    "resolve-runbooks"
    "resolve-alerts"
    "resolve-incidents"
)

echo "=== Resolve: Creating Elasticsearch Indices ==="
echo "Elasticsearch: $ES_URL"
echo ""

for index in "${INDICES[@]}"; do
    mapping_file="$MAPPINGS_DIR/$index.json"
    if [ ! -f "$mapping_file" ]; then
        echo "SKIP: $index (mapping file not found)"
        continue
    fi

    echo -n "Creating $index... "

    response=$(curl -s -w "\n%{http_code}" -X PUT "$ES_URL/$index" \
        -H "Authorization: ApiKey $API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$mapping_file" 2>&1)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        echo "OK"
    elif echo "$body" | grep -q "resource_already_exists_exception"; then
        echo "EXISTS (skipping)"
    else
        echo "FAILED (HTTP $http_code)"
        echo "  $body"
    fi
done

echo ""
echo "Done. Verify with: curl -s '$ES_URL/_cat/indices/resolve-*?v&h=index,docs.count,store.size'"
