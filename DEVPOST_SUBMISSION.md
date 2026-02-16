# Devpost Submission: Resolve

## Project Name
Resolve - Intelligent Incident Resolution Agent

## Tagline
An AI-powered SRE agent that investigates production incidents, identifies root causes, and delivers resolution in under 5 minutes.

---

## Inspiration

Every SRE team has experienced the 3am page: a production service is down, users are impacted, and you need to investigate across logs, metrics, and deployment history to find what went wrong. This process is manual, stressful, and takes an average of 45 minutes per incident.

We asked: what if an AI agent could perform the entire investigation autonomously, following the same systematic protocol that senior SREs use, but in seconds instead of minutes?

## What it does

Resolve is an intelligent incident resolution agent built with Elastic Agent Builder that automates the complete incident lifecycle through a 6-step protocol:

1. **ASSESS** - Checks service health across all microservices, reads error logs, and determines severity
2. **INVESTIGATE** - Analyzes error rate, latency, and CPU trends in 5-minute buckets to pinpoint when degradation started
3. **CORRELATE** - Cross-references recent deployments with the incident timeline to find what changed
4. **DIAGNOSE** - Searches a semantic runbook knowledge base to match symptoms with known resolution procedures
5. **ACT** - Produces a formal incident report with root cause, evidence chain, and specific remediation recommendations
6. **VERIFY** - Re-checks service health to confirm whether the situation is improving

The agent works over a realistic microservices environment with 5 services, 6 Elasticsearch indices, and 4,000+ documents of observability data. It includes a built-in cascading failure scenario where a database connection pool misconfiguration in one service causes failures across the entire stack.

## How we built it

**Elastic Agent Builder** is the core framework. We created:

- **4 ES|QL Tools** - Parameterized Elasticsearch query language tools for structured data analysis:
  - `search-error-logs`: Searches error/critical logs by service and time window
  - `analyze-error-trends`: Aggregates metrics into 5-minute trend buckets
  - `check-recent-deployments`: Correlates deployment history with incident timelines
  - `get-service-health`: Real-time health overview across all services

- **1 Index Search Tool** - Semantic search using ELSER over a runbook knowledge base:
  - `search-runbooks`: Matches natural language symptom descriptions to resolution procedures

- **Custom Agent Instructions** - A detailed 6-step investigation protocol that guides the LLM through systematic multi-step reasoning, ensuring it uses data to support every conclusion.

- **6 Elasticsearch Indices** - Logs, metrics, deployments, runbooks, alerts, and incidents with carefully designed mappings including semantic_text fields for vector search.

- **Synthetic Data Generator** - A Python script that generates 4,098 realistic documents with a built-in cascading failure incident, including correlated timestamps across logs, metrics, and deployments.

The entire project runs on **Elastic Cloud Serverless** with zero infrastructure management. Kibana is the UI -- no custom frontend needed.

## Challenges we ran into

- **ES|QL time duration format**: The `TO_TIMEDURATION()` function requires full unit names ("2 hours") not abbreviations ("2h"). The agent initially sent abbreviated formats, so we updated tool parameter descriptions to guide it toward the correct format.

- **Serverless compatibility**: Elastic Serverless doesn't support `number_of_shards` or `number_of_replicas` settings. We had to strip these from all index mappings.

- **Prompt engineering for reliable tool selection**: Getting the agent to consistently follow the 6-step protocol and chain tools correctly required iterating on the agent instructions multiple times. The key insight was being explicit about which tool to use at each step and what to look for in the results.

- **Synthetic data realism**: The agent's ability to find correlations depends entirely on the data having clear, realistic patterns. We iterated the data generator to ensure deployment timestamps aligned with metric spikes and that cascading failures had realistic propagation delays.

## Accomplishments that we're proud of

- The agent correctly identifies the root cause (DB pool misconfiguration from 50 to 5 connections) by chaining 5+ tool calls across 4 different data sources in a single conversation
- The semantic runbook search (ELSER-powered) accurately matches "database connection pool exhaustion high error rate" to the correct runbook out of 10 candidates
- The incident report includes a precise timeline table with specific numbers (error rate from 0.2% to 44.2%, latency from 118ms to 2509ms)
- The entire setup deploys in under 2 minutes with a single script
- MTTR reduced from 45 minutes (manual) to under 5 minutes (agent-assisted)

## What we learned

- **ES|QL is powerful for agent tools**: Being able to write parameterized analytics queries that the LLM fills in at runtime is a game-changer. The agent can do time-bucketed aggregations, multi-field correlations, and sorted result analysis without any custom backend code.

- **Semantic search changes everything for knowledge bases**: The ELSER-powered index search tool found the right runbook from natural language descriptions every time. No custom embedding pipeline, no vector DB setup -- just a `semantic_text` field.

- **Agent instructions are the real product**: The 6-step protocol in the agent's system instructions is what makes Resolve reliable. Without structured step-by-step reasoning, the agent would skip straight to conclusions. The instructions force it to gather evidence systematically before diagnosing.

## What's next for Resolve

- **Live alerting integration**: Connect to PagerDuty/OpsGenie webhooks so Resolve starts investigating the moment an alert fires
- **Automated remediation execution**: Use Elastic Workflows to execute rollbacks, restarts, and scaling actions directly from the agent
- **Multi-incident correlation**: Track patterns across incidents to identify systemic reliability issues
- **Custom runbook ingestion**: Let teams upload their own runbooks via a simple API

## Built With
- Elastic Agent Builder
- Elasticsearch (Serverless)
- ES|QL
- ELSER (Elastic Learned Sparse Encoder)
- Kibana
- Python

## Try it out

- **GitHub**: https://github.com/brn-mwai/resolve
- **Video Demo**: [link to demo video]

---

## Social Media Post (for +10 bonus)

Shipped Resolve for the @elastic Agent Builder Hackathon -- an AI agent that investigates production incidents in under 5 minutes.

It chains ES|QL queries across logs, metrics, and deployments, then matches symptoms to runbooks using semantic search. The 6-step protocol (ASSESS > INVESTIGATE > CORRELATE > DIAGNOSE > ACT > VERIFY) mimics how senior SREs think.

In our demo, it correctly traced a 45% error rate spike to a DB pool misconfiguration deployed 22 minutes earlier, found the matching runbook, and recommended the exact rollback.

Built on Elastic Cloud Serverless. Zero custom UI -- Kibana is the interface.

#ElasticAgentBuilder #ElasticSearch #DevOps #SRE #AI

https://devpost.com/software/resolve
