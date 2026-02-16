# Resolve

**Intelligent Incident Resolution Agent powered by Elastic Agent Builder**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Elastic](https://img.shields.io/badge/Built%20with-Elastic%20Agent%20Builder-005571)](https://www.elastic.co/docs/explore-analyze/ai-features/elastic-agent-builder)

> Resolve automates production incident investigation and resolution through a systematic 6-step protocol, reducing Mean Time To Resolution from 45 minutes to under 5 minutes.

---

## The Problem

When production systems break, engineering teams face a painful, manual process:

1. **Hunt through logs** across multiple services to find error patterns
2. **Correlate metrics** to identify when degradation started
3. **Check deployment history** to see if a code change caused the issue
4. **Search runbooks** for known resolution procedures
5. **Execute remediation** (rollback, restart, scale) and verify recovery

This manual process takes 30-60 minutes per incident. During that time, users are impacted, revenue is lost, and engineers burn out from repetitive toil.

## The Solution

Resolve is an AI-powered SRE agent that automates the entire incident lifecycle using Elastic Agent Builder. It follows a systematic 6-step investigation protocol:

```
ASSESS --> INVESTIGATE --> CORRELATE --> DIAGNOSE --> ACT --> VERIFY
```

The agent queries logs and metrics via **ES|QL**, searches resolution procedures using **semantic Index Search**, and delivers a complete incident report with root cause analysis and remediation recommendations -- all within a single conversation.

## Architecture

```
+------------------------------------------------------------+
|                   ELASTIC SERVERLESS                        |
|                                                             |
|  +---------------+   +---------------------------------+   |
|  |  DATA LAYER   |   |     RESOLVE AGENT (LLM)         |   |
|  |               |   |                                   |   |
|  | resolve-logs  |<--| 1. ASSESS    > get_service_health |   |
|  | resolve-      |<--| 2. INVESTIGATE > analyze_trends   |   |
|  |  metrics      |<--| 3. CORRELATE > check_deployments  |   |
|  | resolve-      |<--| 4. DIAGNOSE  > search_runbooks    |   |
|  |  deployments  |   | 5. ACT       > create_incident    |   |
|  | resolve-      |<--|              > notify_oncall       |   |
|  |  runbooks     |   | 6. VERIFY    > get_service_health |   |
|  | resolve-      |<--|                                   |   |
|  |  incidents    |   +---------------------------------+   |
|  | resolve-      |                                         |
|  |  alerts       |                                         |
|  +---------------+                                         |
+------------------------------------------------------------+
```

## Features Used

| Feature | Purpose |
|---------|---------|
| **ES\|QL Tools** (4) | Parameterized queries for log search, metric trend analysis, deployment correlation, and service health overview |
| **Index Search Tool** (1) | Semantic search over runbook knowledge base using ELSER to find matching resolution procedures |
| **Elastic Workflows** (3) | Automated incident creation, on-call notification via webhook, and remediation action logging |
| **Custom Agent** | Multi-step reasoning agent with a 6-step investigation protocol (ASSESS, INVESTIGATE, CORRELATE, DIAGNOSE, ACT, VERIFY) |
| **6 Data Indices** | Logs, metrics, deployments, runbooks, alerts, and incidents for full observability coverage |

## Quick Start

### Prerequisites
- [Elastic Cloud Serverless trial](https://cloud.elastic.co/registration?cta=agentbuilderhackathon) (free, 14 days)
- Python 3.10+
- curl

### Setup

```bash
# Clone the repo
git clone https://github.com/brn-mwai/resolve.git
cd resolve

# Configure credentials
cp .env.example .env
# Edit .env with your Elastic credentials (ES_URL, API_KEY, KIBANA_URL)

# Run one-click setup (generates data, creates indices, tools, and agent)
bash setup/setup_all.sh
```

### Usage

1. Open Kibana and select **Resolve** from the agent dropdown
2. Try this prompt:

> "Critical alert on order-service. Error rates are spiking and cascading to payment-service. Investigate and resolve."

3. Watch the agent investigate using the 6-step protocol

### Live Demo

```bash
# Inject a real-time incident
python demo/trigger_incident.py --mode realtime

# After the agent recommends rollback, inject recovery data
python demo/trigger_incident.py --recover
```

## Project Structure

```
resolve/
├── README.md
├── LICENSE                        (MIT)
├── .env.example                   (credential template)
├── agent/
│   ├── agent.json                 (Resolve agent definition)
│   └── tools/                     (8 tool definitions: 4 ES|QL + 1 Search + 3 Workflow)
├── data/
│   ├── generate.py                (synthetic data generator)
│   ├── requirements.txt
│   └── sample/                    (pre-generated NDJSON files)
├── setup/
│   ├── mappings/                  (Elasticsearch index mappings)
│   ├── 01_create_indices.sh
│   ├── 02_ingest_data.sh
│   ├── 03_create_tools.sh
│   ├── 04_create_workflows.sh
│   ├── 05_create_agent.sh
│   └── setup_all.sh              (one-click setup)
└── demo/
    ├── trigger_incident.py        (live incident injection)
    └── scenario.md                (demo script)
```

## The Incident Scenario

Resolve ships with a realistic cascading failure scenario:

| Time | Event |
|------|-------|
| T+0 | `order-service` v2.4.1 deployed with DB pool misconfigured (50 -> 5) |
| T+2min | Database connection timeout errors appear |
| T+6min | Error rate spikes to 45%, cascading to payment-service |
| T+8min | notification-service starts failing |
| T+10min | Alert fires: "order-service error rate > 30%" |
| T+10min | **Resolve agent takes over** |
| T+12min | Agent identifies root cause, recommends rollback |
| T+15min | After rollback, all services recover |

## What We Liked

- **ES|QL in agent tools** -- Being able to write parameterized analytics queries that the agent fills in at runtime is powerful. The agent can do time-bucketed analysis, aggregations, and correlations without us writing a backend.
- **Index Search with semantic matching** -- The runbook search tool finds relevant procedures from natural language symptom descriptions. No custom ML pipeline needed.
- **Multi-step tool chaining** -- The agent autonomously chains 6+ tool calls in a single reasoning phase, each building on the previous step's findings.

## Challenges

- **Prompt engineering for reliable tool selection** -- Getting the agent to consistently follow the 6-step protocol required careful instruction design with explicit tool names at each step.
- **Synthetic data quality** -- The agent's ability to find correlations depends entirely on the data having clear, realistic patterns. We iterated multiple times on the data generator to ensure deployment timestamps aligned with metric spikes.

## Impact

| Metric | Before (Manual) | After (Resolve) |
|--------|-----------------|------------------|
| Mean Time To Resolution | 45 minutes | < 5 minutes |
| Steps to diagnose | 8-12 manual steps | 6 automated steps |
| Services correlated | 1-2 (human limit) | All 5 simultaneously |
| Runbook search time | 5-10 minutes | < 10 seconds |

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Built for the [Elasticsearch Agent Builder Hackathon](https://elasticsearch.devpost.com) by [Brian Mwai](https://github.com/brn-mwai).
