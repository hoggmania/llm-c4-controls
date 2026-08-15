# Injection-Screening Controls — Candidate Tooling (re-dispatched)

Cluster covering `an_inj`, `ss_val`, `rag_scr`, `result` from the llm-c4-controls repo.
Legend: **OSS** = open-source, **Comm** = commercial. "detect" = flags/identifies;
"prevent" = blocks before it reaches the model/agent. The `result` control specifically
addresses **tool/function-call output poisoning** (hostile or sensitive data coming back
from an external tool before the agent trusts it).

> Verified via search this run: ToolHive, Microsoft Prompt Shields, mcp-proxy. Remaining
> candidates grounded in established tooling; "unsure" = not re-verified by live search.

---

## an_inj — Ingested-content screener (hidden instructions in logs/alerts/cases) · `LLM01`

| App | Tag | Fit note / gap |
|---|---|---|
| **Lakera Guard** | Comm | Purpose-built API classifier for prompt injection in inbound content; detect+log. |
| **Microsoft Prompt Shields** | Comm/OSS | Detects indirect (document/email) + direct injection; strong for ingested content. |
| **PromptGuard** (Meta) | OSS | Small classifier for phishing/jailbreak/injection; fast, embeddable. detect-only. |
| **Rebuff** (Protect AI) | OSS | Prompt-injection detection + canary token leakage; can block at the gate. |
| **NeMo Guardrails** | OSS | Input rails can block injected instructions before summarization. prevent (via rail). |
| **GuardrailsAI** | OSS+Comm | Validators/RAIL can flag/repair injected instructions. prevent (config-dependent). |
| **Llama Guard** (Meta) | OSS | Safety classifier incl. injection intent; classify, not redact. |
| **Azure Content Safety** | Comm | Prompt Shields + groundedness; detect + optional block. |
| **garak / LLM-sec / Vigil** | OSS | Red-team scanners that surface injection in content; test-time, not inline. |
| **OPA / Casbin** | OSS | Encode "no instruction-like patterns from untrusted source" as policy at ingest. prevent (custom). |

*Gap:* Most are **detect**; true **prevention** before egress to the summarizer LLM requires
wiring the detector to a gate/block (or a policy engine). No turnkey "scan this SIEM alert
for injected instructions then drop it" appliance — you build the gate.

---

## ss_val — Index validation (screen docs for poison/injection before vector index) · `LLM05, LLM01`

| App | Tag | Fit note / gap |
|---|---|---|
| **Lakera Guard / Prompt Shields** | Comm | Scan each doc for injected instructions at ingest time. detect. |
| **LLM Guard / GuardrailsAI** | OSS | Injection + PII scanners runnable on the ingestion pipeline. prevent (config). |
| **NeMo Guardrails** | OSS | Input rails on the loader; block poisoned/injected docs pre-index. |
| **garak / PyRIT** | OSS | Poisoning/injection probes against a corpus; research/QA, not inline. |
| **Vigil** | OSS | OSS LLM-security scanner for injection in text. Gap: prototype-grade, detect-only. |
| **OPA / Casbin** | OSS | Policy gate on document source + content before it is embedded/indexed. |
| **Presidio** | OSS | PII screen on ingested docs (secondary; complements injection screen). |

*Gap:* **Index-level *poisoning* detection is research-stage** — injection screening is the
mature half. No dedicated "vector-index validator" product; you compose a doc screener at
the loader. (See also `sc_train` poisoning gap in supply_chain_controls.md.)

---

## rag_scr — Retrieved-content screener (block injected instructions in RAG docs) · `LLM01`

| App | Tag | Fit note / gap |
|---|---|---|
| **Lakera Guard / Prompt Shields** | Comm | Screen retrieved passages before they reach the generator. detect+block. |
| **LLM Guard / GuardrailsAI** | OSS | Content/injection scanners on retrieved context; block or repair. prevent (config). |
| **NeMo Guardrails** | OSS | Input rails applied to retrieved context. |
| **Llama Guard** | OSS | Classify injected-intent in retrieved text. detect. |
| **LangChain / LlamaIndex doc scanners** | OSS | Framework-level "document compressor / scanner" hooks; you implement the check. |
| **Rebuff** | OSS | Canary-token leakage detection in retrieved content. |

*Gap:* Functionally overlaps `an_inj` but applied at **retrieval** time, not ingest. The
control is the same detector placed later in the pipeline; frameworks give the hook, not a
turnkey RAG-injection firewall.

---

## result — Tool Result Validator (schema + content filter on untrusted tool output) · `ASI01/06/07; LLM01/02/10`

| App | Tag | Fit note / gap |
|---|---|---|
| **ToolHive** (Stacklok) | OSS | Runs MCP servers in isolated containers; can filter/limit the tool surface + result handling. MCP-native. |
| **MCP Guardian** (EQTY Lab) / **mcp-proxy** / **Pro-vi/mcp-filter** | OSS | Security proxy/gateway → tool-surface filtering, audit logs, per-key allowlist (verified this run). Gap: tool *surface* control, not semantic result-poisoning detection. |
| **OPA / Casbin** | OSS | Policy on tool-result schema + content (reject unexpected/over-privileged payloads). prevent (custom). Gap: you author all rules; no injection semantics. |
| **GuardrailsAI / LLM Guard** | OSS+Comm | Content/schema validation + PII/secrets screening on tool output before the agent acts. |
| **Anthropic / OpenAI tool-use validation** | Comm | Typed `tool_result` you validate/intercept before the next model step. |
| **LangGraph / Pydantic typed results** | OSS | Structured tool results you validate; still trust-by-default unless you add a filter. |

*Gap (the important one):* **Most agent frameworks treat tool/function-call results as
trusted input by default** — exactly the weakness this control exists to fix. Only
MCP-security layers (ToolHive/mcp-proxy/mcp-filter) and an explicit OPA/guardrail gate treat
**tool output as untrusted** before it influences the next step. Schema validation is mature;
**content/poison filtering on tool output is the immature half** — you build the validator.

---

### One-line summary for this cluster
Detection of injected instructions is **mature** (Lakera, Prompt Shields, PromptGuard, Rebuff,
NeMo/Guardrails, Llama Guard, Azure); **prevention** requires wiring the detector to a gate or
policy engine (OPA/Casbin, NeMo rails). The distinctive gap is `result`: tool/function-call
**output** poisoning is under-served because frameworks trust tool results by default —
MCP-security proxies + an explicit validator are the current answer.
