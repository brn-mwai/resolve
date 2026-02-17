#!/usr/bin/env python3
"""
Resolve - Memory Leak Incident Trigger (Second Scenario)
Injects a user-service memory leak incident to prove the agent handles
different root causes with different investigation paths.

This scenario is DIFFERENT from the DB pool incident:
  - Different service (user-service, not order-service)
  - Different root cause (memory leak, not misconfiguration)
  - No bad deployment (leak is gradual, not deployment-correlated)
  - Different runbook matched (Memory Leak Detection, not DB Pool)
  - Different remediation (pod restart, not rollback)

Usage:
    python demo/trigger_memory_leak.py                # Inject memory leak data
    python demo/trigger_memory_leak.py --recover      # Inject recovery (after pod restart)
"""

import argparse
import json
import random
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_env():
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


def es_request(url, api_key, data=None, method="POST"):
    body = None
    if data is not None:
        if isinstance(data, list):
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


def bulk_index(es_url, api_key, index, docs):
    lines = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": index}}))
        lines.append(json.dumps(doc))
    return es_request(f"{es_url}/_bulk", api_key, lines)


def now_ts(offset_seconds=0):
    dt = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"


def log(color, label, message):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"  {color}[{t}] {label}{C_RESET} {message}")


# ---------------------------------------------------------------------------
# Memory leak data generators
# ---------------------------------------------------------------------------

def gen_healthy_baseline(t_offset=0):
    """All services healthy, user-service memory normal at ~50%."""
    docs = []
    for service, hosts, base_mem in [
        ("order-service", ["order-svc-01", "order-svc-02"], 48),
        ("payment-service", ["payment-svc-01", "payment-svc-02"], 45),
        ("notification-service", ["notif-svc-01", "notif-svc-02"], 42),
        ("user-service", ["user-svc-01", "user-svc-02"], 50),
        ("api-gateway", ["api-gw-01", "api-gw-02"], 40),
    ]:
        for host in hosts:
            docs.append({
                "@timestamp": now_ts(t_offset),
                "service": service, "host": host,
                "cpu_percent": round(random.uniform(20, 35), 1),
                "memory_percent": round(base_mem + random.uniform(-3, 3), 1),
                "request_latency_ms": round(random.uniform(50, 140), 1),
                "error_rate": round(random.uniform(0.001, 0.005), 4),
                "requests_per_second": round(random.uniform(200, 450), 1),
                "active_connections": random.randint(80, 200),
            })
    return docs


def gen_memory_climbing_metrics(phase, t_offset=0):
    """
    Memory climbs through phases:
      phase 1: 65%  (early warning)
      phase 2: 78%  (threshold breach)
      phase 3: 88%  (critical, latency degrading)
      phase 4: 94%  (near OOM, errors starting)
    Other services remain healthy.
    """
    mem_levels = {1: 65, 2: 78, 3: 88, 4: 94}
    lat_levels = {1: 180, 2: 350, 3: 1200, 4: 3500}
    err_levels = {1: 0.005, 2: 0.02, 3: 0.08, 4: 0.25}
    cpu_levels = {1: 40, 2: 55, 3: 70, 4: 85}

    mem = mem_levels[phase]
    lat = lat_levels[phase]
    err = err_levels[phase]
    cpu = cpu_levels[phase]

    docs = []
    # user-service degrading
    for host in ["user-svc-01", "user-svc-02"]:
        docs.append({
            "@timestamp": now_ts(t_offset),
            "service": "user-service", "host": host,
            "cpu_percent": round(cpu + random.uniform(-3, 3), 1),
            "memory_percent": round(mem + random.uniform(-2, 2), 1),
            "request_latency_ms": round(lat + random.uniform(-50, 100), 1),
            "error_rate": round(err + random.uniform(-0.005, 0.01), 4),
            "requests_per_second": round(random.uniform(150, 350), 1),
            "active_connections": random.randint(100, 250),
        })

    # Other services healthy
    for service, hosts in [
        ("order-service", ["order-svc-01"]),
        ("payment-service", ["payment-svc-01"]),
        ("notification-service", ["notif-svc-01"]),
        ("api-gateway", ["api-gw-01"]),
    ]:
        for host in hosts:
            docs.append({
                "@timestamp": now_ts(t_offset),
                "service": service, "host": host,
                "cpu_percent": round(random.uniform(22, 38), 1),
                "memory_percent": round(random.uniform(42, 55), 1),
                "request_latency_ms": round(random.uniform(60, 150), 1),
                "error_rate": round(random.uniform(0.001, 0.005), 4),
                "requests_per_second": round(random.uniform(200, 450), 1),
                "active_connections": random.randint(90, 180),
            })
    return docs


def gen_memory_leak_logs(phase, t_offset=0):
    """Generate logs showing memory leak symptoms."""
    docs = []
    ts = now_ts(t_offset)

    if phase == "warning":
        logs = [
            ("warn", "GC pause exceeded 200ms threshold: 340ms", None),
            ("warn", "Memory usage above 75% threshold: current 78%", "MEM_THRESHOLD"),
            ("info", "Heap utilization: 2.1GB / 2.5GB (84%)", None),
        ]
    elif phase == "critical":
        logs = [
            ("error", "OutOfMemoryError: Java heap space during request processing", "OOM_ERROR"),
            ("error", "GC overhead limit exceeded - spending >95% of time in garbage collection", "GC_OVERHEAD"),
            ("critical", "Memory at 94% - approaching OOM kill threshold", "MEM_CRITICAL"),
            ("error", "Request timeout: GC pause blocked request for 4200ms", "GC_TIMEOUT"),
            ("error", "Failed to allocate session cache entry: heap exhausted", "HEAP_EXHAUSTED"),
            ("warn", "Response time degraded: P99 at 3500ms (baseline: 120ms)", "LATENCY_DEGRADED"),
        ]
    else:
        return docs

    for level, msg, code in logs:
        for host in ["user-svc-01", "user-svc-02"]:
            doc = {
                "@timestamp": now_ts(t_offset + random.uniform(0, 8)),
                "level": level, "service": "user-service",
                "message": msg, "host": host,
                "trace_id": f"trace-mem-{random.randint(1000, 9999)}",
                "request_path": random.choice(["/api/users", "/api/users/profile", "/api/users/sessions"]),
                "response_time_ms": random.randint(500, 5000),
            }
            if code:
                doc["error_code"] = code
            docs.append(doc)
    return docs


def gen_memory_alert(t_offset=0):
    return [{
        "@timestamp": now_ts(t_offset),
        "alert_id": "ALT-MEM-LEAK-001",
        "severity": "high",
        "service": "user-service",
        "condition": "memory_percent > 0.85 for 10 minutes",
        "message": "HIGH: user-service memory usage has been above 85% for over 10 minutes and is still climbing. Current: 94%. GC overhead errors detected. Response times severely degraded.",
        "status": "firing",
        "threshold_value": 0.85,
        "actual_value": 0.94,
    }]


def gen_recovery_data(t_offset=0):
    """After pod restart, memory drops back to baseline."""
    docs = []
    for host in ["user-svc-01", "user-svc-02"]:
        docs.append({
            "@timestamp": now_ts(t_offset),
            "service": "user-service", "host": host,
            "cpu_percent": round(random.uniform(20, 30), 1),
            "memory_percent": round(random.uniform(35, 48), 1),
            "request_latency_ms": round(random.uniform(60, 130), 1),
            "error_rate": round(random.uniform(0.001, 0.005), 4),
            "requests_per_second": round(random.uniform(250, 450), 1),
            "active_connections": random.randint(90, 170),
        })
    return docs


def gen_recovery_logs(t_offset=0):
    return [
        {"@timestamp": now_ts(t_offset), "level": "info", "service": "user-service",
         "message": "Pod user-svc-01 restarted - memory reset to baseline (620MB / 2.5GB)",
         "host": "user-svc-01", "trace_id": "trace-restart-01",
         "request_path": "/healthz", "response_time_ms": 15},
        {"@timestamp": now_ts(t_offset + 3), "level": "info", "service": "user-service",
         "message": "Pod user-svc-02 restarted - memory reset to baseline (580MB / 2.5GB)",
         "host": "user-svc-02", "trace_id": "trace-restart-02",
         "request_path": "/healthz", "response_time_ms": 12},
        {"@timestamp": now_ts(t_offset + 8), "level": "info", "service": "user-service",
         "message": "Health check passed - all pods healthy. GC overhead resolved.",
         "host": "user-svc-01", "trace_id": "trace-restart-03",
         "request_path": "/healthz", "response_time_ms": 8},
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Resolve - Memory Leak Incident Trigger")
    parser.add_argument("--recover", action="store_true",
                        help="Inject recovery data (after pod restart)")
    args = parser.parse_args()

    env = load_env()
    es_url = env.get("ES_URL", "").rstrip("/")
    api_key = env.get("API_KEY", "")

    if not es_url or not api_key:
        print("ERROR: ES_URL and API_KEY must be set in .env")
        sys.exit(1)

    random.seed()

    if args.recover:
        print(f"\n{C_BOLD}{C_GREEN}=== Resolve: Memory Leak Recovery ==={C_RESET}\n")

        log(C_GREEN, "RESTART", "Rolling restart of user-service pods...")
        bulk_index(es_url, api_key, "resolve-logs", gen_recovery_logs())

        for i in range(3):
            time.sleep(2)
            bulk_index(es_url, api_key, "resolve-metrics", gen_recovery_data(i * 60))
            log(C_GREEN, "METRICS", f"Recovery metrics batch {i+1}/3")

        print(f"\n{C_BOLD}{C_GREEN}Memory leak recovery complete. Pods restarted, memory nominal.{C_RESET}\n")
        return

    # --- Inject memory leak incident ---
    print(f"\n{C_BOLD}{C_YELLOW}=== Resolve: Memory Leak Scenario ==={C_RESET}\n")
    print(f"  This scenario demonstrates a DIFFERENT incident type:")
    print(f"  - Service: user-service (not order-service)")
    print(f"  - Root cause: memory leak (not deployment misconfiguration)")
    print(f"  - No bad deployment to correlate")
    print(f"  - Runbook: Memory Leak Detection (not DB Pool)")
    print(f"  - Remediation: pod restart (not rollback)\n")

    # Phase 1: Healthy baseline (2 hours ago)
    log(C_GREEN, "BASELINE", "Injecting healthy baseline...")
    for i in range(4):
        bulk_index(es_url, api_key, "resolve-metrics", gen_healthy_baseline(-7200 + i * 600))
    log(C_GREEN, "BASELINE", "All 5 services healthy")
    time.sleep(2)

    # Phase 2: Memory starts climbing (90 min ago -> 30 min ago)
    log(C_YELLOW, "MEMORY", "user-service memory starting to climb...")
    bulk_index(es_url, api_key, "resolve-metrics", gen_memory_climbing_metrics(1, -5400))
    time.sleep(2)

    log(C_YELLOW, "MEMORY", "user-service at 78% memory - threshold breached")
    bulk_index(es_url, api_key, "resolve-metrics", gen_memory_climbing_metrics(2, -3600))
    bulk_index(es_url, api_key, "resolve-logs", gen_memory_leak_logs("warning", -3600))
    time.sleep(2)

    # Phase 3: Getting critical (15 min ago)
    log(C_RED, "MEMORY", "user-service at 88% - GC pauses increasing!")
    bulk_index(es_url, api_key, "resolve-metrics", gen_memory_climbing_metrics(3, -900))
    time.sleep(2)

    # Phase 4: Near OOM (now)
    log(C_RED, "CRITICAL", "user-service at 94% - OOM errors, latency spiking!")
    bulk_index(es_url, api_key, "resolve-metrics", gen_memory_climbing_metrics(4))
    bulk_index(es_url, api_key, "resolve-logs", gen_memory_leak_logs("critical"))
    time.sleep(1)

    # Phase 5: Alert fires
    log(C_RED, "ALERT", "HIGH: user-service memory > 85% for 10 minutes")
    bulk_index(es_url, api_key, "resolve-alerts", gen_memory_alert())

    print(f"\n{C_BOLD}{C_CYAN}{'='*60}")
    print(f"  MEMORY LEAK INCIDENT INJECTED")
    print(f"  ")
    print(f"  Prompt: 'user-service memory usage is climbing steadily")
    print(f"  and response times are degrading. GC overhead errors")
    print(f"  detected. Investigate and resolve.'")
    print(f"  ")
    print(f"  Watch: The agent should take a DIFFERENT path:")
    print(f"    - Check service health (sees user-service memory at 94%)")
    print(f"    - Search error logs (finds OOM, GC_OVERHEAD errors)")
    print(f"    - Check deployments (finds NO correlated deployment)")
    print(f"    - Search runbooks (finds Memory Leak runbook)")
    print(f"    - Recommend: Rolling restart + heap dump analysis")
    print(f"  ")
    print(f"  After agent recommends restart, run:")
    print(f"  python demo/trigger_memory_leak.py --recover")
    print(f"{'='*60}{C_RESET}\n")


if __name__ == "__main__":
    main()
