#!/usr/bin/env bash
# Resolve - Remove Kibana Dashboard and Data Views
# Use this to clean up before re-deploying
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a; source "$ROOT_DIR/.env"; set +a
else
    echo "ERROR: .env file not found."
    exit 1
fi

if [ -z "${KIBANA_URL:-}" ] || [ -z "${API_KEY:-}" ]; then
    echo "ERROR: KIBANA_URL and API_KEY must be set in .env"
    exit 1
fi

echo "=== Resolve: Removing Dashboard & Data Views ==="
echo ""

# Remove dashboard
echo -n "Removing dashboard... "
response=$(curl -s -w "\n%{http_code}" -X DELETE "$KIBANA_URL/api/saved_objects/dashboard/resolve-service-health-dashboard" \
    -H "Authorization: ApiKey $API_KEY" \
    -H "kbn-xsrf: true" 2>&1)
http_code=$(echo "$response" | tail -1)
if [ "$http_code" = "200" ]; then
    echo "OK"
else
    echo "SKIPPED (not found or HTTP $http_code)"
fi

# Remove data views
DATA_VIEW_IDS=("resolve-logs-dv" "resolve-metrics-dv" "resolve-alerts-dv" "resolve-deployments-dv")

for dv_id in "${DATA_VIEW_IDS[@]}"; do
    echo -n "Removing data view $dv_id... "
    response=$(curl -s -w "\n%{http_code}" -X DELETE "$KIBANA_URL/api/data_views/data_view/$dv_id" \
        -H "Authorization: ApiKey $API_KEY" \
        -H "kbn-xsrf: true" 2>&1)
    http_code=$(echo "$response" | tail -1)
    if [ "$http_code" = "200" ]; then
        echo "OK"
    else
        echo "SKIPPED (not found or HTTP $http_code)"
    fi
done

echo ""
echo "Teardown complete. Run deploy_dashboard.sh to re-create."
