#!/usr/bin/env bash
# Resolve - Create the Agent Builder agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a; source "$ROOT_DIR/.env"; set +a
else
    echo "ERROR: .env file not found."
    exit 1
fi

AGENT_FILE="$ROOT_DIR/agent/agent.json"

echo "=== Resolve: Creating Agent ==="
echo "Kibana: $KIBANA_URL"
echo ""

echo -n "Creating Resolve agent... "

response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/agent_builder/agents" \
    -H "Authorization: ApiKey $API_KEY" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d @"$AGENT_FILE" 2>&1)

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo "OK"
    echo ""
    echo "Agent created successfully!"
    echo "Open Kibana and select 'Resolve' from the agent dropdown to start chatting."
elif echo "$body" | grep -q "already exists"; then
    echo "EXISTS"
    echo ""
    echo "Agent already exists. To update, delete first then re-create:"
    echo "  curl -X DELETE '$KIBANA_URL/api/agent_builder/agents/resolve-agent' -H 'Authorization: ApiKey \$API_KEY' -H 'kbn-xsrf: true'"
else
    echo "FAILED (HTTP $http_code)"
    echo "$body" | head -c 300
    echo ""
fi

echo ""
echo "To verify: Open $KIBANA_URL and navigate to Agents > Resolve"
