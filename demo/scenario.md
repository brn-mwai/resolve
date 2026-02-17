# Resolve - Demo Script (3 minutes)

## Setup Checklist
- [ ] Elastic serverless trial active, data freshly ingested (`python data/generate.py && python scripts/setup.py`)
- [ ] Resolve agent created and all 8 tools working
- [ ] Kibana dashboard open (services healthy/green)
- [ ] Agent Builder chat tab open (Resolve selected)
- [ ] Terminal 1 ready: `python demo/trigger_incident.py --mode realtime`
- [ ] Terminal 2 ready: `python demo/trigger_memory_leak.py`
- [ ] Terminal 3 ready: `python demo/oncall_receiver.py` (watching for notifications)
- [ ] Screen recording running (OBS or similar)

---

## Script

### [0:00-0:08] The Hook
**Voiceover:** "It's 3am. Your phone buzzes. Production is down. You have 45 minutes of manual investigation ahead of you -- unless you have Resolve."

**Show:** Black screen with the alert text, then cut to Kibana dashboard.

### [0:08-0:20] What Resolve Does
**Voiceover:** "Resolve is an autonomous SRE agent built with Elastic Agent Builder. It investigates incidents the way a senior engineer would -- but in under 5 minutes, not 45."

**Show:** Architecture diagram (01-architecture.png), then the 6-step protocol bar.

### [0:20-0:35] The Setup
**Voiceover:** "We have 5 microservices, 6 Elasticsearch indices with 4,000 documents of real observability data, and 8 custom tools: 4 ES|QL for analytics, 1 ELSER-powered semantic search for runbooks, and 3 Elastic Workflows for automated actions."

**Show:** Tools list (03-tools-list.png), then dashboard showing healthy services.

### [0:35-0:50] Scenario 1: The Cascading Failure
**Action:** Run `python demo/trigger_incident.py --mode realtime` in Terminal 1.

**Voiceover:** "A developer just deployed order-service v2.4.1 with a database pool misconfigured from 50 connections down to 5. Watch the cascade."

**Show:** Dashboard metrics turning red. Error rates spiking across services.

### [0:50-1:50] The Agent Investigates
**Action:** Switch to Agent Builder. Type the prompt:

> "Critical alert on order-service. Error rates are spiking and cascading to payment-service and notification-service. Investigate and resolve."

**Narrate each step as it happens:**

1. **ASSESS** (5s): "The agent checks all 5 services. order-service is at 45% error rate, with payment and notification degraded."

2. **INVESTIGATE** (10s): "It runs trend analysis. Error rate jumped from 0.2% to 44.3%. Latency spiked from 118ms to 2,500ms."

3. **CORRELATE** (8s): "It checks deployments and finds v2.4.1 by bob.kumar -- the deployment note says 'Changed max pool size from 50 to 5 for testing - FORGOT TO REVERT.' That's the smoking gun."

4. **DIAGNOSE** (8s): "ELSER semantic search matches the exact runbook: Database Connection Pool Exhaustion. It recommends immediate rollback."

5. **ACT** (15s): "The agent creates a formal incident record, notifies the on-call team, and logs the remediation action -- all through Elastic Workflows."

**Show:** Each tool call result as the agent progresses.

### [1:50-2:00] The Result
**Voiceover:** "In under 2 minutes, Resolve identified the root cause, matched the runbook, created the incident ticket, notified the team, and logged the fix. 90% faster than manual."

**Show:** The final incident summary from the agent.

### [2:00-2:30] Scenario 2: The Surprise (Proves it's not hardcoded)
**Voiceover:** "But can it handle a completely different incident? Let's find out."

**Action:** Run `python demo/trigger_memory_leak.py` in Terminal 2. Then prompt:

> "user-service memory is climbing steadily with GC overhead errors. Investigate."

**Voiceover:** "This time there's no bad deployment to find. The agent takes a completely different path: it identifies a memory leak, matches a different runbook, and recommends pod restarts instead of rollback. Same agent, same tools, different reasoning."

**Show:** Agent conversation showing the different investigation path.

### [2:30-2:50] The Reasoning Trace
**Voiceover:** "Here's what happened under the hood."

**Show:** Reasoning trace diagram (11-reasoning-trace.png). "13 LLM calls, 10 tool calls, 148K tokens processed, all in 113 seconds."

### [2:50-3:00] The Impact
**Show:** Impact comparison (10-impact.png).

**Voiceover:** "Mean time to resolution: 45 minutes down to under 5. At 2 incidents per week, that's $468,000 per year in saved engineering time and reduced downtime. This is Resolve."

**End card:** Resolve logo, GitHub URL, "Built with Elastic Agent Builder"

---

## Key Prompts

**Scenario 1 (DB Pool):**
> Critical alert on order-service. Error rates are spiking and cascading to payment-service and notification-service. Investigate and resolve.

**Scenario 2 (Memory Leak):**
> user-service memory usage is climbing steadily and response times are degrading. GC overhead errors detected. Investigate and resolve.

## What Makes This Demo Win

1. **The Hook**: Emotional connection in 8 seconds -- every SRE has lived this
2. **Two Scenarios**: Proves the agent reasons, not just follows a script
3. **Live Workflows**: Real incident records created, real notifications sent
4. **The Numbers**: $468K/year is a number judges remember
5. **All Three Tool Types**: ES|QL + ELSER + Workflows = full platform utilization
