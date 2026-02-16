#!/usr/bin/env bash
# Resolve - Create Agent Builder tools via Kibana API
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

if [ -z "${KIBANA_URL:-}" ]; then
    echo "ERROR: KIBANA_URL must be set in .env"
    exit 1
fi

TOOLS_DIR="$ROOT_DIR/agent/tools"

echo "=== Resolve: Creating Agent Builder Tools ==="
echo "Kibana: $KIBANA_URL"
echo ""

for tool_file in "$TOOLS_DIR"/*.json; do
    tool_name=$(basename "$tool_file" .json)
    echo -n "Creating tool: $tool_name... "

    response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/agent_builder/tools" \
        -H "Authorization: ApiKey $API_KEY" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d @"$tool_file" 2>&1)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        echo "OK"
    elif echo "$body" | grep -q "already exists"; then
        echo "EXISTS (skipping)"
    else
        echo "FAILED (HTTP $http_code)"
        echo "  $body" | head -c 200
        echo ""
    fi
done

echo ""
echo "Listing tools:"
curl -s "$KIBANA_URL/api/agent_builder/tools" \
    -H "Authorization: ApiKey $API_KEY" \
    -H "kbn-xsrf: true" 2>/dev/null | python3 -c "
import sys, json
try:
    tools = json.load(sys.stdin)
    for t in tools:
        if t.get('id','').startswith('resolve-'):
            print(f\"  {t['id']} ({t.get('type','unknown')})\" )
except: pass
" 2>/dev/null || echo "  (Could not list tools)"
echo ""
echo "Done."
