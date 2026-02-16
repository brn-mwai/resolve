#!/usr/bin/env python3
"""
Resolve - Live Incident Trigger
Injects a real-time incident into Elasticsearch for demo purposes.

Usage:
    python trigger_incident.py --mode realtime   # Live demo (injects with real delays)
    python trigger_incident.py --mode batch       # Testing (injects all at once)
    python trigger_incident.py --recover          # Inject recovery data after agent acts
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_env():
    """Load .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("ERROR: .env file not found. Copy .env.example to .env and configure.")
        sys.exit(1)
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def es_request(url: str, api_key: str, data: dict | list | None = None, method: str = "POST"):
    """Make an Elasticsearch API request."""
    body = None
    if data is not None:
        if isinstance(data, list):
            # Bulk format: list of strings
            body = "\n".join(data) + "\n"
        else:
            body = json.dumps(data)

    req = urllib.request.Request(
        url,
        data=body.encode("utf-8") if body else None,
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/x-ndjson" if isinstance(data, list) else "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        return None


def bulk_index(es_url: str, api_key: str, index: str, docs: list[dict]):
    """Bulk index documents."""
    lines = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": index}}))
        lines.append(json.dumps(doc))
    return es_request(f"{es_url}/_bulk", api_key, lines)


def now_ts(offset_seconds: float = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# Incident Data Generators
# ---------------------------------------------------------------------------

def gen_baseline_metrics(t_offset: float = 0) -> list[dict]:
    """Generate healthy baseline metrics for all services."""
    docs = []
    for service, hosts in [
        ("order-service", ["order-svc-01", "order-svc-02"]),
        ("payment-service", ["payment-svc-01", "payment-svc-02"]),
        ("notification-service", ["notif-svc-01", "notif-svc-02"]),
        ("user-service", ["user-svc-01", "user-svc-02"]),
        ("api-gateway", ["api-gw-01", "api-gw-02"]),
    ]:
        for host in hosts:
            docs.append({
                "@timestamp": now_ts(t_offset),
                "service": service,
                "host": host,
                "cpu_percent": round(random.uniform(20, 40), 1),
                "memory_percent": round(random.uniform(40, 55), 1),
                "request_latency_ms": round(random.uniform(50, 150), 1),
                "error_rate": round(random.uniform(0.001, 0.005), 4),
                "requests_per_second": round(random.uniform(200, 500), 1),
                "active_connections": random.randint(80, 200),
            })
    return docs


def gen_bad_deployment(t_offset: float = 0) -> list[dict]:
    """Generate the bad deployment record."""
    return [{
        "@timestamp": now_ts(t_offset),
        "service": "order-service",
        "version": "2.4.1",
        "deployer": "bob.kumar",
        "status": "success",
        "commit_hash": "a3f7c21",
        "changes": "Updated database connection pool configuration and added new order validation logic. Changed max pool size from 50 to 5 for testing - FORGOT TO REVERT.",
    }]


def gen_error_logs(phase: str, t_offset: float = 0) -> list[dict]:
    """Generate error logs for different incident phases."""
    docs = []
    ts = now_ts(t_offset)

    if phase == "early":
        messages = [
            ("error", "Connection pool exhausted: max 5 connections reached, 23 waiting", "DB_POOL_EXHAUSTED"),
            ("error", "Failed to acquire database connection after 30000ms timeout", "DB_CONN_TIMEOUT"),
            ("warn", "Database connection pool utilization at 100%", None),
        ]
        for level, msg, code in messages:
            doc = {"@timestamp": ts, "level": level, "service": "order-service",
                   "message": msg, "host": random.choice(["order-svc-01", "order-svc-02"]),
                   "trace_id": f"trace-{random.randint(1000,9999)}", "request_path": "/api/orders",
                   "response_time_ms": random.randint(5000, 30000)}
            if code:
                doc["error_code"] = code
            docs.append(doc)

    elif phase == "peak":
        order_errors = [
            ("critical", "Database connection pool depleted - all requests failing", "DB_POOL_CRITICAL"),
            ("error", "Connection pool exhausted: max 5 connections reached, 47 waiting", "DB_POOL_EXHAUSTED"),
            ("critical", "Circuit breaker OPEN for database connections - 95% failure rate", "CIRCUIT_OPEN"),
            ("error", "Transaction rollback: could not persist order to database", "TX_ROLLBACK"),
            ("error", "Health check failed: database connection pool at 100% utilization", "HEALTH_CHECK_FAIL"),
        ]
        payment_errors = [
            ("error", "Timeout waiting for order-service response after 30000ms", "UPSTREAM_TIMEOUT"),
            ("error", "Circuit breaker OPEN for order-service - consecutive failures: 15", "CIRCUIT_OPEN"),
        ]
        notif_errors = [
            ("error", "Failed to fetch order details for notification: connection refused", "UPSTREAM_ERROR"),
            ("warn", "Notification queue backing up: 450 pending, order-service unreachable", "QUEUE_BACKLOG"),
        ]
        gateway_errors = [
            ("error", "502 Bad Gateway: order-service returned no response", "BAD_GATEWAY"),
            ("warn", "Elevated error rate on /api/v1/orders: 43% of requests failing", "HIGH_ERROR_RATE"),
        ]

        for level, msg, code in order_errors:
            for host in ["order-svc-01", "order-svc-02", "order-svc-03"]:
                doc = {"@timestamp": now_ts(t_offset + random.uniform(0, 10)),
                       "level": level, "service": "order-service", "message": msg,
                       "host": host, "trace_id": f"trace-{random.randint(1000,9999)}",
                       "request_path": "/api/orders", "response_time_ms": random.randint(10000, 30000)}
                if code:
                    doc["error_code"] = code
                docs.append(doc)

        for level, msg, code in payment_errors:
            doc = {"@timestamp": now_ts(t_offset + random.uniform(5, 15)),
                   "level": level, "service": "payment-service", "message": msg,
                   "host": "payment-svc-01", "trace_id": f"trace-{random.randint(1000,9999)}",
                   "request_path": "/api/payments", "response_time_ms": random.randint(15000, 30000)}
            if code:
                doc["error_code"] = code
            docs.append(doc)

        for level, msg, code in notif_errors:
            doc = {"@timestamp": now_ts(t_offset + random.uniform(8, 18)),
                   "level": level, "service": "notification-service", "message": msg,
                   "host": "notif-svc-01", "trace_id": f"trace-{random.randint(1000,9999)}",
                   "request_path": "/api/notify/email", "response_time_ms": random.randint(5000, 15000)}
            if code:
                doc["error_code"] = code
            docs.append(doc)

        for level, msg, code in gateway_errors:
            doc = {"@timestamp": now_ts(t_offset + random.uniform(3, 12)),
                   "level": level, "service": "api-gateway", "message": msg,
                   "host": "api-gw-01", "trace_id": f"trace-{random.randint(1000,9999)}",
                   "request_path": "/api/v1/orders", "response_time_ms": random.randint(10000, 60000)}
            if code:
                doc["error_code"] = code
            docs.append(doc)

    return docs


def gen_incident_metrics(t_offset: float = 0) -> list[dict]:
    """Generate degraded metrics during incident."""
    docs = []
    ts = now_ts(t_offset)
    configs = [
        ("order-service", ["order-svc-01", "order-svc-02"], 85, 72, 2400, 0.45, 150, 350),
        ("payment-service", ["payment-svc-01"], 55, 58, 1200, 0.22, 250, 200),
        ("notification-service", ["notif-svc-01"], 45, 52, 800, 0.18, 180, 160),
        ("api-gateway", ["api-gw-01", "api-gw-02"], 55, 52, 450, 0.12, 600, 550),
        ("user-service", ["user-svc-01"], 26, 46, 85, 0.002, 380, 155),
    ]
    for service, hosts, cpu, mem, lat, err, rps, conns in configs:
        for host in hosts:
            docs.append({
                "@timestamp": ts, "service": service, "host": host,
                "cpu_percent": round(cpu + random.uniform(-3, 3), 1),
                "memory_percent": round(mem + random.uniform(-2, 2), 1),
                "request_latency_ms": round(lat + random.uniform(-100, 100), 1),
                "error_rate": round(err + random.uniform(-0.02, 0.02), 4),
                "requests_per_second": round(rps + random.uniform(-20, 20), 1),
                "active_connections": int(conns + random.uniform(-20, 20)),
            })
    return docs


def gen_alert(t_offset: float = 0) -> list[dict]:
    """Generate the critical alert."""
    return [{
        "@timestamp": now_ts(t_offset),
        "alert_id": "ALT-CRITICAL-LIVE-001",
        "severity": "critical",
        "service": "order-service",
        "condition": "error_rate > 0.30 for 5 minutes",
        "message": "CRITICAL: order-service error rate has exceeded 30% for the last 5 minutes. Current error rate: 45%. Cascading failures detected in payment-service and notification-service.",
        "status": "firing",
        "threshold_value": 0.30,
        "actual_value": 0.45,
    }]


def gen_recovery_metrics(t_offset: float = 0) -> list[dict]:
    """Generate recovering metrics."""
    docs = []
    ts = now_ts(t_offset)
    for service, hosts in [
        ("order-service", ["order-svc-01", "order-svc-02"]),
        ("payment-service", ["payment-svc-01", "payment-svc-02"]),
        ("notification-service", ["notif-svc-01", "notif-svc-02"]),
        ("user-service", ["user-svc-01", "user-svc-02"]),
        ("api-gateway", ["api-gw-01", "api-gw-02"]),
    ]:
        for host in hosts:
            docs.append({
                "@timestamp": ts, "service": service, "host": host,
                "cpu_percent": round(random.uniform(25, 40), 1),
                "memory_percent": round(random.uniform(42, 55), 1),
                "request_latency_ms": round(random.uniform(60, 180), 1),
                "error_rate": round(random.uniform(0.001, 0.008), 4),
                "requests_per_second": round(random.uniform(250, 500), 1),
                "active_connections": random.randint(100, 200),
            })
    return docs


def gen_rollback_deployment(t_offset: float = 0) -> list[dict]:
    """Generate rollback deployment record."""
    return [{
        "@timestamp": now_ts(t_offset),
        "service": "order-service",
        "version": "2.3.9",
        "deployer": "alice.chen",
        "status": "rollback",
        "commit_hash": "b8e4d12",
        "changes": "Emergency rollback to v2.3.9 due to database connection pool exhaustion in v2.4.1",
        "rollback_of": "2.4.1",
    }]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"


def log(color: str, label: str, message: str):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"  {color}[{t}] {label}{C_RESET} {message}")


def main():
    parser = argparse.ArgumentParser(description="Resolve - Live Incident Trigger")
    parser.add_argument("--mode", choices=["realtime", "batch"], default="realtime",
                        help="realtime: inject with delays for demo. batch: inject all at once for testing.")
    parser.add_argument("--recover", action="store_true",
                        help="Inject recovery data (run after agent suggests rollback)")
    args = parser.parse_args()

    env = load_env()
    es_url = env.get("ES_URL", "")
    api_key = env.get("API_KEY", "")

    if not es_url or not api_key:
        print("ERROR: ES_URL and API_KEY must be set in .env")
        sys.exit(1)

    random.seed()

    if args.recover:
        print(f"\n{C_BOLD}{C_GREEN}=== Resolve: Injecting Recovery Data ==={C_RESET}\n")

        log(C_GREEN, "ROLLBACK", "Deploying order-service v2.3.9 (rollback)")
        bulk_index(es_url, api_key, "resolve-deployments", gen_rollback_deployment())

        log(C_GREEN, "RECOVER", "Injecting recovering metrics...")
        for i in range(3):
            time.sleep(2)
            bulk_index(es_url, api_key, "resolve-metrics", gen_recovery_metrics(i * 60))
            log(C_GREEN, "METRICS", f"Recovery metrics batch {i+1}/3")

        log(C_GREEN, "RESOLVE", "Injecting recovery logs...")
        recovery_logs = [
            {"@timestamp": now_ts(), "level": "info", "service": "order-service",
             "message": "Service restarted with version 2.3.9 - connection pool restored to maxSize=50",
             "host": "order-svc-01", "trace_id": "trace-recovery", "request_path": "/healthz",
             "response_time_ms": 12},
            {"@timestamp": now_ts(5), "level": "info", "service": "order-service",
             "message": "Health check passed - database connections nominal",
             "host": "order-svc-01", "trace_id": "trace-recovery", "request_path": "/healthz",
             "response_time_ms": 8},
            {"@timestamp": now_ts(10), "level": "info", "service": "payment-service",
             "message": "Circuit breaker CLOSED for order-service - connectivity restored",
             "host": "payment-svc-01", "trace_id": "trace-recovery", "request_path": "/healthz",
             "response_time_ms": 45},
        ]
        bulk_index(es_url, api_key, "resolve-logs", recovery_logs)

        print(f"\n{C_BOLD}{C_GREEN}Recovery data injected. Services returning to normal.{C_RESET}\n")
        return

    # --- Incident injection ---
    delay = (lambda s: time.sleep(s)) if args.mode == "realtime" else (lambda s: None)

    print(f"\n{C_BOLD}{C_RED}=== Resolve: Live Incident Trigger ({args.mode} mode) ==={C_RESET}\n")

    # Phase 1: Baseline
    log(C_GREEN, "BASELINE", "Injecting healthy baseline metrics...")
    for i in range(3):
        bulk_index(es_url, api_key, "resolve-metrics", gen_baseline_metrics(-180 + i * 60))
    log(C_GREEN, "BASELINE", "All services healthy")
    delay(3)

    # Phase 2: Bad deployment
    log(C_YELLOW, "DEPLOY", "order-service v2.4.1 deployed by bob.kumar")
    log(C_YELLOW, "DEPLOY", "Changes: 'Updated DB connection pool config... max pool size from 50 to 5'")
    bulk_index(es_url, api_key, "resolve-deployments", gen_bad_deployment())
    delay(5)

    # Phase 3: First errors
    log(C_RED, "ERRORS", "First database connection errors appearing...")
    bulk_index(es_url, api_key, "resolve-logs", gen_error_logs("early"))
    delay(5)

    # Phase 4: Metrics degradation
    log(C_RED, "METRICS", "Error rate spiking on order-service...")
    bulk_index(es_url, api_key, "resolve-metrics", gen_incident_metrics())
    delay(5)

    # Phase 5: Full cascade + more error logs
    log(C_RED, "CASCADE", "Cascading failures in payment-service and notification-service!")
    bulk_index(es_url, api_key, "resolve-logs", gen_error_logs("peak"))
    delay(5)

    # Phase 6: Alert fires
    log(C_RED, "ALERT", "CRITICAL: order-service error rate > 30% for 5 minutes")
    log(C_RED, "ALERT", "Cascading failures detected in payment-service and notification-service")
    bulk_index(es_url, api_key, "resolve-alerts", gen_alert())

    print(f"\n{C_BOLD}{C_CYAN}{'='*60}")
    print(f"  INCIDENT INJECTED - Start the Resolve agent now!")
    print(f"  ")
    print(f"  Prompt: 'Critical alert on order-service. Error rates")
    print(f"  are spiking and cascading to other services. Investigate.'")
    print(f"  ")
    print(f"  After the agent recommends a rollback, run:")
    print(f"  python demo/trigger_incident.py --recover")
    print(f"{'='*60}{C_RESET}\n")


if __name__ == "__main__":
    main()
