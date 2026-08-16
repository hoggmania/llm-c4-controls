# Agent Execution-Safety, Authorization & Audit Controls — Candidate Tooling

Research summary of OSS and commercial software that can implement each control.
Legend: **OSS** = open-source core, **Comm** = commercial (may have OSS tier), **OSS+Comm** = both.
"Gaps" = what you must still build/wire; no single product covers the whole stack.

> **Cross-cutting note (read first):** No off-the-shelf product implements the full *agent-safety loop* end to end. The realistic architecture is **AI-native frameworks (LangGraph/AutoGen/ADK/Agent SDK) + MCP security layer (ToolHive/mcp-proxy) + generic hardened infra (Vault, Temporal, K8s, Envoy, OTel, SIEM)**. Combiners that span several controls: **ToolHive** (registry + proxy + egress + kill), **Temporal** (txn + resilience + kill via cancel), **LangSmith/Langfuse** (audit + risk-trace + post_alert source), **Vault** (credential + kill via revoke). Everything is "AI-native vs repurposed infra" — only ToolHive, HumanLayer, and the LLM-observability tools (LangSmith/Langfuse/AgentOps/Helicone) are purpose-built for agents; the rest repurpose infra (Vault, K8s, Envoy, SIEM).

---

## agent — Orchestrator runtime that plans but CANNOT call external tools directly
*Pattern: planner emits proposed tool calls (structured outputs); a separate hardened executor runs them. No framework enforces isolation by default — it's an architecture.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **LangGraph** (OSS) | OSS | `interrupt()`/checkpointer lets planner pause before a tool node; executor runs calls elsewhere. | Doesn't enforce no-network itself; you must architect the split. |
| **AutoGen** (Microsoft, OSS) | OSS | Multi-agent; route code/tool execution to a sandboxed "Executor" agent. | Default runs code locally; isolation is opt-in. |
| **CrewAI** (OSS) | OSS | Tasks produce outputs; bind tools only on a dedicated executor agent. | Agents usually hold tool bindings directly. |
| **Microsoft Agent Framework / Semantic Kernel** (OSS+Comm, Azure) | OSS+Comm | Enterprise orchestration; tools behind proxy, Azure Foundry. | Orchestrator still typically binds tools. |
| **Google ADK** (OSS) | OSS | Open agent framework; keep tools behind a proxy. | Same — no built-in isolation. |
| **Anthropic Agent SDK / tool-use** (Comm) | Comm | Typed tool_use blocks you intercept before execution. | Client SDK, not a sandbox runtime. |
| **Pydantic AI** (OSS) | OSS | Strict typed tool calls you validate/intercept pre-execution. | No built-in isolation; you run the executor. |
| **SmolAgents** (HuggingFace, OSS) | OSS | CodeAgent pattern; run generated code in a sandbox, not on host. | Code-exec focus; tool gating is custom. |

---

## proposal — Structured action builder (tool, op, resource, params, expected side effects)
*Native "expected side-effects" is not built into any tool — you extend the schema.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Pydantic / Pydantic AI** (OSS) | OSS | Define a typed `Action` model; agent must emit a valid instance. | Validation only, no policy/side-effect field. |
| **Instructor** (OSS) | OSS | Coerces free-form LLM output into typed Pydantic models. | Relies on model compliance. |
| **Anthropic / OpenAI tool-use JSON Schema** (Comm) | Comm | Tool defs are JSON Schema; model emits typed `tool_use`. | Schema is for the model; enforcement is the caller's job. |
| **LangGraph ToolCall** (OSS) | OSS | Tool calls are typed dicts (id/name/args) in the graph. | No side-effect declaration. |
| **MCP Tool schema** (Anthropic MCP spec, OSS) | OSS | Each tool carries `inputSchema` (JSON Schema). | No native "expected side effects" — extend it. |
| **jsonschema / ajv** (OSS) | OSS | Canonical JSON-Schema validation of the action. | Not LLM-aware. |
| **Cerberus** (OSS) | OSS | Lightweight schema + normalization. | Less ecosystem adoption. |

---

## registry — Tool / MCP allowlist (approved tools, ops, owners, schemas, risk tiers)
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **ToolHive** (Stacklok, OSS) | OSS | Runs MCP servers in isolated containers; capability/permission model. | MCP-focused; not a generic tool registry. |
| **MCP Registry spec + Smithery** (spec OSS / Smithery Comm) | OSS+Comm | Registry of MCP servers with metadata/discovery. | Registration ≠ authorization; add allowlist policy yourself. |
| **mcp-proxy** (OSS) | OSS | Reverse proxy in front of MCP servers; gate exposed tools. | No owner/risk metadata by default. |
| **Kong / Apigee** (Comm) | Comm | API gateways with allowlists, consumers, ACLs, ownership. | Generic; not AI-tool aware. |
| **OPA / Casbin** (OSS) | OSS | Encode the allowlist as policy (tool, op, owner, resource, risk). | Not a registry itself; you feed it the data. |
| **FastMCP** (OSS) | OSS | Build MCP servers with auth; mount only approved tools. | Per-server; allowlist is manual. |
| **Cloudflare MCP / Heroku MCP** (Comm) | Comm | Hosted/remote MCP registries. | Vendor lock-in; authz model varies. |

---

## param — Parameter & schema validator (canonicalize; reject injection/traversal/out-of-bounds)
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Pydantic** (OSS) | OSS | Typed validation, coercion, numeric/string constraints. | Not security-focused (no injection rules by default). |
| **Zod** (OSS) | OSS | TS/JS typed validation for param objects. | Same — no semantic checks. |
| **jsonschema / ajv** | OSS | Schema enforcement of params. | No injection/traversal detection. |
| **Guardrails AI** (OSS+Comm) | OSS+Comm | Validators + RAIL specs; detect injection, PII, out-of-bounds, can repair. | LLM-based validators add latency/non-determinism. |
| **Rebuff** (OSS) | OSS | Prompt-injection detection in inputs/params. | Prompt-specific; not all param types. |
| **Custom path canonicalization + regex** (generic) | OSS | Normalize path, reject `../`, bound lengths. | Manual to build/maintain. |
| **Semgrep** (OSS+Comm) | OSS+Comm | Static analysis of code; limited runtime param use. | Not a runtime param validator (unsure fit). |

---

## risk — Action risk classifier (destructive / irreversible / financial / privileged / bulk-export)
*Mostly custom + rules + an LLM judge; few turnkey products.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Custom LLM "risk judge"** (pattern) | OSS | Classify proposed action vs a risk taxonomy. | Needs eval; can misclassify. |
| **OPA / Casbin rules** (OSS) | OSS | Deterministic rules (e.g., `DELETE`→high, `export>1k`→high). | Static; no semantic understanding. |
| **NVIDIA NeMo Guardrails** (OSS) | OSS | Programmable rails; flag risky intents (input rails). | Built for prompt safety; you author the risk rail. |
| **Guardrails AI / RAIL** (OSS+Comm) | OSS+Comm | Policy rules that can flag unsafe actions. | More output-validation than action-semantics. |
| **Lakera Guard** (Comm) | Comm | Managed AI security; detects injection/unsafe actions, can block. | Prompt/input focus; action-risk is emerging. |
| **HumanLayer risk tagging / LangSmith metadata** (OSS+Comm) | OSS+Comm | Tag actions by risk to trigger approval. | Tagging, not classification engine. |
| **Lasso / HiddenLayer / Protect AI** (Comm) | Comm | AI security posture; some flag risky tool calls. | Specifics vary; verify per vendor (unsure). |

---

## approval — Informed, time-bound human approval gate for high-risk actions
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **HumanLayer** (OSS SDK + Comm) | OSS+Comm | Purpose-built HITL API; agents request approval, humans approve/reject with context; supports timeouts. | You wire risk→approval trigger. |
| **LangGraph `interrupt()`** (OSS) | OSS | Pauses for human input before a node executes. | UI/timeout/escalation you build. |
| **Temporal** (OSS+Comm) | OSS+Comm | Workflow waits on human "signal" with timers; durable, escalatable. | You build the approval UI. |
| **Microsoft Agent Framework + Azure Approval** (Comm) | Comm | Native human-approval steps in flows. | Azure-coupled. |
| **Jira / ticketing approvals** (Comm) | Comm | Approval recorded as a ticket (audit trail). | Slow; not real-time. |
| **Slack / email approve buttons** (custom) | OSS | Common lightweight pattern. | You build state + timeout. |

---

## credential — Credential broker issuing short-lived, tool- and resource-scoped creds after authorization
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **HashiCorp Vault** (OSS+Comm) | OSS+Comm | Dynamic secrets (AWS STS assumed_role, GCP, Azure, DB, SSH); short-lived, lease-scoped, revocable. | You map tool→role; not agent-aware. |
| **AWS STS / GCP STS / Azure AD** (Comm) | Comm | Native STS issuing short-lived, scoped tokens. | Cloud-specific. |
| **HashiCorp Boundary** (OSS+Comm) | OSS+Comm | Just-in-time, session-scoped access; no static creds. | Infra-access focus, not tool API creds. |
| **CyberArk / strongDM / Teleport** (Comm) | Comm | Privileged-access brokers; JIT creds + session recording. | Enterprise cost; not LLM-tool native. |
| **OIDC token exchange (RFC 8693) + your broker** (OSS pattern) | OSS | Exchange agent identity for scoped creds. | You build the broker. |
| **IAM Roles Anywhere / Workload Identity** (Comm) | Comm | Issue creds to workloads, scoped. | Infra-level, not per-tool. |

---

## txn — Transaction & idempotency guard (spend/row/change limits, dedupe, dry-run, rollback)
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Temporal** (OSS+Comm) | OSS+Comm | Durable workflows, idempotency keys, saga compensation/rollback, timers. | Heavy infra; you model the transaction. |
| **Cadence** (OSS, Temporal predecessor) | OSS | Same durable-orchestration model. | Legacy/maintenance. |
| **DB transactions + Outbox pattern** (OSS) | OSS | ACID for DB changes; row/change limits; rollback. | App-level, not agent-level. |
| **Redis `limits` / rate limiter** (OSS) | OSS | Spend/row/change quota guard. | Not a transaction; dedupe only. |
| **LangGraph checkpointer + conditional edges** (OSS) | OSS | Dry-run / state rollback within the graph. | Not external side effects. |
| **Idempotency-key pattern (Stripe/Resend-style)** (pattern) | OSS | Dedupe repeated calls. | Manual per-tool implementation. |

---

## proxy — Tool execution proxy / sandbox / egress gateway (network/file/process isolation)
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **ToolHive** (OSS) | OSS | Wraps MCP servers in isolated container; network egress allowlist + minimal perms. | MCP-only. |
| **E2B** (OSS core + Comm) | OSS+Comm | Firecracker microVM sandbox for agent code; network control. | Code-exec focus; tool-call proxying is custom. |
| **gVisor** (OSS, Google) | OSS | Syscall-intercepting sandbox (process/file isolation). | You run the proxy inside it. |
| **Docker / Firecracker / Kata** (OSS) | OSS | Container/microVM isolation baseline. | You build egress control. |
| **Envoy / Istio egress gateway** (OSS+Comm) | OSS+Comm | L7 egress filtering, mTLS, allowlists. | Not tool-semantics aware. |
| **Squid / forward proxy** (OSS) | OSS | HTTP egress allowlist. | No authz on tool semantics. |
| **Modal / Northflank** (Comm) | Comm | Managed sandboxed workloads w/ egress controls. | Vendor lock-in. |

---

## resilience — Resilience controller (deadlines, bounded retries/backoff, circuit breakers, safe fallback)
*Almost entirely repurposed generic infra.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Temporal** (OSS+Comm) | OSS+Comm | Activity timeouts, retry policies, exponential backoff. | Infra to operate. |
| **Tenacity** (OSS, Python) | OSS | Retries + backoff + stop conditions. | No circuit breaker. |
| **resilience4j** (OSS, Java) | OSS | Circuit breaker, retry, timeout, bulkhead. | JVM-only. |
| **Polly** (OSS, .NET) | OSS | Resilience policy set. | .NET runtime. |
| **Envoy / Istio** (OSS+Comm) | OSS+Comm | Circuit breaking, retries, timeouts at proxy. | Network-level, not agent logic. |
| **LangGraph / framework retries** (OSS) | OSS | Built-in tool-call retry. | Limited scope. |
| **Chaos Mesh / Gremlin** (OSS+Comm) | OSS+Comm | Chaos testing, not runtime resilience. | Validation only (limited fit). |

---

## kill — Kill switch & incident control (revoke tools/credentials, stop active runs)
*No dedicated "AI kill switch" product exists — compose from the below.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Vault lease revocation** (OSS+Comm) | OSS+Comm | Instantly revoke dynamic creds. | Only credentials. |
| **ToolHive stop/disable** (OSS) | OSS | Stop MCP servers, cut tool access. | MCP-only. |
| **Temporal cancel / terminate** (OSS+Comm) | OSS+Comm | Stop active runs durably. | Only if run is on Temporal. |
| **Kubernetes** (OSS) | OSS | Delete pods/jobs; network policies cut egress. | Broad, not agent-aware. |
| **Framework stop (LangGraph `.stop()`, Anthropic stop, OpenAI cancel)** (OSS+Comm) | OSS+Comm | Stop generation/run in-flight. | Per-framework semantics. |
| **Lakera Guard / PANW AI Runtime Security** (Comm) | Comm | Policy-based block/quarantine of risky activity. | Prompt/input focus. |
| **Envoy circuit breaker / egress cut** (OSS+Comm) | OSS+Comm | Stop routing to a tool backend. | Network-level only. |

---

## audit — Append-only trace pipeline (proposal, identity, policy, approval, execution, result, latency, tokens, cost)
*Most LLM-observability tools are mutable DBs — true immutability needs WORM/CloudTrail-style store.*

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **LangSmith** (Comm) | Comm | Traces every run/tool call; metadata, tokens, cost, latency. | Not WORM/immutable by default. |
| **Langfuse** (OSS+Comm) | OSS+Comm | Self-hostable LLM observability; traces, token/cost, sessions. | Still a DB; add WORM yourself. |
| **AgentOps** (OSS+Comm) | OSS+Comm | Agent-native sessions, tokens, cost, errors. | Not immutable. |
| **Helicone** (OSS+Comm) | OSS+Comm | LLM gateway + observability logging. | Not full proposal lifecycle. |
| **OpenTelemetry** (OSS) | OSS | Vendor-neutral traces/logs/metrics pipeline to any backend. | You choose/secure the backend. |
| **MLflow** (OSS+Comm) | OSS+Comm | Experiment tracking; logs params/artifacts (lineage). | Not real-time audit. |
| **AWS CloudTrail (WORM via S3 Object Lock)** (Comm) | Comm | Truly append-only/immutable API audit trail. | Cloud API scope, not agent-internal. |
| **OpenObserve / Loki / ClickHouse** (OSS+Comm) | OSS+Comm | Log stores for traces. | Loki not immutable; you enforce WORM. |

---

## post_alert — Audit→SIEM connector exporting immutable traces to SOC/IR
| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **OpenTelemetry Collector exporters** (OSS) | OSS | Splunk HEC, Elasticsearch, OTLP exporters; route to SIEM. | You configure pipelines; immutability = backend. |
| **Vector** (OSS, Datadog) | OSS | Observability data pipeline; ship logs to Splunk/Elastic/S3. | Not SIEM-specific. |
| **Fluent Bit / Fluentd** (OSS) | OSS | Ubiquitous log forwarders to SIEM. | Generic. |
| **Falco** (OSS, Sysdig) | OSS | Runtime security; emits anomalies to SIEM (sandbox behavior). | Runtime focus, not audit semantics. |
| **Cribl** (Comm) | Comm | Enterprise pipeline routing/transform to SIEM. | Cost. |
| **Splunk HEC / Elastic Agent / Sentinel connectors** (Comm) | Comm | Native SIEM ingest. | Vendor-specific. |
| **Loki → Grafana OnCall / Alertmanager** (OSS) | OSS | Alerting on log patterns. | Not SOC-grade SIEM. |

---

## One-line recommendation
Build the loop as: **LangGraph/AutoGen (agent, proposal) → ToolHive + OPA (registry, param, proxy) → Vault (credential) → Temporal (txn, resilience, kill) → HumanLayer (approval) → OTel+Langfuse (audit) → Vector/OTel-exporters (post_alert)**, with risk classification as a custom LLM-judge + OPA rules layer, and a WORM/CloudTrail-style store for true append-only audit.
