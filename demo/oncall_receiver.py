#!/usr/bin/env python3
"""
Resolve - On-Call Receiver
Watches the resolve-incidents Elasticsearch index for new documents
and displays them as formatted terminal notifications.

Usage:
    python demo/oncall_receiver.py
"""

import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# ANSI Colors
# ---------------------------------------------------------------------------
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_DIM = "\033[2m"

POLL_INTERVAL = 3  # seconds


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------
def load_env() -> dict:
    """Load .env file from project root (KEY=VALUE lines)."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"{C_RED}ERROR:{C_RESET} .env file not found at {env_path}")
        print("Copy .env.example to .env and configure ES_URL and API_KEY.")
        sys.exit(1)
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


# ---------------------------------------------------------------------------
# Elasticsearch helpers
# ---------------------------------------------------------------------------
def es_request(url: str, api_key: str, data: dict | None = None, method: str = "GET") -> dict | None:
    """Make an Elasticsearch API request using urllib only."""
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )

    # Allow self-signed / cloud certs
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:300]
        print(f"{C_DIM}  ES error {e.code}: {error_body}{C_RESET}")
        return None
    except urllib.error.URLError as e:
        print(f"{C_DIM}  Connection error: {e.reason}{C_RESET}")
        return None


def fetch_all_docs(es_url: str, api_key: str, index: str) -> list[dict]:
    """Fetch all documents from an index, returning list of (id, source) tuples."""
    query = {
        "size": 100,
        "sort": [{"@timestamp": {"order": "asc", "unmapped_type": "date"}}],
        "query": {"match_all": {}},
    }
    result = es_request(f"{es_url}/{index}/_search", api_key, query, method="POST")
    if not result:
        return []
    hits = result.get("hits", {}).get("hits", [])
    return [{"_id": h["_id"], **h.get("_source", {})} for h in hits]


# ---------------------------------------------------------------------------
# Document type detection
# ---------------------------------------------------------------------------
def detect_doc_type(doc: dict) -> str:
    """Determine the document type from its fields.

    Documents may carry an explicit 'type' field, or we infer from structure:
      - oncall_notification: has 'message' but no 'title'
      - remediation_action:  has 'actions' list or 'action_type'/'details'
      - incident (default):  has 'title' and 'summary'
    """
    explicit = doc.get("type", "").lower()
    if explicit == "oncall_notification":
        return "oncall_notification"
    if explicit == "remediation_action":
        return "remediation_action"

    # Infer from structure
    if "actions" in doc or ("action_type" in doc) or ("details" in doc and "title" not in doc):
        return "remediation_action"
    if "message" in doc and "title" not in doc:
        return "oncall_notification"
    return "incident"


# ---------------------------------------------------------------------------
# Severity color
# ---------------------------------------------------------------------------
def severity_color(severity: str) -> str:
    s = severity.lower() if severity else ""
    if s == "critical":
        return C_RED
    if s == "high":
        return C_YELLOW
    if s == "medium":
        return C_YELLOW
    return C_CYAN


# ---------------------------------------------------------------------------
# Notification renderers
# ---------------------------------------------------------------------------
def wrap_text(text: str, width: int = 45, indent: int = 13) -> str:
    """Word-wrap text to fit within the notification box."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    pad = " " * indent
    return ("\n" + pad).join(lines)


def render_incident(doc: dict) -> None:
    """Render a standard incident notification."""
    sev = doc.get("severity", "unknown").upper()
    sev_c = severity_color(doc.get("severity", ""))
    service = doc.get("service", "unknown")
    title = doc.get("title", "Untitled Incident")
    summary = doc.get("summary", "No summary provided.")
    status = doc.get("status", "unknown")
    assigned = doc.get("assigned_to", "unassigned")
    timestamp = doc.get("@timestamp", "unknown")

    border = "=" * 56

    print()
    print(f"  {C_CYAN}{C_BOLD}{border}{C_RESET}")
    print(f"  {C_CYAN}{C_BOLD}  RESOLVE INCIDENT NOTIFICATION{C_RESET}")
    print(f"  {C_CYAN}{C_BOLD}{border}{C_RESET}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  SEVERITY:{C_RESET}  {sev_c}{C_BOLD}{sev}{C_RESET}")
    print(f"  {C_BOLD}{C_WHITE}  SERVICE:{C_RESET}   {service}")
    print(f"  {C_BOLD}{C_WHITE}  TITLE:{C_RESET}     {wrap_text(title, width=42, indent=15)}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  SUMMARY:{C_RESET}   {wrap_text(summary, width=42, indent=15)}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  STATUS:{C_RESET}    {C_GREEN}{status}{C_RESET}")
    print(f"  {C_BOLD}{C_WHITE}  ASSIGNED:{C_RESET}  {assigned}")
    print(f"  {C_BOLD}{C_WHITE}  TIME:{C_RESET}      {timestamp}")
    print()
    print(f"  {C_CYAN}{C_BOLD}{border}{C_RESET}")
    print()


def render_oncall(doc: dict) -> None:
    """Render an on-call notification."""
    sev = doc.get("severity", "unknown").upper()
    sev_c = severity_color(doc.get("severity", ""))
    service = doc.get("service", "unknown")
    message = doc.get("message", "No message.")
    incident_id = doc.get("incident_id", "N/A")
    timestamp = doc.get("@timestamp", "unknown")

    border = "=" * 56

    print()
    print(f"  {C_YELLOW}{C_BOLD}{border}{C_RESET}")
    print(f"  {C_YELLOW}{C_BOLD}  ON-CALL ALERT{C_RESET}")
    print(f"  {C_YELLOW}{C_BOLD}{border}{C_RESET}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  SEVERITY:{C_RESET}    {sev_c}{C_BOLD}{sev}{C_RESET}")
    print(f"  {C_BOLD}{C_WHITE}  SERVICE:{C_RESET}     {service}")
    print(f"  {C_BOLD}{C_WHITE}  INCIDENT:{C_RESET}    {incident_id}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  MESSAGE:{C_RESET}     {wrap_text(message, width=40, indent=17)}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  TIME:{C_RESET}        {timestamp}")
    print()
    print(f"  {C_YELLOW}{C_BOLD}{border}{C_RESET}")
    print()


def render_remediation(doc: dict) -> None:
    """Render a remediation action notification."""
    service = doc.get("service", "unknown")
    incident_id = doc.get("incident_id", "N/A")
    timestamp = doc.get("@timestamp", "unknown")

    # action_type / details can be top-level or nested in actions[]
    action_type = doc.get("action_type", "")
    details = doc.get("details", "")

    actions = doc.get("actions", [])
    if actions and isinstance(actions, list):
        first = actions[0] if actions else {}
        if not action_type:
            action_type = first.get("action", first.get("action_type", "unknown"))
        if not details:
            details = first.get("detail", first.get("details", "No details."))

    if not action_type:
        action_type = "unknown"
    if not details:
        details = "No details provided."

    border = "=" * 56

    print()
    print(f"  {C_GREEN}{C_BOLD}{border}{C_RESET}")
    print(f"  {C_GREEN}{C_BOLD}  REMEDIATION EXECUTED{C_RESET}")
    print(f"  {C_GREEN}{C_BOLD}{border}{C_RESET}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  ACTION:{C_RESET}     {C_GREEN}{C_BOLD}{action_type.upper()}{C_RESET}")
    print(f"  {C_BOLD}{C_WHITE}  SERVICE:{C_RESET}    {service}")
    print(f"  {C_BOLD}{C_WHITE}  INCIDENT:{C_RESET}   {incident_id}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  DETAILS:{C_RESET}    {wrap_text(details, width=40, indent=16)}")
    print()
    print(f"  {C_BOLD}{C_WHITE}  TIME:{C_RESET}       {timestamp}")
    print()
    print(f"  {C_GREEN}{C_BOLD}{border}{C_RESET}")
    print()


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------
def main() -> None:
    env = load_env()
    es_url = env.get("ES_URL", "").rstrip("/")
    api_key = env.get("API_KEY", "")

    if not es_url or not api_key:
        print(f"{C_RED}ERROR:{C_RESET} ES_URL and API_KEY must be set in .env")
        sys.exit(1)

    index = "resolve-incidents"
    seen_ids: set[str] = set()

    # Seed seen_ids with any existing documents so we only show new ones
    print(f"{C_DIM}  Connecting to Elasticsearch...{C_RESET}")
    existing = fetch_all_docs(es_url, api_key, index)
    for doc in existing:
        seen_ids.add(doc["_id"])

    if existing:
        print(f"{C_DIM}  Found {len(existing)} existing document(s) -- skipping.{C_RESET}")
    print()
    print(f"  {C_CYAN}{C_BOLD}Watching {index} for new notifications...{C_RESET}")
    print(f"  {C_DIM}Press Ctrl+C to stop.{C_RESET}")
    print()

    try:
        while True:
            docs = fetch_all_docs(es_url, api_key, index)
            for doc in docs:
                doc_id = doc["_id"]
                if doc_id in seen_ids:
                    continue

                seen_ids.add(doc_id)
                doc_type = detect_doc_type(doc)

                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  {C_DIM}[{ts}] New document: {doc_id} (type: {doc_type}){C_RESET}")

                if doc_type == "oncall_notification":
                    render_oncall(doc)
                elif doc_type == "remediation_action":
                    render_remediation(doc)
                else:
                    render_incident(doc)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n  {C_DIM}Stopped.{C_RESET}\n")


if __name__ == "__main__":
    main()
