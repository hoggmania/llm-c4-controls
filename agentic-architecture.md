# Agentic Application — Control Architecture (One-Pager)

**Scope:** How an LLM agent's proposed *actions* (tool calls, MCP, state changes) are
typed, authorized, constrained, executed, observed, and audited — independent of what
the model says in prose. Primary framework: **OWASP Top 10 for Agentic Applications 2026**
(`ASI01`–`ASI10`); secondary: OWASP GenAI LLM Top 10 2026 (`LLM01`–`LLM10`).

---

## Two non-negotiable reframes

1. **The model is not an authorization boundary.** It must hold no direct tool
   credentials and have no direct network path to external actions. Every side-effecting
   action is mediated by deterministic components the model cannot bypass.
2. **Tool results are untrusted input.** Anything a tool returns is treated as hostile
   (schema, provenance, sensitive content) before it can influence the agent's next step.

---

## Lifecycle of a single agent action

Each action flows through a non-bypassable path, bound to one immutable **action ID**
that links proposal → decision → approval → budget → execution grant (so none can be
replayed for a different action).

| # | Stage | What happens | Key controls |
|---|---|---|---|
| 1 | **Action planning** | Model emits a *typed proposal* from an allowlisted tool/MCP registry. | Allowlisted registry; no direct credentials |
| 2 | **Authorization** | Canonical parameter validation, then identity-/tenant-/resource-/purpose-aware policy. | Read ≠ write separation; canonicalization |
| 3 | **Approval** | Destructive / financial / privileged / bulk-export actions hit a human gate showing the exact scoped action + expiry. | Explicit human approval; scoped expiry |
| 4 | **Constrained execution** | Short-lived scoped creds; transaction limits; idempotency; dry-run/rollback; isolated tool/MCP proxy. | Sandbox proxy; least privilege |
| 5 | **Result handling** | Tool output validated (schema, provenance, PII) before next step. | Untrusted-input contract |
| 6 | **Runtime safety** | Rate / concurrency / step / token / time / cost budgets + deadlines, bounded retry, circuit breaker, safe fallback, kill switch. | Budget envelopes; kill switch |
| 7 | **Evidence** | Proposal, policy version, approval, attempts, side effects, result, latency, tokens, cost → append-only audit. | Append-only trace → SIEM |

---

## Layered control model

- **Ingestion** — controlled entry; typed proposals only.
- **Runtime / Agent core** — policy decision + approval + constrained execution proxy.
- **Supply chain** — tool/MCP provenance, signed/pinned deps, provider config hygiene.
- **Detection & feedback** — anomaly detection, drift loop, audit→SIEM, red-team queue.

A weakness in an earlier layer propagates forward; monitoring feeds fixes back into
ingestion and runtime. The layers are connected, not isolated.

---

## OWASP Agentic Top 10 2026 — coverage posture

All `ASI01`–`ASI10` are covered by at least one stage above. Coverage is **marked
explicitly as partial** where the current component view does not claim full mitigation:

| Status | Categories needing more than the current view |
|---|---|
| Partial | Goal integrity, signed/pinned tool provenance, persistent memory controls, agent-to-agent protocols, per-agent behavioral attestation |

Treat partial coverage as open architecture decisions, not a label hidden inside a
generic "guardrails" box.

---

## Known gaps (do not ship without addressing)

- Signed + pinned tool/MCP provenance (no replay, no substitution).
- Persistent-memory isolation and redaction controls.
- Agent-to-agent protocol authentication and scoping.
- Per-agent behavioral attestation / drift from approved policy.
- Goal-integrity checks that detect instruction-conflict or goal-hijack.

**Authoritative artifact:** `05-agent-tool-runtime-controls.puml` (C4 L3). Full
component crosswalk and strength ratings: `05-owasp-coverage.md`.
