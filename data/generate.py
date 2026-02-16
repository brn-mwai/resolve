#!/usr/bin/env python3
"""
Resolve - Synthetic Data Generator
Generates realistic microservices observability data with a built-in incident scenario.

Scenario: order-service v2.4.1 deployed with a database connection pool misconfiguration,
causing cascading failures across payment-service and notification-service.

Usage:
    python generate.py                    # Generate all data
    python generate.py --output ../data/sample  # Custom output directory
"""

import argparse
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVICES = [
    "order-service",
    "payment-service",
    "notification-service",
    "user-service",
    "api-gateway",
]

HOSTS = {
    "order-service": ["order-svc-01", "order-svc-02", "order-svc-03"],
    "payment-service": ["payment-svc-01", "payment-svc-02"],
    "notification-service": ["notif-svc-01", "notif-svc-02"],
    "user-service": ["user-svc-01", "user-svc-02"],
    "api-gateway": ["api-gw-01", "api-gw-02"],
}

REQUEST_PATHS = {
    "order-service": ["/api/orders", "/api/orders/{id}", "/api/orders/{id}/status", "/api/orders/bulk", "/healthz"],
    "payment-service": ["/api/payments", "/api/payments/{id}", "/api/payments/refund", "/api/payments/verify", "/healthz"],
    "notification-service": ["/api/notify/email", "/api/notify/sms", "/api/notify/push", "/api/notify/batch", "/healthz"],
    "user-service": ["/api/users", "/api/users/{id}", "/api/users/auth", "/api/users/profile", "/healthz"],
    "api-gateway": ["/api/v1/orders", "/api/v1/payments", "/api/v1/users", "/api/v1/notifications", "/healthz"],
}

# Timeline: 2 hours of data
# T+0 to T+58: Normal operation
# T+58: Bad deployment
# T+60: Errors start
# T+66: Error rate peaks, cascading begins
# T+70: Alert fires
# T+80: Rollback deployed
# T+85: Recovery begins
# T+90: Fully resolved
# T+90 to T+120: Normal operation resumed

TOTAL_MINUTES = 120
INCIDENT_START_MIN = 60
INCIDENT_PEAK_MIN = 66
ALERT_FIRE_MIN = 70
ROLLBACK_MIN = 80
RECOVERY_MIN = 85
RESOLVED_MIN = 90

DEPLOYERS = ["alice.chen", "bob.kumar", "carol.okonkwo", "david.miller", "eve.nakamura"]


def ts(base: datetime, offset_minutes: float) -> str:
    """Return ISO timestamp string offset from base."""
    dt = base + timedelta(minutes=offset_minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def jitter(value: float, pct: float = 0.1) -> float:
    """Add random jitter to a value."""
    return value * (1 + random.uniform(-pct, pct))


# ---------------------------------------------------------------------------
# Log Generation
# ---------------------------------------------------------------------------

NORMAL_LOG_MESSAGES = {
    "order-service": [
        ("info", "Order created successfully", None),
        ("info", "Order status updated to processing", None),
        ("info", "Inventory check passed for order {trace_id}", None),
        ("info", "Payment authorization received", None),
        ("warn", "Slow database query detected: 450ms", None),
        ("info", "Order fulfillment initiated", None),
    ],
    "payment-service": [
        ("info", "Payment processed successfully", None),
        ("info", "Payment verification complete", None),
        ("info", "Refund initiated for transaction {trace_id}", None),
        ("info", "Card tokenization successful", None),
        ("warn", "Payment retry attempt 1 of 3", None),
    ],
    "notification-service": [
        ("info", "Email notification sent to customer", None),
        ("info", "SMS notification queued", None),
        ("info", "Push notification delivered", None),
        ("info", "Batch notification job completed: 150 sent", None),
    ],
    "user-service": [
        ("info", "User authentication successful", None),
        ("info", "User profile updated", None),
        ("info", "Password reset token generated", None),
        ("info", "Session refreshed for user {trace_id}", None),
    ],
    "api-gateway": [
        ("info", "Request routed to order-service", None),
        ("info", "Request routed to payment-service", None),
        ("info", "Rate limit check passed", None),
        ("info", "JWT token validated", None),
        ("warn", "Request approaching rate limit: 85% of quota", None),
    ],
}

INCIDENT_ERROR_MESSAGES_ORDER = [
    ("error", "Connection pool exhausted: max 5 connections reached, 23 waiting", "DB_POOL_EXHAUSTED"),
    ("error", "Failed to acquire database connection after 30000ms timeout", "DB_CONN_TIMEOUT"),
    ("critical", "Database connection pool depleted - all requests failing", "DB_POOL_CRITICAL"),
    ("error", "SQLException: Cannot acquire connection from pool - pool exhausted", "DB_POOL_EXHAUSTED"),
    ("error", "Order creation failed: database connection timeout after 30s", "DB_CONN_TIMEOUT"),
    ("error", "Transaction rollback: could not persist order to database", "TX_ROLLBACK"),
    ("critical", "Circuit breaker OPEN for database connections - 95% failure rate", "CIRCUIT_OPEN"),
    ("error", "Health check failed: database connection pool at 100% utilization", "HEALTH_CHECK_FAIL"),
    ("error", "Connection pool stats: active=5, idle=0, waiting=31, maxWait=30000ms", "DB_POOL_EXHAUSTED"),
    ("error", "Dropping request /api/orders - no database connections available", "DB_CONN_TIMEOUT"),
]

INCIDENT_ERROR_MESSAGES_PAYMENT = [
    ("error", "Timeout waiting for order-service response after 30000ms", "UPSTREAM_TIMEOUT"),
    ("error", "Failed to verify order status: upstream service unavailable", "SERVICE_UNAVAILABLE"),
    ("error", "Payment processing failed: order validation timeout", "UPSTREAM_TIMEOUT"),
    ("warn", "Retry attempt 3/3 for order-service call failed", "RETRY_EXHAUSTED"),
    ("error", "Circuit breaker OPEN for order-service - consecutive failures: 15", "CIRCUIT_OPEN"),
]

INCIDENT_ERROR_MESSAGES_NOTIF = [
    ("error", "Failed to fetch order details for notification: connection refused", "UPSTREAM_ERROR"),
    ("error", "Notification enrichment failed: order-service returned 503", "SERVICE_UNAVAILABLE"),
    ("warn", "Notification queue backing up: 450 pending, order-service unreachable", "QUEUE_BACKLOG"),
    ("error", "Email notification skipped: missing order data from upstream", "DATA_MISSING"),
]

INCIDENT_ERROR_MESSAGES_GATEWAY = [
    ("error", "502 Bad Gateway: order-service returned no response", "BAD_GATEWAY"),
    ("warn", "Elevated error rate on /api/v1/orders: 43% of requests failing", "HIGH_ERROR_RATE"),
    ("error", "Request timeout on /api/v1/orders after 60s", "GATEWAY_TIMEOUT"),
]


def generate_logs(base_time: datetime) -> list[dict]:
    """Generate application log documents."""
    logs = []

    for minute in range(TOTAL_MINUTES):
        t = minute  # offset in minutes

        for service in SERVICES:
            # Determine how many logs per minute for this service
            if t < INCIDENT_START_MIN or t >= RESOLVED_MIN:
                # Normal operation: 2-5 logs per minute per service
                count = random.randint(2, 5)
                error_ratio = 0.0
            elif INCIDENT_START_MIN <= t < INCIDENT_PEAK_MIN:
                # Incident ramping up
                progress = (t - INCIDENT_START_MIN) / (INCIDENT_PEAK_MIN - INCIDENT_START_MIN)
                if service == "order-service":
                    count = random.randint(5, 15)
                    error_ratio = progress * 0.7
                elif service in ("payment-service", "notification-service"):
                    count = random.randint(3, 8)
                    error_ratio = progress * 0.3
                elif service == "api-gateway":
                    count = random.randint(3, 7)
                    error_ratio = progress * 0.2
                else:
                    count = random.randint(2, 5)
                    error_ratio = 0.0
            elif INCIDENT_PEAK_MIN <= t < ROLLBACK_MIN:
                # Peak incident
                if service == "order-service":
                    count = random.randint(15, 30)
                    error_ratio = 0.8
                elif service == "payment-service":
                    count = random.randint(8, 15)
                    error_ratio = 0.5
                elif service == "notification-service":
                    count = random.randint(6, 12)
                    error_ratio = 0.4
                elif service == "api-gateway":
                    count = random.randint(5, 10)
                    error_ratio = 0.3
                else:
                    count = random.randint(2, 5)
                    error_ratio = 0.0
            elif ROLLBACK_MIN <= t < RECOVERY_MIN:
                # Rollback deployed, still some errors
                if service == "order-service":
                    count = random.randint(8, 15)
                    error_ratio = 0.3
                elif service in ("payment-service", "notification-service"):
                    count = random.randint(4, 8)
                    error_ratio = 0.15
                else:
                    count = random.randint(2, 5)
                    error_ratio = 0.02
            else:
                # RECOVERY_MIN <= t < RESOLVED_MIN: recovering
                progress = (t - RECOVERY_MIN) / (RESOLVED_MIN - RECOVERY_MIN)
                if service == "order-service":
                    count = random.randint(3, 8)
                    error_ratio = 0.3 * (1 - progress)
                elif service in ("payment-service", "notification-service"):
                    count = random.randint(2, 5)
                    error_ratio = 0.15 * (1 - progress)
                else:
                    count = random.randint(2, 5)
                    error_ratio = 0.0

            for i in range(count):
                second_offset = random.uniform(0, 59)
                trace_id = str(uuid.uuid4())[:8]
                host = random.choice(HOSTS[service])
                path = random.choice(REQUEST_PATHS[service])

                is_error = random.random() < error_ratio

                if is_error:
                    # Pick an error message based on service
                    if service == "order-service":
                        level, message, error_code = random.choice(INCIDENT_ERROR_MESSAGES_ORDER)
                    elif service == "payment-service":
                        level, message, error_code = random.choice(INCIDENT_ERROR_MESSAGES_PAYMENT)
                    elif service == "notification-service":
                        level, message, error_code = random.choice(INCIDENT_ERROR_MESSAGES_NOTIF)
                    elif service == "api-gateway":
                        level, message, error_code = random.choice(INCIDENT_ERROR_MESSAGES_GATEWAY)
                    else:
                        continue
                    response_time = random.randint(5000, 30000) if "timeout" in message.lower() else random.randint(500, 5000)
                else:
                    level, message, error_code = random.choice(NORMAL_LOG_MESSAGES[service])
                    message = message.replace("{trace_id}", trace_id)
                    response_time = random.randint(10, 300)

                log = {
                    "@timestamp": ts(base_time, t + second_offset / 60),
                    "level": level,
                    "service": service,
                    "message": message,
                    "trace_id": f"trace-{trace_id}",
                    "host": host,
                    "request_path": path,
                    "response_time_ms": response_time,
                }
                if error_code:
                    log["error_code"] = error_code
                logs.append(log)

    return logs


# ---------------------------------------------------------------------------
# Metrics Generation
# ---------------------------------------------------------------------------

BASELINE_METRICS = {
    "order-service": {"cpu": 35, "mem": 55, "latency": 120, "error_rate": 0.002, "rps": 450, "conns": 180},
    "payment-service": {"cpu": 28, "mem": 48, "latency": 95, "error_rate": 0.001, "rps": 320, "conns": 140},
    "notification-service": {"cpu": 20, "mem": 40, "latency": 60, "error_rate": 0.001, "rps": 280, "conns": 100},
    "user-service": {"cpu": 25, "mem": 45, "latency": 80, "error_rate": 0.001, "rps": 380, "conns": 150},
    "api-gateway": {"cpu": 40, "mem": 50, "latency": 30, "error_rate": 0.001, "rps": 1200, "conns": 500},
}


def get_incident_multipliers(service: str, minute: int) -> dict:
    """Return metric multipliers based on incident timeline."""
    if minute < INCIDENT_START_MIN or minute >= RESOLVED_MIN:
        return {"cpu": 1, "mem": 1, "latency": 1, "error_rate": 1, "rps": 1, "conns": 1}

    if service == "user-service":
        return {"cpu": 1, "mem": 1, "latency": 1, "error_rate": 1, "rps": 1, "conns": 1}

    if INCIDENT_START_MIN <= minute < INCIDENT_PEAK_MIN:
        progress = (minute - INCIDENT_START_MIN) / (INCIDENT_PEAK_MIN - INCIDENT_START_MIN)
    elif INCIDENT_PEAK_MIN <= minute < ROLLBACK_MIN:
        progress = 1.0
    elif ROLLBACK_MIN <= minute < RECOVERY_MIN:
        progress = 1.0 - 0.5 * ((minute - ROLLBACK_MIN) / (RECOVERY_MIN - ROLLBACK_MIN))
    else:  # RECOVERY_MIN <= minute < RESOLVED_MIN
        progress = 0.5 * (1.0 - (minute - RECOVERY_MIN) / (RESOLVED_MIN - RECOVERY_MIN))

    if service == "order-service":
        return {
            "cpu": 1 + progress * 1.5,
            "mem": 1 + progress * 0.4,
            "latency": 1 + progress * 20,
            "error_rate": 1 + progress * 220,  # 0.002 * 220 = 0.44 peak
            "rps": 1 - progress * 0.3,
            "conns": 1 + progress * 1.5,
        }
    elif service == "payment-service":
        delayed = max(0, progress - 0.3) / 0.7 if progress > 0.3 else 0
        return {
            "cpu": 1 + delayed * 0.8,
            "mem": 1 + delayed * 0.2,
            "latency": 1 + delayed * 12,
            "error_rate": 1 + delayed * 150,
            "rps": 1 - delayed * 0.2,
            "conns": 1 + delayed * 0.8,
        }
    elif service == "notification-service":
        delayed = max(0, progress - 0.5) / 0.5 if progress > 0.5 else 0
        return {
            "cpu": 1 + delayed * 0.6,
            "mem": 1 + delayed * 0.3,
            "latency": 1 + delayed * 8,
            "error_rate": 1 + delayed * 100,
            "rps": 1 - delayed * 0.15,
            "conns": 1 + delayed * 0.6,
        }
    elif service == "api-gateway":
        return {
            "cpu": 1 + progress * 0.5,
            "mem": 1 + progress * 0.1,
            "latency": 1 + progress * 5,
            "error_rate": 1 + progress * 80,
            "rps": 1 + progress * 0.2,  # more retries = more requests
            "conns": 1 + progress * 0.4,
        }

    return {"cpu": 1, "mem": 1, "latency": 1, "error_rate": 1, "rps": 1, "conns": 1}


def generate_metrics(base_time: datetime) -> list[dict]:
    """Generate service health metric documents (one per service per minute)."""
    metrics = []

    for minute in range(TOTAL_MINUTES):
        for service in SERVICES:
            base = BASELINE_METRICS[service]
            mult = get_incident_multipliers(service, minute)

            for host in HOSTS[service]:
                error_rate = min(base["error_rate"] * mult["error_rate"], 0.95)
                cpu = min(base["cpu"] * mult["cpu"], 98)
                mem = min(base["mem"] * mult["mem"], 95)
                latency = base["latency"] * mult["latency"]
                rps = max(base["rps"] * mult["rps"] / len(HOSTS[service]), 10)
                conns = int(base["conns"] * mult["conns"] / len(HOSTS[service]))

                metrics.append({
                    "@timestamp": ts(base_time, minute),
                    "service": service,
                    "host": host,
                    "cpu_percent": round(jitter(cpu, 0.05), 1),
                    "memory_percent": round(jitter(mem, 0.03), 1),
                    "request_latency_ms": round(jitter(latency, 0.1), 1),
                    "error_rate": round(jitter(error_rate, 0.05), 4),
                    "requests_per_second": round(jitter(rps, 0.08), 1),
                    "active_connections": max(1, int(jitter(conns, 0.1))),
                })

    return metrics


# ---------------------------------------------------------------------------
# Deployment Generation
# ---------------------------------------------------------------------------

def generate_deployments(base_time: datetime) -> list[dict]:
    """Generate deployment history documents."""
    deployments = []

    # Historical normal deployments (past 2 days)
    historical = [
        (-2880, "user-service", "3.1.0", "Improved session handling and token refresh"),
        (-2160, "api-gateway", "2.8.5", "Updated rate limiting configuration"),
        (-1440, "notification-service", "1.5.2", "Added batch notification support"),
        (-720, "payment-service", "4.2.1", "PCI compliance updates for card tokenization"),
        (-360, "order-service", "2.3.9", "Performance optimization for bulk order queries"),
    ]

    for offset, service, version, changes in historical:
        deployments.append({
            "@timestamp": ts(base_time, offset),
            "service": service,
            "version": version,
            "deployer": random.choice(DEPLOYERS),
            "status": "success",
            "commit_hash": uuid.uuid4().hex[:7],
            "changes": changes,
        })

    # The bad deployment: order-service v2.4.1
    deployments.append({
        "@timestamp": ts(base_time, 58),
        "service": "order-service",
        "version": "2.4.1",
        "deployer": "bob.kumar",
        "status": "success",
        "commit_hash": "a3f7c21",
        "changes": "Updated database connection pool configuration and added new order validation logic. Changed max pool size from 50 to 5 for testing - FORGOT TO REVERT.",
    })

    # The rollback deployment
    deployments.append({
        "@timestamp": ts(base_time, ROLLBACK_MIN),
        "service": "order-service",
        "version": "2.3.9",
        "deployer": "alice.chen",
        "status": "rollback",
        "commit_hash": "b8e4d12",
        "changes": "Emergency rollback to v2.3.9 due to database connection pool exhaustion in v2.4.1",
        "rollback_of": "2.4.1",
    })

    return deployments


# ---------------------------------------------------------------------------
# Runbook Generation
# ---------------------------------------------------------------------------

def generate_runbooks() -> list[dict]:
    """Generate runbook documents for known issues."""
    return [
        {
            "title": "Database Connection Pool Exhaustion",
            "service": "order-service",
            "symptoms": "Connection pool exhausted errors, database connection timeouts, high number of waiting connections, circuit breaker open for database. Error codes: DB_POOL_EXHAUSTED, DB_CONN_TIMEOUT, CIRCUIT_OPEN.",
            "resolution_steps": "1. Verify connection pool configuration in service config (expected: maxPoolSize=50, minIdle=10, maxWait=5000ms).\n2. Check if a recent deployment changed pool settings (git log --oneline -5).\n3. If pool size was reduced: IMMEDIATE ROLLBACK to previous version.\n4. If pool size is correct: Check for connection leaks using 'SELECT * FROM pg_stat_activity' on the database.\n5. Temporary mitigation: Scale up service replicas to distribute load.\n6. Post-resolution: Verify error rates return to baseline (<0.5%) within 10 minutes.",
            "tags": ["database", "connection-pool", "order-service", "critical"],
            "content": "Database Connection Pool Exhaustion Runbook. When the order-service database connection pool is exhausted, all requests that require database access will fail. This typically manifests as DB_POOL_EXHAUSTED and DB_CONN_TIMEOUT errors. The most common cause is a misconfigured maxPoolSize parameter, often introduced during deployments. The resolution is to rollback the deployment if pool size was changed, or investigate connection leaks if the configuration is correct. Cascading failures in payment-service and notification-service are expected as they depend on order-service for order data validation.",
        },
        {
            "title": "Upstream Service Timeout Errors",
            "service": "payment-service",
            "symptoms": "Timeout errors when calling upstream services, UPSTREAM_TIMEOUT error codes, circuit breaker open for upstream dependencies, elevated retry rates.",
            "resolution_steps": "1. Identify which upstream service is timing out from error logs.\n2. Check the health of the upstream service using its /healthz endpoint.\n3. If upstream is degraded: Focus on fixing the upstream service first.\n4. Temporary mitigation: Increase timeout thresholds or enable graceful degradation mode.\n5. If upstream is healthy: Check network connectivity and DNS resolution.\n6. Monitor circuit breaker status: it should auto-close once upstream recovers.",
            "tags": ["timeout", "upstream", "payment-service", "circuit-breaker"],
            "content": "Upstream Service Timeout Runbook. When payment-service experiences timeouts calling upstream services, it is usually caused by degradation in the upstream service rather than a payment-service issue itself. First identify and resolve the upstream issue. The circuit breaker will automatically recover once the upstream service returns to health.",
        },
        {
            "title": "Notification Queue Backlog",
            "service": "notification-service",
            "symptoms": "Notification queue growing rapidly, QUEUE_BACKLOG warnings, failed notification deliveries, missing order data errors.",
            "resolution_steps": "1. Check queue depth: if >500 pending, investigate upstream dependencies.\n2. Verify order-service connectivity.\n3. If order-service is down: Enable fallback mode to send basic notifications without order enrichment.\n4. If queue is stuck: Restart notification workers.\n5. Once upstream recovers: Queue will drain automatically.\n6. Verify no notifications were permanently lost by checking dead letter queue.",
            "tags": ["queue", "notification-service", "backlog"],
            "content": "Notification Queue Backlog Runbook. The notification-service enriches notifications with data from order-service. When order-service is unavailable, the queue backs up. Enable fallback mode for basic notifications and wait for upstream recovery.",
        },
        {
            "title": "API Gateway 502 Bad Gateway Errors",
            "service": "api-gateway",
            "symptoms": "502 Bad Gateway responses, BAD_GATEWAY and GATEWAY_TIMEOUT error codes, elevated error rate on specific routes.",
            "resolution_steps": "1. Identify which backend service routes are returning 502.\n2. Check the health of the affected backend service.\n3. If backend is down: Work on restoring the backend service.\n4. Temporary mitigation: Configure fallback responses or maintenance pages.\n5. Monitor retry storms: Disable automatic retries if they are amplifying the problem.\n6. Once backend recovers, 502 errors will resolve automatically.",
            "tags": ["gateway", "502", "api-gateway", "routing"],
            "content": "API Gateway 502 Errors Runbook. 502 errors from the gateway indicate that a backend service is not responding. This is a symptom, not a root cause. Focus on identifying and fixing the backend service issue.",
        },
        {
            "title": "High CPU Utilization Alert",
            "service": "order-service",
            "symptoms": "CPU usage above 80%, degraded response times, potential thread starvation, increased garbage collection pauses.",
            "resolution_steps": "1. Check if high CPU correlates with traffic spike (check requests_per_second).\n2. If traffic is normal: Look for runaway queries or infinite loops in recent deployments.\n3. Take a thread dump to identify hot threads.\n4. Temporary mitigation: Scale horizontally by adding more replicas.\n5. If caused by specific query: Add database indexes or optimize the query.\n6. Monitor: CPU should return to <50% within 15 minutes of mitigation.",
            "tags": ["cpu", "performance", "order-service"],
            "content": "High CPU Utilization Runbook. High CPU in order-service can be caused by traffic spikes, inefficient queries, or code regressions. First check if the CPU spike correlates with a recent deployment or traffic increase.",
        },
        {
            "title": "Memory Leak Detection and Response",
            "service": "user-service",
            "symptoms": "Steadily increasing memory usage over time, OutOfMemoryError exceptions, increasing garbage collection frequency and duration.",
            "resolution_steps": "1. Check memory trends: Is usage growing linearly over hours/days?\n2. If sudden spike: Likely caused by a specific request pattern or data load.\n3. Take heap dump for analysis: kubectl exec -it pod -- jmap -dump:format=b,file=/tmp/heap.bin <pid>\n4. Temporary mitigation: Rolling restart of affected pods.\n5. Long-term: Identify leak source from heap dump and fix in code.\n6. Add memory alerts at 80% and 90% thresholds.",
            "tags": ["memory", "leak", "user-service"],
            "content": "Memory Leak Runbook. Memory leaks manifest as steadily increasing memory usage. Take a heap dump for analysis and perform rolling restarts as temporary mitigation.",
        },
        {
            "title": "SSL Certificate Expiry",
            "service": "api-gateway",
            "symptoms": "SSL handshake failures, certificate expiry warnings in logs, HTTPS connections failing.",
            "resolution_steps": "1. Check certificate expiry: openssl s_client -connect host:443 | openssl x509 -noout -dates\n2. If expired: Renew certificate immediately via cert-manager or manual process.\n3. If expiring soon: Schedule renewal during maintenance window.\n4. Update monitoring to alert 30 days before expiry.\n5. Verify renewal by checking HTTPS connectivity from external endpoint.",
            "tags": ["ssl", "certificate", "api-gateway", "security"],
            "content": "SSL Certificate Expiry Runbook. SSL certificates must be renewed before expiry. Use cert-manager for automatic renewal. If expired, renew immediately and verify HTTPS connectivity.",
        },
        {
            "title": "Database Replica Lag",
            "service": "order-service",
            "symptoms": "Stale reads from read replicas, replication lag metrics increasing, inconsistent query results between primary and replicas.",
            "resolution_steps": "1. Check replication lag: SELECT pg_last_wal_replay_lsn() on replica.\n2. If lag >10s: Check replica CPU and I/O utilization.\n3. If replica overloaded: Reduce read traffic or add more replicas.\n4. If network issue: Check connectivity between primary and replica.\n5. Temporary mitigation: Route all reads to primary (increases primary load).\n6. Monitor: Lag should return to <1s within 30 minutes.",
            "tags": ["database", "replication", "order-service", "lag"],
            "content": "Database Replica Lag Runbook. Replication lag causes stale reads. Check replica resource utilization and network connectivity. Temporarily route reads to primary if needed.",
        },
        {
            "title": "Rate Limiting Threshold Breach",
            "service": "api-gateway",
            "symptoms": "429 Too Many Requests responses increasing, rate limit warnings in logs, specific clients or IPs hitting limits.",
            "resolution_steps": "1. Identify which clients/IPs are hitting rate limits.\n2. Check if this is legitimate traffic growth or an attack.\n3. If legitimate: Increase rate limit thresholds for affected clients.\n4. If attack: Enable IP blocking and notify security team.\n5. Monitor: Verify 429 responses decrease after adjustment.\n6. Consider implementing per-client rate limit tiers.",
            "tags": ["rate-limit", "api-gateway", "traffic"],
            "content": "Rate Limiting Runbook. Rate limit breaches can be caused by legitimate traffic growth or attacks. Identify the source and adjust limits or block malicious traffic accordingly.",
        },
        {
            "title": "Service Deployment Rollback Procedure",
            "service": "order-service",
            "symptoms": "Any service degradation that correlates with a recent deployment. Elevated error rates, latency spikes, or feature regressions following a deploy.",
            "resolution_steps": "1. Confirm the issue correlates with a recent deployment (check deployment timestamps vs error spike).\n2. Decision: If error rate >10% or P99 latency >5x baseline, proceed with rollback.\n3. Execute rollback: kubectl rollout undo deployment/<service-name> -n production\n4. Or redeploy previous version: helm upgrade <service> --set image.tag=<previous-version>\n5. Monitor for 10 minutes: Error rates should drop within 5 minutes.\n6. If rollback successful: Create post-mortem ticket and investigate root cause.\n7. If rollback doesn't help: The issue may not be deployment-related, investigate other causes.",
            "tags": ["rollback", "deployment", "procedure", "order-service"],
            "content": "Service Deployment Rollback Runbook. When a deployment causes service degradation, rollback to the previous version. Verify the issue correlates with deployment timing, then execute rollback and monitor recovery. Create a post-mortem ticket for investigation.",
        },
    ]


# ---------------------------------------------------------------------------
# Alert Generation
# ---------------------------------------------------------------------------

def generate_alerts(base_time: datetime) -> list[dict]:
    """Generate alert documents."""
    alerts = []

    # Historical resolved alerts (normal operations)
    historical_alerts = [
        (-1440, "medium", "user-service", "Memory usage above 75% threshold", 0.75, 0.78, "resolved"),
        (-720, "low", "api-gateway", "Request latency P99 above 500ms", 500, 520, "resolved"),
        (-360, "low", "notification-service", "Queue depth above 200", 200, 215, "resolved"),
    ]

    for offset, severity, service, message, threshold, actual, status in historical_alerts:
        alerts.append({
            "@timestamp": ts(base_time, offset),
            "alert_id": f"ALT-{uuid.uuid4().hex[:8]}",
            "severity": severity,
            "service": service,
            "condition": f"{message.split(' above ')[0]} above threshold",
            "message": message,
            "status": status,
            "threshold_value": threshold,
            "actual_value": actual,
        })

    # The critical incident alert
    alerts.append({
        "@timestamp": ts(base_time, ALERT_FIRE_MIN),
        "alert_id": "ALT-CRITICAL-001",
        "severity": "critical",
        "service": "order-service",
        "condition": "error_rate > 0.30 for 5 minutes",
        "message": "CRITICAL: order-service error rate has exceeded 30% for the last 5 minutes. Current error rate: 45%. Cascading failures detected in payment-service and notification-service.",
        "status": "firing",
        "threshold_value": 0.30,
        "actual_value": 0.45,
    })

    # Cascading alert for payment-service
    alerts.append({
        "@timestamp": ts(base_time, ALERT_FIRE_MIN + 2),
        "alert_id": "ALT-HIGH-002",
        "severity": "high",
        "service": "payment-service",
        "condition": "error_rate > 0.15 for 3 minutes",
        "message": "HIGH: payment-service error rate at 22%. Upstream dependency (order-service) is degraded.",
        "status": "firing",
        "threshold_value": 0.15,
        "actual_value": 0.22,
    })

    return alerts


# ---------------------------------------------------------------------------
# NDJSON Writer
# ---------------------------------------------------------------------------

def write_ndjson(docs: list[dict], filepath: str, index_name: str):
    """Write documents as NDJSON (newline-delimited JSON) for Elasticsearch bulk API."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for doc in docs:
            action = json.dumps({"index": {"_index": index_name}})
            data = json.dumps(doc, ensure_ascii=False)
            f.write(f"{action}\n{data}\n")
    print(f"  Written {len(docs):,} docs to {filepath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for Resolve")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "sample"),
                        help="Output directory for NDJSON files")
    parser.add_argument("--base-time", default=None,
                        help="Base time in ISO format (default: 2 hours ago)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    if args.base_time:
        base_time = datetime.fromisoformat(args.base_time).replace(tzinfo=timezone.utc)
    else:
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)

    print(f"Resolve - Synthetic Data Generator")
    print(f"Base time: {base_time.isoformat()}")
    print(f"Output: {args.output}")
    print(f"Seed: {args.seed}")
    print()

    print("Generating logs...")
    logs = generate_logs(base_time)
    write_ndjson(logs, os.path.join(args.output, "logs.ndjson"), "resolve-logs")

    print("Generating metrics...")
    metrics = generate_metrics(base_time)
    write_ndjson(metrics, os.path.join(args.output, "metrics.ndjson"), "resolve-metrics")

    print("Generating deployments...")
    deployments = generate_deployments(base_time)
    write_ndjson(deployments, os.path.join(args.output, "deployments.ndjson"), "resolve-deployments")

    print("Generating runbooks...")
    runbooks = generate_runbooks()
    write_ndjson(runbooks, os.path.join(args.output, "runbooks.ndjson"), "resolve-runbooks")

    print("Generating alerts...")
    alerts = generate_alerts(base_time)
    write_ndjson(alerts, os.path.join(args.output, "alerts.ndjson"), "resolve-alerts")

    total = len(logs) + len(metrics) + len(deployments) + len(runbooks) + len(alerts)
    print(f"\nTotal: {total:,} documents generated")
    print(f"  Logs:        {len(logs):,}")
    print(f"  Metrics:     {len(metrics):,}")
    print(f"  Deployments: {len(deployments)}")
    print(f"  Runbooks:    {len(runbooks)}")
    print(f"  Alerts:      {len(alerts)}")
    print(f"\nIncident timeline:")
    print(f"  Baseline:    {base_time.isoformat()} to {ts(base_time, INCIDENT_START_MIN)}")
    print(f"  Bad deploy:  {ts(base_time, 58)}")
    print(f"  Errors start:{ts(base_time, INCIDENT_START_MIN)}")
    print(f"  Peak:        {ts(base_time, INCIDENT_PEAK_MIN)}")
    print(f"  Alert fires: {ts(base_time, ALERT_FIRE_MIN)}")
    print(f"  Rollback:    {ts(base_time, ROLLBACK_MIN)}")
    print(f"  Resolved:    {ts(base_time, RESOLVED_MIN)}")


if __name__ == "__main__":
    main()
