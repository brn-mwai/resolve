## Inspiration

Every SRE team has experienced the 3am page: a production service is down, users are impacted, and you need to investigate across logs, metrics, and deployment history to find what went wrong. This manual process takes 30-60 minutes per incident. During that time, users are affected, revenue is lost, and engineers burn out from repetitive toil.

We asked: what if an AI agent could perform the entire investigation autonomously, following the same systematic protocol that senior SREs use, but in seconds instead of minutes?

## What it does

Resolve is an intelligent incident resolution agent built with Elastic Agent Builder that automates the complete incident lifecycle through a systematic 6-step protocol:

```
ASSESS --> INVESTIGATE --> CORRELATE --> DIAGNOSE --> ACT --> VERIFY
```

![Architecture](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/resolve-architecture.png)

The agent operates over a realistic microservices environment with **5 services**, **6 Elasticsearch indices**, and **4,098 documents** of observability data. It includes a built-in cascading failure scenario where a database connection pool misconfiguration in `order-service` causes failures across the entire stack.

### The 6-Step Protocol

| Step | What It Does | Tools Used |
|------|-------------|------------|
| **ASSESS** | Checks health of all services, reads error logs, determines severity | `get-service-health` + `search-error-logs` (ES\|QL) |
| **INVESTIGATE** | Analyzes error rate, latency, CPU trends in 5-min buckets | `analyze-error-trends` (ES\|QL) |
| **CORRELATE** | Cross-references deployments with incident timeline | `check-recent-deployments` (ES\|QL) |
| **DIAGNOSE** | Searches runbook knowledge base via semantic matching | `search-runbooks` (ELSER Index Search) |
| **ACT** | Creates incident record, notifies on-call, logs remediation | `create-incident` + `notify-oncall` + `execute-remediation` (Workflows) |
| **VERIFY** | Re-checks metrics to confirm recovery | `get-service-health` + `analyze-error-trends` (ES\|QL) |

### The Incident Scenario

| Time | Event |
|------|-------|
| T+0 | `order-service` v2.4.1 deployed with DB pool misconfigured (50 to 5) |
| T+2min | Database connection timeout errors appear |
| T+6min | Error rate spikes to **45%**, cascading to payment-service |
| T+8min | notification-service starts failing |
| T+10min | Alert fires: "order-service error rate > 30%" |
| T+10min | **Resolve agent investigates** |
| T+12min | Agent identifies root cause, recommends rollback |
| T+20min | After rollback, all services recover to baseline |

### Agent Output Example

The agent produces a complete incident report with:
- **Root Cause**: DB connection pool reduced from 50 to 5 in v2.4.1 deployment
- **Evidence Chain**: Timeline table with specific numbers (error rate 0.2% to 44.2%, latency 118ms to 2509ms)
- **MTTR**: 22 minutes
- **Recommended Action**: Rollback to v2.3.9
- **Runbook Match**: "Database Connection Pool Exhaustion" procedure

## How we built it

**Elastic Agent Builder** is the core framework. We used all three tool types:

### ES|QL Tools (4)
Parameterized Elasticsearch query language tools for structured analytics:

```sql
FROM resolve-metrics
| WHERE service == ?service
| WHERE @timestamp >= NOW() - TO_TIMEDURATION(?time_window)
| STATS avg_error_rate = AVG(error_rate),
        avg_latency = AVG(request_latency_ms),
        max_cpu = MAX(cpu_percent)
  BY BUCKET(@timestamp, 5 minutes)
| SORT `BUCKET(@timestamp, 5 minutes)` DESC
```

The agent fills in `?service` and `?time_window` parameters at runtime. No backend code needed.

### Index Search Tool (1)
Semantic search using **ELSER** (Elastic Learned Sparse Encoder) over a runbook knowledge base. The `resolve-runbooks` index uses `semantic_text` field type with `.elser-2-elasticsearch` inference. The agent describes symptoms in natural language and gets matching resolution procedures.

### Elastic Workflow Tools (3)
Automated actions the agent triggers after diagnosis:
- **create-incident**: Writes a formal incident record to `resolve-incidents` index
- **notify-oncall**: Sends webhook notification to the on-call team
- **execute-remediation**: Logs the remediation action (rollback, restart, scale-up)

### Data Layer
6 Elasticsearch indices with carefully designed mappings:

| Index | Docs | Purpose |
|-------|------|---------|
| `resolve-logs` | 2,756 | Application logs with level, service, error_code, trace_id |
| `resolve-metrics` | 1,320 | CPU, memory, latency, error_rate, RPS per service |
| `resolve-deployments` | 7 | Version history with deployer, changes, commit hash |
| `resolve-runbooks` | 10 | Resolution procedures with semantic_text for vector search |
| `resolve-alerts` | 5 | Alert triggers with threshold vs actual values |
| `resolve-incidents` | Agent-created | Incident records written by workflow tools |

### Infrastructure
- **Elastic Cloud Serverless** -- zero infrastructure management
- **Kibana** is the UI -- no custom frontend built
- **Python** synthetic data generator with realistic cascading failure patterns
- **One-click setup** -- single script creates indices, ingests data, deploys tools, and registers the agent

## Challenges we ran into

**ES|QL time duration format.** The `TO_TIMEDURATION()` function requires full unit names ("2 hours") not abbreviations ("2h"). The agent initially sent abbreviated formats, causing query failures. We fixed this by updating tool parameter descriptions to guide the LLM toward the correct format -- a lesson in how tool descriptions are prompts too.

**Serverless compatibility.** Elastic Serverless doesn't support `number_of_shards` or `number_of_replicas` settings. Our initial index mappings included these, causing creation failures. We stripped all settings blocks to be serverless-compatible.

**Prompt engineering for reliable tool selection.** Getting the agent to consistently follow the 6-step protocol and chain 8+ tools in the correct order required iterating on the agent instructions multiple times. The key insight: be explicit about which tool to use at each step and what to look for in the results. Vague instructions led to skipped steps.

**Synthetic data realism.** The agent's ability to find correlations depends entirely on the data having clear, realistic patterns. We iterated the data generator multiple times to ensure deployment timestamps aligned precisely with metric spikes and that cascading failures had realistic propagation delays across dependent services.

## Accomplishments that we're proud of

- The agent correctly identifies the root cause (DB pool misconfiguration from 50 to 5 connections) by **chaining 8+ tool calls across 4 different data sources** in a single conversation
- The semantic runbook search (ELSER-powered) accurately matches "database connection pool exhaustion" to the correct runbook out of 10 candidates
- The incident report includes a **precise timeline table with specific numbers** -- not vague summaries, but exact metrics at each 5-minute interval
- Uses **all three Agent Builder tool types**: ES|QL, Index Search, and Elastic Workflows
- The entire project deploys in under 2 minutes with a single script
- **MTTR reduced from 45 minutes (manual) to under 5 minutes (agent-assisted)**

## What we learned

**ES|QL is powerful for agent tools.** Being able to write parameterized analytics queries that the LLM fills in at runtime is a game-changer. The agent performs time-bucketed aggregations, multi-field correlations, and sorted result analysis without any custom backend code.

**Semantic search changes everything for knowledge bases.** The ELSER-powered index search tool found the right runbook from natural language symptom descriptions every time. No custom embedding pipeline, no vector DB setup -- just a `semantic_text` field type and an inference ID.

**Agent instructions are the real product.** The 6-step protocol in the agent's system instructions is what makes Resolve reliable. Without structured step-by-step reasoning, the agent skips straight to conclusions. The instructions force it to gather evidence systematically before diagnosing.

**Tool descriptions are prompts.** The `description` field on each tool is not just documentation -- it's how the LLM decides when and how to use the tool. Writing precise, actionable descriptions (including format hints like "use full time unit names") directly impacts agent reliability.

## What's next for Resolve

- **Live alerting integration**: Connect to PagerDuty/OpsGenie webhooks so Resolve starts investigating the moment an alert fires
- **Multi-incident correlation**: Track patterns across incidents to identify systemic reliability issues
- **Custom runbook ingestion**: Let teams upload their own runbooks and resolution procedures
- **Post-mortem generation**: Automatically compile investigation steps into a formatted post-mortem document

## Built With

Elastic Agent Builder, Elasticsearch, ES|QL, ELSER, Elastic Workflows, Kibana, Python

## Links

- **GitHub**: [github.com/brn-mwai/resolve](https://github.com/brn-mwai/resolve)

---

*Built by [Brian Mwai](https://github.com/brn-mwai) for the Elasticsearch Agent Builder Hackathon, February 2026.*
