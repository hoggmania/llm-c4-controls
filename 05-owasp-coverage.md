# OWASP GenAI LLM Top 10 2026 — Private-Data Exposure Coverage Matrix

Maps the [OWASP GenAI LLM Top 10 2026](https://github.com/owasp/www-project-top-10-for-large-language-model-applications)
to the four AI surfaces plus the Supply Chain and Post-Usage Alerting layers from
`04-data-exposure-controls.puml`. Earlier editions use different
numbering, so mappings must identify their edition explicitly. OWASP now maintains the
[canonical 2026 Markdown](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/tree/main/2026/final)
in its active source repository.

| OWASP 2026 | Risk | Surfaces where it bites | Controls in the diagram |
|---|---|---|---|
| **LLM01** | Prompt Injection | Analyzer, Semantic Search, RAG, Red-team queue | `an_inj`, `ss_val`, `rag_scr`, `post_rt` |
| **LLM02** | Sensitive Information Disclosure | Analyzer, Model diagnostics, Semantic Search, RAG, Post-usage | `an_dlp`/`an_out`, `tok_scrub`/`tok_gate`, `ss_enc`, `rag_acl`/`rag_red`, `post_dlp`, `post_anom` |
| **LLM03** | Excessive Agency | Analyzer, Semantic Search, RAG | `an_rbac`, `ss_acl`, `rag_acl` |
| **LLM04** | Supply Chain | All surfaces depend on models, libraries, providers or data | `sc_inv`, `sc_sbom`, `sc_train`, `sc_cfg`, `sc_lic` |
| **LLM05** | Data and Model Poisoning | Semantic Search, RAG, Training data | `ss_val`, `rag_scr`, `sc_train` |
| **LLM06** | Unbounded Consumption | Tokenization/model diagnostics and cross-surface usage | `tok_rl`, `post_anom` |
| **LLM07** | Misinformation | User-facing model outputs | `post_drift` (eval/feedback) |
| **LLM08** | Hidden Context Exposure | Model diagnostics, RAG, Provider config | `tok_gate`, `rag_out`, `sc_cfg` |
| **LLM09** | Vector and Embedding Weaknesses | Semantic Search, RAG, Emb-exposure detector | `ss_enc`, `ss_acl`, `rag_acl`, `post_emb` |
| **LLM10** | Improper Output Handling | Analyzer, RAG, SIEM alerting | `an_out`, `rag_out`, `post_alert` |

## Surface-specific exposure notes

### AI Analyzer / Cortex-style (SIEM/SOAR AI features)
- Ingests logs/alerts/cases already containing PII, credentials, internal topology.
- *Primary leak:* shipping that corpus to an LLM for summarization (LLM02) + injected
  instructions hidden in log lines (LLM01).
- *Control pattern:* AI-DLP scrub **before** egress, field-level RBAC, injected-content
  screening, output redaction, then **egress DLP re-verifies** the outbound call.

### Tokenization and model diagnostics
- *Primary leak:* a third-party tokenization service receives the original text, while model
  diagnostics such as log-probability distributions or internal states can reveal information
  about prompts and system instructions (LLM02, LLM08). Token IDs alone are not embeddings.
- *Secondary:* adversarial or unusually token-dense input can drive cost and latency (LLM06).
- *Control pattern:* tokenize locally where possible, pre-scrub data sent to third parties,
  restrict diagnostic APIs to trusted operators, and rate-limit by both requests and tokens.
  SBOM scanning covers the tokenizer library itself (LLM04).

### Semantic Search
- *Primary leak:* embeddings are more reversible than people assume. [Morris et al.](https://aclanthology.org/2023.emnlp-main.765/)
  recovered 92% of 32-token inputs exactly in an embedding-inversion experiment; a separate
  [Cyborg demonstration](https://www.cyborg.co/blog/openclaw-do005) reported 99.38%
  reconstruction against a production-like VDB. These results
  are environment-specific rather than universal guarantees. Query embeddings can also reveal
  searcher intent (LLM09, LLM02).
- *Secondary:* cross-tenant vector access (LLM03), index poisoning (LLM05).
- *Control pattern:* treat the VDB as a sensitive store (encrypt at rest/in transit), per-tenant
  namespace ACLs, validate/screen indexed documents, and run an **embedding-exposure detector**
  that flags a vector store copied to / queried from an unexpected party.

### RAG
- *Primary leak:* over-broad retriever returns docs the user isn't authorized to see, and the
  model faithfully includes PII in the answer (LLM02 + LLM03). Indirect prompt injection via
  retrieved docs is the most-exploited RAG failure (LLM01).
- *Control pattern:* doc-level pre-retrieval ACL, retrieved-content injection screening,
  post-retrieval PII redaction, output guardrail (no-secret echo, cite sources), then
  **egress DLP** verifies the final answer too.

## Supply Chain & Vulnerability layer (NEW)
Not just ingestion — the model, embedding provider, tokenizer libraries, and RAG document
loaders are themselves exposure paths.
- `sc_inv` Model/Vendor Inventory: know every provider, version, and data flow (LLM04).
- `sc_sbom` SBOM & Dependency Scan: CVE scan of libs, tokenizer deps, RAG loaders (LLM04).
- `sc_train` Training/Pretrain PII Scan: detect PII or poisoned data in fine-tune/corpus
  before it enters the model (LLM04, LLM05).
- `sc_cfg` Provider Config & Key Hygiene: signed DPAs, no hard-coded keys, tenant isolation,
  and a kill-switch to cut a compromised provider (LLM04, LLM08).
- `sc_lic` License / Provenance Check: model & dataset license compliance and source
  attestation (LLM04).

## Post-Usage Detection & Alerting layer (NEW — the part most programs skip)
Ingestion controls reduce risk; they do not prove it stayed contained. Post-usage controls
close the loop:
- `post_dlp` Egress DLP Monitor: inspects outbound prompts/completions for PII the input
  scrubber may have missed (LLM02). Cross-linked to `an_dlp` and `rag_out` for verification.
- `post_emb` Embedding-exposure Detector: flags vector stores or embedding logs that have been
  copied to / queried from an untrusted party (LLM09).
- `post_anom` Anomaly & Leak Detection: unusual volume, token-inflation patterns, secret regex
  appearing in outputs (LLM06, LLM02).
- `post_drift` Drift & Feedback Loop: quality, bias, and behavior-change monitoring plus
  user-flagged leaks feed back into policy (LLM07).
- `post_alert` Audit -> SIEM Alerting: immutable traces fan out to SOC/IR so a leak becomes an
  incident, not a footnote (LLM10, LLM02).
- `post_rt` Red-team & Review Queue: human review of high-risk / near-miss events, including
  suspected prompt-injection attempts (LLM01).

## LLM as a new type of DLP (paradigm reframe)
The LLM is not only a risky sink that needs DLP bolted around it — it is also a
*new class of DLP*: a semantic inspector that understands natural language, so it
catches leakage regex/label-based DLP cannot ("the patient with the rare condition",
a paraphrased secret, PII described rather than typed). Operationalize it as:
- Deploy the inspector as a **separate model instance** from the app LLM, with no
  shared context, credentials, or trust — otherwise a compromised app model silently
  blinds its own DLP (`post_dlp` follows this pattern).
- Use semantic inspection where language understanding adds value: `an_inj`/`rag_scr`
  screen for injected instructions and `post_dlp` evaluates outputs. Use conventional
  access telemetry to detect vector-store exposure (`post_emb`) and an independent eval
  pipeline to flag behavior change (`post_drift`).
- Do not rely on a single LLM to police itself. Separation of duties + immutable
  audit (`post_alert`) is what turns "semantic DLP" into a control rather than a hope.

## Open gaps / decisions
- **LLM07 (Misinformation)** has no point control — it is governed by `post_drift`, not a per-
  request filter. Confirm that's acceptable vs. adding an inline confidence/source check.
- **2023–24 vs 2026** numbering differs (2023–24 LLM06 = Sensitive Information Disclosure,
  now LLM02; 2023–24 LLM08 = Excessive Agency, now LLM03). Confirm which edition your
  audience expects before publishing and label it explicitly.
- Consider whether the post-usage layer should also emit **user-facing incident comms** (DSAR /
  breach-notification triggers) — that's a governance handoff, not a component, so it's left
  out of the architecture view intentionally.
