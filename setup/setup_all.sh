#!/usr/bin/env bash
# Resolve - One-Click Setup
# Runs all setup steps in sequence
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║     Resolve - Incident Resolution Agent   ║"
echo "║            One-Click Setup                ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v curl &> /dev/null; then
    echo "ERROR: curl is required. Install it and try again."
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python 3 is required for data generation."
    exit 1
fi

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "ERROR: .env file not found."
    echo "  cp .env.example .env"
    echo "  Then fill in your Elastic credentials."
    exit 1
fi

echo "Prerequisites OK"
echo ""

# Step 1: Generate synthetic data
echo "━━━ Step 1/5: Generating synthetic data ━━━"
if [ -f "$ROOT_DIR/data/sample/logs.ndjson" ]; then
    echo "Data files already exist. Skipping generation."
    echo "(Delete data/sample/*.ndjson to regenerate)"
else
    cd "$ROOT_DIR"
    $PYTHON data/generate.py
fi
echo ""

# Step 2: Create indices
echo "━━━ Step 2/5: Creating Elasticsearch indices ━━━"
bash "$SCRIPT_DIR/01_create_indices.sh"
echo ""

# Step 3: Ingest data
echo "━━━ Step 3/5: Ingesting data ━━━"
bash "$SCRIPT_DIR/02_ingest_data.sh"
echo ""

# Step 4: Create tools
echo "━━━ Step 4/5: Creating Agent Builder tools ━━━"
bash "$SCRIPT_DIR/03_create_tools.sh"
echo ""

# Step 5: Create agent
echo "━━━ Step 5/5: Creating Resolve agent ━━━"
bash "$SCRIPT_DIR/05_create_agent.sh"
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║          Setup Complete!                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Open Kibana and select the 'Resolve' agent"
echo "  2. Try: 'There is a critical alert on order-service. Error rates are spiking. Investigate.'"
echo "  3. Watch the agent investigate using the 6-step protocol"
echo ""
echo "For a live demo, run:"
echo "  python demo/trigger_incident.py --mode realtime"
