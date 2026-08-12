# OWASP GenAI LLM Top 10 (2026) — Private-Data Exposure Coverage Matrix

Maps the current OWASP list (published 2026-08-03) to the four AI surfaces plus the
Supply Chain and Post-Usage Alerting layers from `04-data-exposure-controls.puml`.
The 2023 edition is legacy and renumbered — do not mix them.

| OWASP 2026 | Risk | Surfaces where it bites | Controls in the diagram |
|---|---|---|---|
| **LLM01** | Prompt Injection | Analyzer, Semantic Search, RAG, Red-team queue | `an_inj`, `ss_val`, `rag_scr`, `post_rt` |
| **LLM02** | Sensitive Information Disclosure | **ALL** — core private-data leak | `an_dlp`/`an_out`, `tok_scrub`, `ss_enc`, `rag_acl`/`rag_red`, `post_dlp`, `post_anom` |
| **LLM03** | Supply Chain Vulnerabilities | **ALL** (vendor/libs/data) | `sc_inv`, `sc_sbom`, `sc_train`, `sc_cfg`, `sc_lic` |
| **LLM04** | Data & Model Poisoning | Semantic Search, RAG, Training data | `ss_val`, `rag_scr`, `sc_train` |
| **LLM05** | Improper Output Handling | Analyzer, RAG, Semantic Search, SIEM alerting | `an_out`, `rag_out`, `post_alert` |
| **LLM06** | Excessive Agency / Permissions | Analyzer, Semantic Search, RAG | `an_rbac`, `ss_acl`, `rag_acl` |
| **LLM07** | System Prompt Leakage | Analyzer, RAG, Provider config | `rag_out`, `sc_cfg` |
| **LLM08** | Vector & Embedding Weaknesses | Tokenizer, Semantic Search, RAG, Emb-exposure detector | `tok_gate`, `ss_enc`, `ss_acl`, `post_emb` |
| **LLM09** | Misinformation | **ALL** — hallucinated private claims | `post_drift` (eval/feedback) |
| **LLM10** | Unbounded Consumption | Analyzer, Tokenizer, Semantic Search, RAG | `tok_rl`, `post_anom` |

## Surface-specific exposure notes

### AI Analyzer / Cortex-style (SIEM/SOAR AI features)
- Ingests logs/alerts/cases already containing PII, credentials, internal topology.
- *Primary leak:* shipping that corpus to an LLM for summarization (LLM02) + injected
  instructions hidden in log lines (LLM01).
- *Control pattern:* AI-DLP scrub **before** egress, field-level RBAC, injected-content
  screening, output redaction, then **egress DLP re-verifies** the outbound call.

### Tokenizers
- *Primary leak:* token / logprob / hidden-state APIs let an attacker invert text back out
  (Morris et al. 2023 recovered 92% of a 32-token string; this is LLM08, not just LLM02).
- *Secondary:* token-inflation (homoglyphs, weird unicode) blows up cost/latency (LLM10).
- *Control pattern:* never expose raw logprobs/hidden states to untrusted callers, rate-limit
  token endpoints, pre-scrub PII before any third-party tokenizer. SBOM scan covers the
  tokenizer library itself (LLM03).

### Semantic Search
- *Primary leak:* embeddings are more reversible than people assume — embedding-inversion
  attacks reconstruct plaintext from stored vectors (Cyborg reports 99.38% on a production-like
  VDB). Query embeddings also reveal searcher intent (LLM08, LLM02).
- *Secondary:* cross-tenant vector access (LLM06), index poisoning (LLM04).
- *Control pattern:* treat the VDB as a sensitive store (encrypt at rest/in transit), per-tenant
  namespace ACLs, validate/screen indexed documents, and run an **embedding-exposure detector**
  that flags a vector store copied to / queried from an unexpected party.

### RAG
- *Primary leak:* over-broad retriever returns docs the user isn't authorized to see, and the
  model faithfully includes PII in the answer (LLM02 + LLM06). Indirect prompt injection via
  retrieved docs is the most-exploited RAG failure (LLM01).
- *Control pattern:* doc-level pre-retrieval ACL, retrieved-content injection screening,
  post-retrieval PII redaction, output guardrail (no-secret echo, cite sources), then
  **egress DLP** verifies the final answer too.

## Supply Chain & Vulnerability layer (NEW)
Not just ingestion — the model, embedding provider, tokenizer libraries, and RAG document
loaders are themselves exposure paths.
- `sc_inv` Model/Vendor Inventory: know every provider, version, and data flow (LLM03).
- `sc_sbom` SBOM & Dependency Scan: CVE scan of libs, tokenizer deps, RAG loaders (LLM03).
- `sc_train` Training/Pretrain PII Scan: detect PII or poisoned data in fine-tune/corpus
  before it enters the model (LLM03, LLM04).
- `sc_cfg` Provider Config & Key Hygiene: signed DPAs, no hard-coded keys, tenant isolation,
  and a kill-switch to cut a compromised provider (LLM03, LLM07).
- `sc_lic` License / Provenance Check: model & dataset license compliance and source
  attestation (LLM03).

## Post-Usage Detection & Alerting layer (NEW — the part most programs skip)
Ingestion controls reduce risk; they do not prove it stayed contained. Post-usage controls
close the loop:
- `post_dlp` Egress DLP Monitor: inspects outbound prompts/completions for PII the input
  scrubber may have missed (LLM02). Cross-linked to `an_dlp` and `rag_out` for verification.
- `post_emb` Embedding-exposure Detector: flags vector stores or embedding logs that have been
  copied to / queried from an untrusted party (LLM08).
- `post_anom` Anomaly & Leak Detection: unusual volume, token-inflation patterns, secret regex
  appearing in outputs (LLM10, LLM02).
- `post_drift` Drift & Feedback Loop: quality, bias, and behavior-change monitoring plus
  user-flagged leaks feed back into policy (LLM09).
- `post_alert` Audit -> SIEM Alerting: immutable traces fan out to SOC/IR so a leak becomes an
  incident, not a footnote (LLM05, LLM02).
- `post_rt` Red-team & Review Queue: human review of high-risk / near-miss events, including
  suspected prompt-injection attempts (LLM01).

## LLM as a new type of DLP (paradigm reframe)
The LLM is not only a risky sink that needs DLP bolted around it — it is also a
*new class of DLP*: a semantic inspector that understands natural language, so it
catches leakage regex/label-based DLP cannot ("the patient with the rare condition",
a paraphrased secret, PII described rather than typed). Operationalize it as:
- Deploy the inspector as a **separate model instance** from the app LLM, with no
  shared context, credentials, or trust — otherwise a compromised app model silently
  blinds its own DLP (`post_dlp`, `post_emb`, `post_anom` follow this pattern).
- Use the same semantic-inspection power at every layer: `an_inj`/`rag_scr` screen for
  injected instructions, `post_emb` detects embedding inversion, `post_drift` flags
  behavior change. The model that leaks is also the model that can watch.
- Do not rely on a single LLM to police itself. Separation of duties + immutable
  audit (`post_alert`) is what turns "semantic DLP" into a control rather than a hope.

## Open gaps / decisions
- **LLM09 (Misinformation)** has no point control — it is governed by `post_drift`, not a per-
  request filter. Confirm that's acceptable vs. adding an inline confidence/source check.
- **2023 vs 2026** numbering differs (2023 LLM06 = Sensitive Information Disclosure, now
  LLM02; 2023 LLM08 = Excessive Agency). Confirm which edition your audience expects before
  publishing. Post-usage alerting maps cleanly to either edition.
- Consider whether the post-usage layer should also emit **user-facing incident comms** (DSAR /
  breach-notification triggers) — that's a governance handoff, not a component, so it's left
  out of the architecture view intentionally.
