#!/usr/bin/env bash
# Resolve - Create Elastic Workflows
# Note: Workflows may need to be created via Kibana UI if API isn't available
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

WORKFLOWS_DIR="$ROOT_DIR/workflows"

echo "=== Resolve: Setting Up Workflows ==="
echo ""
echo "Elastic Workflows may need to be configured via the Kibana UI."
echo "The workflow YAML definitions are in: $WORKFLOWS_DIR"
echo ""
echo "Workflow files:"
for wf in "$WORKFLOWS_DIR"/*.yaml; do
    name=$(grep "^name:" "$wf" | head -1 | awk '{print $2}')
    desc=$(grep "^description:" "$wf" | head -1 | sed 's/description: "//' | sed 's/"$//')
    echo "  $name - $desc"
done
echo ""
echo "To register workflows:"
echo "  1. Open Kibana: $KIBANA_URL"
echo "  2. Navigate to Management > Stack Management > Workflows"
echo "  3. Import each YAML file from the workflows/ directory"
echo "  4. Or use the Workflows API if available on your deployment"
echo ""

# Attempt API creation (may not be available on all deployments)
echo "Attempting API registration..."
for wf in "$WORKFLOWS_DIR"/*.yaml; do
    wf_name=$(basename "$wf" .yaml)
    echo -n "  Registering $wf_name... "

    # Convert YAML to JSON for API (requires python)
    json_body=$(python3 -c "
import yaml, json, sys
with open('$wf') as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
" 2>/dev/null)

    if [ -z "$json_body" ]; then
        echo "SKIP (yaml parsing failed - install PyYAML: pip install pyyaml)"
        continue
    fi

    response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/workflows" \
        -H "Authorization: ApiKey $API_KEY" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d "$json_body" 2>&1)

    http_code=$(echo "$response" | tail -1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "OK"
    else
        echo "MANUAL SETUP NEEDED (API returned HTTP $http_code)"
    fi
done

echo ""
echo "Done. If API registration failed, use the Kibana UI to import workflows."
