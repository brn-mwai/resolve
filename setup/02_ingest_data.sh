#!/usr/bin/env bash
# Resolve - Bulk ingest synthetic data into Elasticsearch
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

SAMPLE_DIR="$ROOT_DIR/data/sample"

FILES=(
    "logs.ndjson"
    "metrics.ndjson"
    "deployments.ndjson"
    "runbooks.ndjson"
    "alerts.ndjson"
)

echo "=== Resolve: Ingesting Data ==="
echo "Elasticsearch: $ES_URL"
echo ""

for file in "${FILES[@]}"; do
    filepath="$SAMPLE_DIR/$file"
    if [ ! -f "$filepath" ]; then
        echo "SKIP: $file (not found). Run 'python data/generate.py' first."
        continue
    fi

    doc_count=$(grep -c '"index"' "$filepath" || true)
    echo -n "Ingesting $file ($doc_count docs)... "

    # Split into chunks of 500 docs (1000 lines = 500 action+doc pairs)
    total_lines=$(wc -l < "$filepath")
    chunk_size=1000
    offset=0
    errors=0

    while [ $offset -lt $total_lines ]; do
        chunk=$(tail -n +$((offset + 1)) "$filepath" | head -n $chunk_size)

        response=$(echo "$chunk" | curl -s -w "\n%{http_code}" -X POST "$ES_URL/_bulk" \
            -H "Authorization: ApiKey $API_KEY" \
            -H "Content-Type: application/x-ndjson" \
            --data-binary @- 2>&1)

        http_code=$(echo "$response" | tail -1)
        body=$(echo "$response" | head -n -1)

        if [ "$http_code" != "200" ]; then
            errors=$((errors + 1))
        elif echo "$body" | grep -q '"errors":true'; then
            errors=$((errors + 1))
        fi

        offset=$((offset + chunk_size))
    done

    if [ $errors -eq 0 ]; then
        echo "OK"
    else
        echo "WARN ($errors chunk errors)"
    fi
done

echo ""
echo "Verifying document counts:"
curl -s "$ES_URL/_cat/indices/resolve-*?v&h=index,docs.count,store.size" \
    -H "Authorization: ApiKey $API_KEY" 2>/dev/null || echo "(verification failed)"
echo ""
echo "Done."
