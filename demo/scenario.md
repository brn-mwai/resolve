# Resolve - Demo Script (3 minutes)

## Setup Checklist
- [ ] Elastic serverless trial active with data ingested
- [ ] Resolve agent created and tested
- [ ] Kibana dashboard open showing healthy services
- [ ] Agent Builder chat tab open (Resolve selected)
- [ ] Terminal ready with `python demo/trigger_incident.py --mode realtime`
- [ ] Second terminal ready with `python demo/trigger_incident.py --recover`
- [ ] Screen recording running (OBS or similar)

---

## Script

### [0:00-0:15] The Problem
**Voiceover:** "When production systems break, SRE teams spend 30 to 60 minutes manually digging through logs, correlating metrics with deployments, searching for runbooks, and executing fixes. That's 30 to 60 minutes of downtime for every incident."

**Show:** Kibana dashboard with all services healthy (green).

### [0:15-0:30] Introducing Resolve
**Voiceover:** "Resolve is an AI-powered SRE agent built with Elastic Agent Builder. It automates the entire incident investigation and resolution lifecycle using a systematic 6-step protocol."

**Show:** Brief flash of architecture diagram.

### [0:30-0:50] The Incident
**Action:** Run `python demo/trigger_incident.py --mode realtime` in terminal.

**Voiceover:** "A developer just deployed order-service v2.4.1 with a database connection pool misconfigured from 50 to 5 connections. Watch what happens."

**Show:** Dashboard metrics turning red. Error rates spiking. Point out the cascading failures.

### [0:50-2:20] The Agent in Action
**Action:** Switch to Agent Builder chat. Type the prompt:

> "Critical alert on order-service. Error rates are spiking and cascading to payment-service. Investigate and resolve."

**Voiceover (narrate each step as it happens):**

1. **ASSESS:** "The agent first checks overall service health. It sees order-service at 45% error rate, with payment and notification services degraded."

2. **INVESTIGATE:** "It analyzes error trends and pinpoints exactly when the metrics started degrading."

3. **CORRELATE:** "It checks recent deployments and finds order-service v2.4.1 was deployed right before the errors started. The deployment note mentions changing pool size from 50 to 5."

4. **DIAGNOSE:** "It searches runbooks and finds the Database Connection Pool Exhaustion procedure, which matches the symptoms perfectly."

5. **ACT:** "The agent generates a formal incident report with the evidence chain, assigns severity as Critical, and recommends an immediate rollback to v2.3.9. It drafts the on-call notification message."

6. **VERIFY:** (After running recovery) "After rollback, the agent confirms error rates are dropping back to normal."

### [2:20-2:40] Recovery
**Action:** Run `python demo/trigger_incident.py --recover` in second terminal.

**Show:** Dashboard metrics recovering to green.

**Voiceover:** "After the rollback, all services return to normal within minutes."

### [2:40-3:00] Impact
**Voiceover:** "Resolve reduced Mean Time To Resolution from 45 minutes to under 5 minutes. Built entirely with Elastic Agent Builder using ES|QL for analytics and semantic search for runbook matching. No custom UI needed -- Kibana is the interface."

**Show:** End card with project name, GitHub URL, tech stack.

---

## Key Prompts for Demo

**Primary:**
> Critical alert on order-service. Error rates are spiking and cascading to payment-service and notification-service. Please investigate and resolve.

**Fallback (if agent needs nudging):**
> Can you check what was recently deployed to order-service?

> Search the runbooks for database connection pool issues.

> Create an incident ticket and recommend a fix.
