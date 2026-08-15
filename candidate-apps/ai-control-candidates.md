# AI/LLM Control Implementation — Candidate Tools by Control

Classification legend used below:
- **Gateway** = sits in the request path, can allow/deny/transform/rate-limit.
- **Guardrail lib** = code-level validator/filter you call on input or output.
- **Observability** = logs/traces/costs; may alert but usually does not enforce.
- **Policy engine** = general authz/decision layer you wire into the path.
- **Serving layer** = model server you operate; controls what its endpoints expose.
- **Crypto/KMS** = encryption primitives / key management.
- **Agent framework** = orchestration runtime with loop/step limits.

All entries verified via vendor docs (Aug 2026). Items I could not confirm are marked **`unsure`**.

---

## ss_enc — Encrypt embeddings at rest + in transit (vector DB as a sensitive store)

| Candidate | Type | Fit | Gaps |
|---|---|---|---|
| **Google Tink** (KmsEnvelopeAead) | OSS (Apache-2.0) | Crypto lib for client-side **envelope encryption** of embeddings before they hit the vector DB; integrates with GCP/AWS/Azure KMS as KEK. | App must encrypt/decrypt in code; no key rotation UI; needs a KMS backend. |
| **HashiCorp Vault — Transit secrets engine** | Open core (BSL) | Encryption-as-a-Service / envelope encryption; central DEK wrapping, audit log, per-tenant keys. | BSL license (not OSI); operational burden to run HA; still need app to call it. |
| **Cloud KMS** (AWS KMS / GCP KMS / Azure Key Vault) | Commercial (managed) | Managed KEK for envelope encryption of stored embeddings + TLS for in-transit; CMEK for managed vector stores. | Managed-service lock-in; at-rest only unless paired with Tink/Vault app-side encryption. |
| **PostgreSQL `pgcrypto` / `pg_tde`** | OSS | If embeddings live in Postgres/pgvector, `pgcrypto` (column encryption) or Percona `pg_tde` (TDE) encrypt at rest; TLS for transit. | Native TDE only via extensions/Enterprise Postgres; app-layer key handling. |
| **Redis** (TLS + at-rest encryption) | OSS core + Commercial (Enterprise/Cloud) | In-transit TLS and at-rest encryption for cached/operational vectors. | OSS Redis has no native at-rest encryption (Enterprise/Cloud does); not a primary vector store here. |
| **MongoDB** (CSFLE / Atlas encrypt-at-rest) | Commercial (Atlas) + OSS (client-side FLE) | Client-Side Field Level Encryption (OSS driver) or Atlas encrypt-at-rest/CMEK for embedded vector fields. | FLE adds app complexity; managed at-rest is paid tier. |
| **Weaviate / Qdrant** (self-host) | OSS (self-managed) + Commercial (Cloud) | OSS engines you harden yourself: TLS in transit, disk/volume encryption + CMEK on Cloud for at rest. | Encryption-at-rest depends on your infra/KMS; managed CMEK is a paid cloud feature. |
| **Pinecone** | Commercial (managed only) | Managed vector DB with encryption in transit (TLS) + at rest + RBAC and scoped API keys. | No self-host / no bring-your-own-KMS on lower tiers; embeddings leave your perimeter to vendor. |
| **Confidential Computing / TEE** (Gramine + Intel SGX, Azure Confidential, AWS Nitro) | OSS (Gramine) + Commercial (cloud) | Encrypts data **in use** — runs the embedding/query path inside an enclave so the vector store never sees plaintext in memory. | High latency/porting cost; SGX enclave sizing limits; Gramine app porting effort. |

**Note:** No single product does "encrypt embeddings everywhere." Typical stack = Tink/Vault+KMS for app-side envelope encryption + TLS transit + volume/KMS at-rest + (optional) TEE for in-use. CMEK coverage and self-host options are the main differentiators.

---

## tok_gate — Gate logprobs & internal model states (restrict raw diagnostic APIs to trusted operators)

| Candidate | Type | Fit | Gaps |
|---|---|---|---|
| **LiteLLM Proxy** | OSS + Commercial (enterprise) | Central proxy with **virtual keys**; restrict which keys/models may request `logprobs`; key-scoped access so diagnostic endpoints aren't broadly exposed. | Does not auto-strip `logprobs` from responses unless you add a callback; operator-vs-user distinction is your key design. |
| **Kong AI Gateway** | Commercial (OSS core, enterprise plugins) | Consumer auth + ACL groups + **response transformer** to strip `logprobs`/diagnostic fields; trusted-operator consumer group only. | Response-transformer config is manual; not natively LLM-diagnostic-aware. |
| **Azure API Management** | Commercial | Subscriptions + policies to transform/remove response fields and restrict diagnostic routes by subscription/role. | Config-heavy; generic (not LLM-aware); policy authoring overhead. |
| **AWS Bedrock** (IAM) | Commercial | IAM policies scope model/feature access per principal; Bedrock doesn't expose raw logprobs, reducing surface. | IAM is coarse; no fine-grained "logprobs only for operator" without separate endpoint design. |
| **vLLM** (serving) | OSS | Self-hosted OpenAI-compatible server; `--api-key` auth and you can avoid exposing logprobs endpoints to untrusted callers. | No built-in per-role policy; `unsure` whether per-key logprobs suppression is native — needs proxy/custom layer. |
| **Text Generation Inference (TGI)** | OSS | HF serving layer; configurable endpoints/features so internal states aren't exposed by default. | Operational; no native RBAC on diagnostic fields. |
| **Open Policy Agent (OPA)** | OSS (CNCF) | General **policy engine** as a sidecar/Envoy ext-authz: enforce "only `role=operator` may call `/v1/logprobs`". | Not LLM-specific; you write Rego + wire the decision into the path. |
| **Cloudflare AI Gateway** | Commercial (free tier) | API-token scopes + response transformation to drop diagnostic fields before they reach clients. | Coarse compared to OPA; response-transform rules are limited. |

**Note:** This is fundamentally an **authorization + response-hygiene** problem. Gateways (Kong, Azure APIM, CF) handle transport/auth/transform; OPA adds policy; the serving layer (vLLM/TGI) controls what's exposed; LiteLLM is the LLM-aware middle ground. None auto-classifies "internal state" — you define which fields are diagnostic.

---

## tok_rl — Rate-limit & cap (throttle token inflation / adversarial token-dense input; requests + tokens)

| Candidate | Type | Fit | Gaps |
|---|---|---|---|
| **LiteLLM Proxy** | OSS + Commercial | Per-key/user/team **rpm + tpm** limits, `max_parallel_requests` (concurrency), `max_budget`; token-aware throttling. | No native per-request "token-density" (adversarial padding) inspection; step/concurrency for *agent loops* out of scope. |
| **Kong AI Rate Limiting Advanced** | Commercial | Token-based rate limiting **partitioned by model + consumer**; tiered gold/silver/bronze quotas. | Enterprise plugin; token counting is best-effort on streaming. |
| **Cloudflare AI Gateway** | Commercial (free tier) | Fixed/sliding **rate limits** + **spend limits**; abuse prevention on token-heavy traffic. | No deep payload inspection for token-stuffing; per-tenant budgets exist but agent-step limits don't. |
| **AWS Bedrock** (service quotas) | Commercial | Model/token **quotas & throttling** per account/region; guards runaway token use. | Account/region granularity, not per-end-user without extra IAM plumbing. |
| **Azure API Management** | Commercial | Rate-limit + quota policies (requests & custom token counters) at the API edge. | Generic; needs custom policy for true token counting. |
| **Apache APISIX** | OSS | `limit-count`/`limit-req` + emerging AI plugins; token-aware throttling via custom plugins. | Token counting needs custom Lua/plugin work. |
| **Envoy + Rate Limit Service** | OSS | Global, shared rate limiting across services; can key on token estimates. | You build the token estimator + RL service; not LLM-native. |
| **vLLM / TGI** (serving) | OSS | Per-key/in-process rate limiting at the model server; bounds token throughput per caller. | `unsure` on rich per-tenant token caps; mainly protects the GPU, not end-user token inflation. |

**Note:** Gateways do requests+tokens+concurrency well. **Adversarial token-dense input** (padding to inflate cost/evade) is not directly detected by any of these — that needs a payload/length inspector (custom gateway plugin or input guardrail). Pair with `tok_gate` (strip logprobs) and a content/length pre-filter.

---

## rag_out — Output guardrail (no secret echo, cite sources, on generated RAG answers)

| Candidate | Type | Fit | Gaps |
|---|---|---|---|
| **NVIDIA NeMo Guardrails** | OSS (Apache-2.0) | Runtime rail system: **output rails** can reject/alter LLM output (e.g., remove sensitive data); Colang policies for RAG flows. | "Cite sources" not built-in — you write a rail; secret detection relies on your validators. |
| **Guardrails AI** | OSS core (Apache-2.0) + Commercial (Pro) | Composable validators: `DetectPII`, toxicity, jailbreak; re-prompt on failure; structured-output enforcement. | No native citation/source-grounding check; secret detection = PII validators only. |
| **Llama Guard** (Meta) | OSS (Llama community license) | LLM-based input/output safety classifier with customizable risk taxonomy; flags unsafe responses. | Not a secret/citation checker; needs a second model call; taxonomy tuning required. |
| **AWS Bedrock Guardrails** | Commercial | Configurable content filters, denied topics, PII redaction, **grounded-in-source** (hallucination) check on RAG answers. | Per-account; cost per 1K text units; citation enforcement is indirect. |
| **Azure AI Content Safety / Foundry Guardrails** | Commercial | Detects unsafe content, **Protected Material**, **Prompt Shields**, and **Groundedness** (answers supported by sources) — closest to "cite sources" signal. | Groundedness ≠ explicit citation; PII redaction separate; vendor lock-in. |
| **Microsoft Presidio** | OSS (Apache-2.0) | PII detection + anonymization/redaction of text (and images) — directly addresses "no secret echo." | Not an LLM guardrail; you must wire it into input/output path; no citation logic. |
| **LLM Guard** (Protect AI) | OSS (Apache-2.0) | Scanners for prompt injection, PII, secrets, toxicity on both input and output. | Secret scanning is regex/model-based; citation check not included. |
| **Rebuff** (Protect AI) | OSS | Self-hardening **prompt-injection** detector + canary-word leakage check (catches system-prompt echo). | Injection-focused; not a full output guardrail; not citation/secret-general. |
| **Lakera Guard** | Commercial | Purpose-built LLM security (prompt injection, data loss, jailbreaks) as an API. | Paid; closed; citation/PII coverage is vendor-defined. |

**Note:** "No secret echo" → Presidio / Guardrails DetectPII / LLM Guard secrets. "Cite sources / grounded" → Azure Groundedness + Bedrock grounded-in-source are the only near-native signals; true citation enforcement is usually **app-level** (assert retrieved-chunk IDs appear in output). Output-rail libs (NeMo, Guardrails) are where you compose these.

---

## governor — Runtime governor (rate, concurrency, step, token, time AND cost budgets per user/tenant for agent runs)

| Candidate | Type | Fit | Gaps |
|---|---|---|---|
| **LiteLLM Proxy** | OSS + Commercial | **Virtual keys** with `max_budget` + `budget_duration`, `rpm`/`tpm`, `max_parallel_requests`; per user/team/tenant spend & token caps. | Covers rate/token/cost/concurrency; **no agent step/iteration** limit (that's the framework's job). |
| **Portkey AI Gateway** | Commercial (OSS core) | Virtual keys with **cost-based + token-based budgets**, rate limits, RBAC/SSO, granular per-tenant governance. | Advanced budgets are Enterprise-tier; step/concurrency for agent internals not enforced. |
| **Cloudflare AI Gateway** | Commercial (free tier) | **Spend limits** (cost budgets) per user/model + rate limiting + analytics. | No step/concurrency/agent-loop governance; observability-light. |
| **Helicone** | OSS core + Commercial cloud | Cost tracking + **custom rate limits** (request-count + cost-based) per user; alerts on budget. | Docs show **token-based rate limiting "coming soon"**; no step/concurrency enforcement. |
| **LangSmith** | Commercial | Project/org **spend budgets**, tracing, alerts; good tenant-level cost visibility. | Observability, not an enforcement gateway; no step/concurrency caps; no hard rate limiting. |
| **Langfuse** | OSS (MIT) + Commercial cloud | Token & cost tracking, usage breakdowns per user/session; self-hostable. | Budget **enforcement** is limited (mostly observability/alerting); no rate/step control. |
| **AWS Bedrock** | Commercial | Per-model token quotas + guardrails; per-tenant via IAM/cross-account isolation. | No agent step limits; quota granularity is account/region, not fine user. |
| **LangGraph** | OSS | `recursion_limit` = hard **step cap** on agent graphs; human-in-the-loop interrupts. | Step/latency only; no token/cost/rate budgets (use LiteLLM/Portkey alongside). |
| **AutoGen / CrewAI** | OSS | `GroupChat(max_round=...)` / `max_iter` = **step + iteration caps** for multi-agent loops. | Framework-level only; no token/cost/rate governance. |
| **Open Policy Agent (OPA)** | OSS | Sidecar policy for **concurrency/step/quota** decisions (e.g., max N concurrent runs per tenant). | You encode and enforce; not turnkey for LLM cost. |
| **AgentOps** | Commercial (observability) | Agent tracing/cost; `unsure` whether it enforces hard budgets vs. alerts only — verify before relying on it. | `unsure` on enforcement strength. |

**Note:** No single tool is a full governor. The realistic pattern is **compose**: a gateway (LiteLLM / Portkey / CF) for rate+token+cost+concurrency **per tenant**, plus an **agent framework** (LangGraph/AutoGen/CrewAI) for step/iteration caps, plus optional OPA for cross-cutting policy. Observability (LangSmith/Langfuse/Helicone) closes the loop with alerts.

---

## Cross-cutting sources (verified)
- LiteLLM proxy budgets/rate limits: docs.litellm.ai/docs/proxy/users, /virtual_keys, /cost_tracking
- NeMo Guardrails: github.com/NVIDIA-NeMo/Guardrails; docs.nvidia.com/nemo/guardrails
- Guardrails AI: guardrailsai.com; github.com/guardrails-ai (DetectPII Apache-2.0)
- Llama Guard: ai.meta.com/research/publications/llama-guard; huggingface.co/meta-llama/Llama-Guard-3-8B
- Tink envelope encryption: developers.google.com/tink; cloud.google.com/kms/docs/client-side-encryption
- Kong AI Rate Limiting Advanced: developer.konghq.com/plugins/ai-rate-limiting-advanced
- Cloudflare AI Gateway (rate + spend limits): developers.cloudflare.com/ai-gateway
- Helicone custom rate limits: docs.helicone.ai/features/advanced-usage/custom-rate-limits
- Portkey budgets: docs.portkey.ai/docs/product/ai-gateway/virtual-keys/budget-limits
- AWS Bedrock Guardrails: docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- Azure AI Content Safety / Foundry Guardrails: azure.microsoft.com/en-us/products/ai-services/ai-content-safety
- Microsoft Presidio: microsoft.github.io/presidio
- LLM Guard / Rebuff (Protect AI): github.com/protectai/llm-guard, github.com/protectai/rebuff
- Langfuse / LangSmith cost tracking: langfuse.com/docs, langchain.com (LangSmith)
- LangGraph recursion_limit: docs.langchain.com/oss/python/langgraph; machinelearningplus.com/gen-ai/langgraph-cycles-recursion-limits
- OPA: openpolicyagent.org
- Vault Transit: developer.hashicorp.com/vault/tutorials/encryption-as-a-service/eaas-transit
- Vector DB encryption: qdrant.tech, pinecone.com docs, weaviate.io; beyondscale.tech blog (hardening)
- Confidential computing / Gramine / SGX: confidentialcomputing.io, gramine project, intel.com SGX
