# Where Private Data Actually Leaks in AI Systems — and Why "Guardrails" Diagrams Keep Missing It

*How to model the real exposure surfaces — AI analyzers, tokenization and model diagnostics, semantic search, RAG, agent tools, supply chain, and the post-usage blind spot — and why the LLM is itself a new kind of DLP.*

Most "AI security" diagrams are theater. They draw a box labeled *Guardrails* between the user and the model, slap a shield emoji on it, and call the risk closed. Then private data leaks anyway — through the vector database nobody classified as sensitive, through a third-party text-processing service nobody treated as an exposure surface, through a summarization feature that shipped SIEM logs to a third party, or through an agent that used an over-privileged tool to move the data somewhere it should never have gone.

The problem isn't that we lack controls. It's that we model the problem wrong. We treat "LLM privacy" as a single risk with a single control, when it is really five or six distinct exposure surfaces, each with its own leak mechanism, each needing its own control — and then a second layer that watches whether any of it actually held.

This is a C4 modeling problem. The C4 model (Context → Container → Component) is built for exactly this: progressively disclosing where the risk lives as you zoom in. At Component level, two complementary views make the controls concrete and checkable: one follows private data across AI surfaces; the other follows an agent action from model intent through authorization, constrained execution and audit.

---

## The four surfaces where private data leaks

### 1. AI Analyzers (Cortex-style SIEM/SOAR AI features)

These systems ingest logs, alerts, and cases that *already* contain PII, credentials, and internal topology. The AI feature's job is to summarize them. The leak is that you now ship that entire corpus to a model — frequently a third-party one — for "helpful" summarization.

- **Primary leak:** sensitive information disclosure (OWASP LLM02) — the corpus goes to the model before anyone scrubs it.
- **Secondary leak:** prompt injection (LLM01) where the injected instruction is hidden *inside a log line* that looks like routine telemetry.
- **Control pattern:** AI-DLP pre-redaction *before* egress, field-level RBAC on what the analyzer can even read, ingested-content screening for injection, output redaction before display, and a separate egress check to confirm the outbound call is actually clean.

### 2. Tokenization and model diagnostics

Tokenization and model diagnostics are related operational surfaces, but they are not the same representation. A third-party tokenizer receives the original text and can expose it through service logs or retention. Model APIs may separately expose log-probability distributions, while privileged debugging or self-hosted inference interfaces may expose internal states. Those diagnostics can reveal information about prompts and system instructions; token IDs alone are not embeddings.

- **Primary leak:** sensitive information disclosure (OWASP LLM02) from sending raw text to a third party, plus possible hidden-context exposure (LLM08) through overly permissive diagnostic interfaces.
- **Secondary leak:** unbounded consumption (LLM06) when adversarial or unusually token-dense input drives cost and latency.
- **Control pattern:** tokenize locally where possible, pre-scrub data sent to third parties, restrict diagnostic APIs to trusted operators, rate-limit by requests and tokens, and SBOM-scan tokenizer dependencies (LLM04).

### 3. Semantic Search

The received wisdom is that embeddings are "unrecognizable" vectors. The research disagrees. [Morris et al. (EMNLP 2023)](https://aclanthology.org/2023.emnlp-main.765/) recovered **92% of 32-token inputs exactly** in an embedding-inversion experiment. A separate [Cyborg demonstration](https://www.cyborg.co/blog/openclaw-do005) reported **99.38% reconstruction in under five minutes** against a production-like vector database containing synthetic sensitive data. Those results depend on the model, data and attacker access; they are evidence of risk, not a universal recovery rate. Your vector database should be classified as a sensitive store.

- **Primary leak:** LLM09 (vector/embedding weakness) plus LLM02 — stored embeddings *and* query embeddings both leak, the latter revealing searcher intent.
- **Secondary leaks:** cross-tenant vector access (LLM03), index poisoning (LLM05).
- **Control pattern:** encrypt embeddings at rest and in transit, enforce per-tenant namespace ACLs, validate/screen indexed documents, and run an *embedding-exposure detector* that flags a vector store copied to or queried from an unexpected party.

### 4. RAG

RAG has a particularly direct privacy failure mode: an over-broad retriever returns documents the user isn't authorized to see, and the model diligently includes the sensitive content in its answer. Add indirect prompt injection embedded in a retrieved document (LLM01), and the result can be data exfiltration wrapped in a helpful citation.

- **Control pattern:** doc-level *pre-retrieval* ACL (don't retrieve what the user can't see), retrieved-content injection screening, post-retrieval PII redaction, an output guardrail that refuses to echo secrets and cites sources, then egress DLP on the final answer too.

---

## When the model can act: agent tool and runtime controls

An agent changes the threat model because model output is no longer only text shown to a user. It can become a database query, Git operation, cloud API call, payment, email or shell command. Prompt injection becomes materially more dangerous when the compromised model can combine untrusted input, private data and an external communication or state-change capability.

The control boundary therefore cannot be another prompt. The application must mediate every action through deterministic components that the model cannot bypass:

1. **Build a typed action proposal.** Bind the tool, operation, resource, parameters and expected side effects to an immutable action identifier. The model never receives direct credentials.
2. **Validate and authorize the exact action.** Canonicalize parameters before an identity-, tenant-, resource- and purpose-aware policy decision. Separate read permission from write permission.
3. **Escalate risk, not prose.** Destructive, irreversible, financial, privileged and bulk-export actions go to a human approval gate that shows the exact scoped action and expiry.
4. **Constrain execution.** Issue short-lived tool- and resource-scoped credentials; enforce transaction limits, idempotency, dry-run and rollback; execute through a sandboxed tool/MCP proxy.
5. **Treat tool results as hostile input.** Validate provenance, schema and sensitive content before the result can enter the next agent step.
6. **Bound the run.** Apply rate, concurrency, step, token, time and cost budgets, plus deadlines, bounded retries, circuit breakers, safe fallback and an incident kill switch.
7. **Preserve evidence.** Record the proposal, identity, policy version, approval, attempts, side effects, result, latency, tokens and cost in an append-only trace.

This view maps primarily to the [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), especially Tool Misuse, Identity and Privilege Abuse, Unexpected Code Execution and Cascading Failures. It maps secondarily to the LLM risks that feed or amplify those failures: Prompt Injection, Sensitive Information Disclosure, Excessive Agency, Supply Chain, Unbounded Consumption and Improper Output Handling.

Mapping does not mean complete mitigation. The current component view deliberately marks partial treatment for agent goal integrity, signed and pinned tool provenance, persistent memory, agent-to-agent protocols and per-agent behavioral attestation. Those are additional architecture decisions, not labels to hide inside a generic guardrail.

---

## The layer most programs skip: supply chain

So far this is all "ingestion and runtime." But the model, embedding provider, tokenizer libraries, and RAG document loaders are themselves exposure paths — and they're the ones that survive a clean runtime.

- **Model/vendor inventory (LLM04):** know every provider, version, and data flow. You can't control what you haven't catalogued.
- **SBOM & dependency scan (LLM04):** CVE-scan libs, tokenizer deps, RAG loaders.
- **Training/pretrain PII scan (LLM04, LLM05):** detect PII or poisoned data in fine-tunes and corpora *before* it enters the model.
- **Provider config & key hygiene (LLM04, LLM08):** signed DPAs, no hard-coded keys, tenant isolation, and a kill-switch to cut a compromised provider.
- **License/provenance check (LLM04):** model and dataset license compliance and source attestation.

The supply-chain layer is what turns "we use a safe model" into "we can prove our model supply is governed."

---

## The layer that actually proves containment: post-usage alerting

Ingestion controls *reduce* risk. They do not *prove* it stayed contained. Post-usage controls close that loop, and they're the part almost everyone omits because they're not on the happy path.

- **Semantic egress DLP (LLM02):** inspects outbound prompts/completions for PII the input scrubber missed.
- **Embedding-exposure detector (LLM09):** flags vector stores or embedding logs that leaked to an untrusted party.
- **Anomaly & leak detection (LLM06, LLM02):** unusual volume, token-inflation patterns, secret regexes in outputs.
- **Drift & feedback loop (LLM07):** quality, bias, behavior-change monitoring plus user-flagged leaks feeding back into policy.
- **Audit → SIEM alerting (LLM10, LLM02):** immutable traces fan out to SOC/IR so a leak becomes an *incident*, not a footnote.
- **Red-team & review queue (LLM01):** human review of high-risk and near-miss events, including suspected injection attempts.

The point of this layer is simple: a control you can't observe failing is not a control, it's optimism.

---

## The reframe: the LLM is a new type of DLP

Here's the insight that reorganizes the whole picture: the LLM is not only a risky sink that needs DLP bolted around it. **It is also a new class of DLP** — a semantic inspector that understands natural language, so it catches leakage that regex and label-based DLP cannot: "the patient with the rare condition," a paraphrased secret, PII *described* rather than typed.

But this reframe has a non-obvious trap. The thing that leaks is the same kind of thing that can watch — so the inspector must be a **separate model instance** from the application LLM, with no shared context, credentials, or trust. Otherwise a compromised application model silently blinds its own DLP. Embedding-exposure detection should instead rely on independent vector-store access telemetry, while drift monitoring belongs in an independently operated evaluation pipeline.

Treat the LLM as a semantic DLP, not just a risky endpoint. And never let one model police itself.

---

## OWASP GenAI LLM and Agentic Top 10 2026 coverage

This maps to the [OWASP GenAI LLM Top 10 2026 source repository](https://github.com/owasp/www-project-top-10-for-large-language-model-applications), which points to the active [canonical 2026 Markdown](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/tree/main/2026/final). Earlier editions use different numbering, so the edition should always be stated explicitly. Every category is covered by at least one surface or cross-cutting control:

| OWASP 2026 | Risk | Covered by |
|---|---|---|
| LLM01 | Prompt Injection | analyzer, semantic search, RAG, red-team queue |
| LLM02 | Sensitive Information Disclosure | analyzer, diagnostics, semantic search, RAG, egress DLP |
| LLM03 | Excessive Agency | analyzer, semantic search, RAG |
| LLM04 | Supply Chain | vendor inventory, SBOM, training-PII scan, config, provenance |
| LLM05 | Data and Model Poisoning | semantic search, RAG, training-data scan |
| LLM06 | Unbounded Consumption | tokenization/model diagnostics, cross-surface anomaly detection |
| LLM07 | Misinformation | drift & feedback loop |
| LLM08 | Hidden Context Exposure | model diagnostics, RAG, provider config |
| LLM09 | Vector and Embedding Weaknesses | semantic search, RAG, embedding-exposure detector |
| LLM10 | Improper Output Handling | analyzer, RAG, SIEM alerting |

The agent tool/runtime view uses the separate Agentic Top 10 as its primary framework:

| OWASP Agentic 2026 | Risk | Main controls in the agent view | Coverage |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | constrained orchestrator, approval, untrusted-result validation | Partial |
| ASI02 | Tool Misuse & Exploitation | allowlist, parameter validation, policy decision, transaction guard, proxy | Strong |
| ASI03 | Identity & Privilege Abuse | delegation context, policy decision, scoped credential broker | Strong |
| ASI04 | Agentic Supply Chain Vulnerabilities | tool/MCP registry | Partial |
| ASI05 | Unexpected Code Execution | deterministic validation, scoped grants, sandboxed proxy | Strong |
| ASI06 | Memory & Context Poisoning | tool-result validation | Partial |
| ASI07 | Insecure Inter-Agent Communication | authenticated MCP boundary and result validation | Partial |
| ASI08 | Cascading Failures | budgets, idempotency, circuit breakers, audit and kill switch | Strong |
| ASI09 | Human-Agent Trust Exploitation | scoped proposal, risk classification, approval evidence | Moderate |
| ASI10 | Rogue Agents | audit, revocation and kill switch | Partial |

The detailed component-to-category crosswalk, including the secondary LLM mapping, is in [`05-owasp-coverage.md`](05-owasp-coverage.md).

---

## What to do Monday

1. **Stop drawing one "Guardrails" box.** Model the surfaces separately. If your diagram cannot distinguish tokenization, model diagnostics and embeddings, it is incomplete.
2. **Classify your vector database as sensitive.** Encrypt it, ACL it per tenant, and put an exposure detector on it. This is the highest-leverage, lowest-attention item on the list.
3. **Add the post-usage layer before you add more ingestion controls.** You already have input scrubbing. What you don't have is proof it worked.
4. **Put every agent action behind a non-bypassable tool proxy.** The model should hold neither direct credentials nor a direct network path to tools. Bind authorization, approval, budgets and execution to the same immutable action identifier.
5. **Deploy your semantic DLP as a separate instance.** Same model family, different trust boundary, no shared context.
6. **Pull both applicable OWASP 2026 lists into your threat model.** Use the LLM Top 10 for model/data risks and the Agentic Top 10 for autonomous action risks; check each mapping against a real component, not a shield emoji.

The diagrams that accompany this article—C4 Context, Container, lifecycle Component, private-data exposure, and agent tool/runtime views—are on GitHub under `llm-c4-controls`. The lesson they encode is the same one a flat "guardrails" diagram hides: private data in AI does not leak in one place. It can leak in the analyzer, a third-party text processor, the vector store, the retriever or the provider; an over-privileged agent can then turn that exposure into an external action; and an unobserved failure can survive long after the request completed.
