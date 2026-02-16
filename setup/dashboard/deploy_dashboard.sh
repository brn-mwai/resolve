#!/usr/bin/env bash
# Resolve - Deploy Kibana Dashboard
# Creates data views and imports the service health dashboard
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a; source "$ROOT_DIR/.env"; set +a
else
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

if [ -z "${KIBANA_URL:-}" ] || [ -z "${API_KEY:-}" ]; then
    echo "ERROR: KIBANA_URL and API_KEY must be set in .env"
    exit 1
fi

echo "=== Resolve: Deploying Kibana Dashboard ==="
echo "Kibana: $KIBANA_URL"
echo ""

# ── Step 1: Create Data Views ──────────────────────────────────────────────────

DATA_VIEWS=(
    "resolve-logs-dv|resolve-logs|Resolve Logs"
    "resolve-metrics-dv|resolve-metrics|Resolve Metrics"
    "resolve-alerts-dv|resolve-alerts|Resolve Alerts"
    "resolve-deployments-dv|resolve-deployments|Resolve Deployments"
)

echo "── Creating Data Views ──"
for dv in "${DATA_VIEWS[@]}"; do
    IFS='|' read -r id title name <<< "$dv"
    echo -n "  $name ($title)... "

    response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/data_views/data_view" \
        -H "Authorization: ApiKey $API_KEY" \
        -H "kbn-xsrf: true" \
        -H "Content-Type: application/json" \
        -d "{\"data_view\":{\"id\":\"$id\",\"title\":\"$title\",\"timeFieldName\":\"@timestamp\",\"name\":\"$name\"}}" 2>&1)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        echo "CREATED"
    elif echo "$body" | grep -q "Duplicate"; then
        echo "EXISTS (skipping)"
    else
        echo "FAILED (HTTP $http_code)"
        echo "    $body"
    fi
done

echo ""

# ── Step 2: Import Dashboard ──────────────────────────────────────────────────

NDJSON_FILE="$SCRIPT_DIR/resolve-dashboard.ndjson"

if [ ! -f "$NDJSON_FILE" ]; then
    echo "ERROR: Dashboard file not found: $NDJSON_FILE"
    exit 1
fi

echo "── Importing Dashboard ──"
echo -n "  Resolve - Service Health Dashboard... "

response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/saved_objects/_import?overwrite=true" \
    -H "Authorization: ApiKey $API_KEY" \
    -H "kbn-xsrf: true" \
    -F file=@"$NDJSON_FILE" 2>&1)

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ] && echo "$body" | grep -q '"success":true'; then
    echo "OK"
else
    echo "FAILED (HTTP $http_code)"
    echo "    $body"
    exit 1
fi

echo ""
echo "=== Dashboard Deployed ==="
echo ""
echo "Open in Kibana:"
echo "  $KIBANA_URL/app/dashboards#/view/resolve-service-health-dashboard"
echo ""
echo "Dashboard panels:"
echo "  1. Service Error Rate Trends     (line chart  - resolve-metrics)"
echo "  2. Error Log Count by Service    (bar chart   - resolve-logs)"
echo "  3. Active Alerts by Severity     (donut chart - resolve-alerts)"
echo "  4. Deployment Timeline           (data table  - resolve-deployments)"
echo "  5. Request Latency Trends        (line chart  - resolve-metrics)"
