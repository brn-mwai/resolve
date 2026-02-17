## Inspiration

It's 3am. Your phone buzzes. Production is down. Error rates are spiking, cascading across services, and users are impacted. You open four dashboards, grep through logs, search Confluence for the runbook, page the on-call team, and write up the incident ticket. Forty-five minutes later, you find the root cause: someone changed a config value from 50 to 5.

Every SRE team has lived this. The average incident takes 30-60 minutes to investigate manually. At 2 incidents per week, that's $468,000/year in lost engineering time and extended downtime.

We asked: what if an AI agent could do the entire investigation autonomously -- following the same systematic protocol that senior SREs use, but in under 5 minutes?

## What it does

Resolve is an intelligent incident resolution agent built with Elastic Agent Builder that automates the complete incident lifecycle through a systematic 6-step protocol:

```
ASSESS --> INVESTIGATE --> CORRELATE --> DIAGNOSE --> ACT --> VERIFY
```

The agent operates over a realistic microservices environment with **5 services**, **6 Elasticsearch indices**, and **4,098 documents** of observability data. It handles **multiple incident types** with different investigation paths:

- **Scenario 1: Cascading DB Pool Failure** -- A deployment misconfiguration in `order-service` causes failures across the entire stack. The agent correlates the deployment, matches the DB pool runbook, and recommends rollback.
- **Scenario 2: Memory Leak** -- `user-service` memory climbs steadily with no bad deployment to blame. The agent takes a completely different path: skips deployment correlation, identifies the memory leak pattern, matches a different runbook, and recommends pod restarts.

Same agent, same tools, different reasoning. This proves Resolve isn't hardcoded -- it thinks.

---

## Screenshots

### 1. Architecture Overview
> Resolve uses all three Agent Builder tool types: 4 ES|QL tools for structured analytics, 1 ELSER-powered Index Search for semantic runbook matching, and 3 Elastic Workflows for automated incident actions. All running on Elastic Cloud Serverless with Kibana as the UI.

![Architecture](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/01-architecture.png)

### 2. Resolve Agent in Kibana Agent Builder
> The Resolve agent configured in Kibana with 8 custom tools and a 6-step investigation protocol in the system instructions. Powered by Claude Opus 4.5 as the reasoning model.

![Agent Builder](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/02-agent-builder.png)

### 3. All 8 Custom Tools Deployed
> 4 ES|QL tools (search-error-logs, analyze-error-trends, check-recent-deployments, get-service-health), 1 Index Search tool (search-runbooks with ELSER), and 3 Workflow tools (create-incident, notify-oncall, execute-remediation).

![Tools List](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/03-tools-list.png)

### 4. Step 1 ASSESS: Agent Checks Service Health
> The agent begins by calling `get-service-health` to get a broad view across all 5 microservices, then `search-error-logs` for order-service. It identifies elevated error rates and determines this is a Critical severity incident with cascading impact.

![Step ASSESS](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/04-step-assess.png)

### 5. Step 2 INVESTIGATE: Error Trend Analysis
> The agent calls `analyze-error-trends` and receives 5-minute bucketed metrics showing the exact inflection point. Error rate jumps from 0.2% baseline to 44.2% at the peak. Latency spikes from 118ms to 2,509ms. CPU hits 92%.

![Step INVESTIGATE](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/05-step-investigate.png)

### 6. Step 3 CORRELATE: Deployment Found
> The agent calls `check-recent-deployments` and discovers order-service v2.4.1 was deployed by bob.kumar at 07:35 UTC. The deployment note reads: "Changed max pool size from 50 to 5 for testing -- FORGOT TO REVERT." The deployment timestamp matches the error spike exactly.

![Step CORRELATE](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/06-step-correlate.png)

### 7. Step 4 DIAGNOSE: Runbook Semantic Search Match
> The agent calls `search-runbooks` with the symptoms "database connection pool exhaustion high error rate". ELSER semantic matching returns the exact runbook: "Database Connection Pool Exhaustion" with step-by-step resolution instructions including "IMMEDIATE ROLLBACK to previous version."

![Step DIAGNOSE](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/07-step-diagnose.png)

### 8. Step 5 ACT: Complete Incident Report
> The agent produces a formal incident report with root cause, a precise evidence chain timeline table (specific error rates and latency at each 5-minute interval), severity assessment, recommended rollback action, runbook reference, and on-call notification draft. MTTR: 22 minutes.

![Step ACT](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/08-step-act.png)

### 9. Kibana Dashboard: Service Health Visualization
> The Resolve dashboard shows 5 panels: Service Error Rate Trends (line chart), Error Log Count by Service (bar chart), Active Alerts by Severity (donut), Deployment Timeline (table), and Request Latency Trends (line chart). The error spike from the cascading failure is clearly visible.

![Dashboard](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/09-dashboard.png)

### 10. Impact: Before vs After
> Manual incident investigation takes 30-60 minutes. Resolve automates the entire process in under 5 minutes using structured multi-step reasoning across logs, metrics, deployments, and runbooks.

![Impact](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/10-impact.png)

### 11. Agent Reasoning Trace
> Under the hood: the full investigation flow visualized. 10 tool calls across 3 tool types, chained through autonomous reasoning. The agent assessed, investigated, correlated, diagnosed, and acted -- producing a formal incident record, on-call notification, and remediation log. 13 LLM calls, 148K tokens, 113 seconds total.

![Reasoning Trace](https://raw.githubusercontent.com/brn-mwai/resolve/main/docs/screenshots/11-reasoning-trace.png)

---

## The 6-Step Protocol

| Step | What It Does | Tools Used |
|------|-------------|------------|
| **ASSESS** | Checks health of all services, reads error logs, determines severity | `get-service-health` + `search-error-logs` (ES\|QL) |
| **INVESTIGATE** | Analyzes error rate, latency, CPU trends in 5-min buckets | `analyze-error-trends` (ES\|QL) |
| **CORRELATE** | Cross-references deployments with incident timeline | `check-recent-deployments` (ES\|QL) |
| **DIAGNOSE** | Searches runbook knowledge base via semantic matching | `search-runbooks` (ELSER Index Search) |
| **ACT** | Creates incident record, notifies on-call, logs remediation | `create-incident` + `notify-oncall` + `execute-remediation` (Workflows) |
| **VERIFY** | Re-checks metrics to confirm recovery | `get-service-health` + `analyze-error-trends` (ES\|QL) |

## The Incident Scenario

| Time | Event |
|------|-------|
| T+0 | `order-service` v2.4.1 deployed with DB pool misconfigured (50 to 5) |
| T+2min | Database connection timeout errors appear |
| T+6min | Error rate spikes to **45%**, cascading to payment-service |
| T+8min | notification-service starts failing |
| T+10min | Alert fires: "order-service error rate > 30%" |
| T+10min | **Resolve agent investigates** |
| T+12min | Agent identifies root cause, recommends rollback to v2.3.9 |
| T+20min | After rollback, all services recover to baseline |

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
- **create-incident**: Writes a formal incident record to `resolve-incidents` index with severity, service, timeline
- **notify-oncall**: Sends webhook notification to the on-call engineering team with incident details
- **execute-remediation**: Logs the remediation action (rollback, restart, scale-up) against the incident record

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

- The agent correctly identifies the root cause (DB pool misconfiguration from 50 to 5 connections) by **chaining 10 tool calls across 4 different data sources** in a single conversation
- **Two completely different incident scenarios** (DB pool failure vs memory leak) prove the agent reasons autonomously -- it takes different investigation paths, matches different runbooks, and recommends different remediations
- The semantic runbook search (ELSER-powered) accurately matches symptoms to the correct runbook out of 10 candidates, regardless of the incident type
- The incident report includes a **precise timeline table with specific numbers** -- not vague summaries, but exact metrics at each 5-minute interval
- All three Elastic Workflow tools fire successfully: incident record created, on-call team notified, remediation action logged
- Uses **all three Agent Builder tool types**: ES|QL, Index Search, and Elastic Workflows
- The entire project deploys in under 2 minutes with a single script
- **MTTR reduced from 45 minutes (manual) to under 5 minutes (agent-assisted)** -- $468K/year in savings at 2 incidents/week

## What we learned

**ES|QL is powerful for agent tools.** Being able to write parameterized analytics queries that the LLM fills in at runtime is a game-changer. The agent performs time-bucketed aggregations, multi-field correlations, and sorted result analysis without any custom backend code.

**Semantic search changes everything for knowledge bases.** The ELSER-powered index search tool found the right runbook from natural language symptom descriptions every time. No custom embedding pipeline, no vector DB setup -- just a `semantic_text` field type and an inference ID.

**Agent instructions are the real product.** The 6-step protocol in the agent's system instructions is what makes Resolve reliable. Without structured step-by-step reasoning, the agent skips straight to conclusions. The instructions force it to gather evidence systematically before diagnosing.

**Tool descriptions are prompts.** The `description` field on each tool is not just documentation -- it's how the LLM decides when and how to use the tool. Writing precise, actionable descriptions (including format hints like "use full time unit names") directly impacts agent reliability.

## What's next for Resolve

- **Live alert-triggered investigations**: Connect to PagerDuty/OpsGenie webhooks so Resolve starts investigating the moment an alert fires -- zero human intervention needed
- **Multi-incident pattern detection**: Track patterns across incidents to identify systemic reliability issues before they cascade
- **Custom runbook ingestion**: Let teams upload their own runbooks via drag-and-drop; ELSER indexes them automatically for semantic search
- **Post-mortem generation**: Automatically compile the agent's investigation steps, evidence chain, and timeline into a formatted post-mortem document
- **Cost tracking**: Calculate the dollar value of each incident resolved, building the business case for autonomous incident response

---

*Built by [Brian Mwai](https://github.com/brn-mwai) for the Elasticsearch Agent Builder Hackathon, February 2026.*
