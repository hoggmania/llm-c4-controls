# AI-Data-Security Control — Candidate Tool Matrix

Research of OSS + commercial tools that can *implement* each control in the C4 architecture.
Tag key: **OSS** = open-source/ open-weight, **Commercial** = closed/paid SaaS or licensed.
"Semantic" = LLM/regex-blind detection (catches "the patient with the rare condition"); "Classic" = PII/secret DLP via regex/NER/dictionaries.

---

## an_dlp — Pre-redaction scrubber (remove PII before logs/alerts/cases egress to LLM summarizer)

| Candidate | Tag | Capability fit | Gap / uncertainty |
|---|---|---|---|
| Microsoft Presidio | OSS | Context-aware PII detection + Anonymizer (replace/mask/hash/filter) for text & images; self-hostable, no data egress. Canonical fit. | Misses novel/semantic PII; needs recognizer tuning + NLP models (e.g. GLiNER/Transformers). |
| Google Cloud DLP / Sensitive Data Protection | Commercial | DLP API de-identification transforms (mask, crypto-hash, redact) over text, structured, and Cloud Storage; inspect+deidentify. | Cloud-bound; data leaves perimeter unless VPC-SC — conflicts with no-egress goal. Per-MB pricing. |
| Azure AI Language — PII | Commercial | Detect/classify/redact PII entities in raw text; redacts all detected entities. | Sends text to Azure; data-residency to consider. |
| Amazon Comprehend PII | Commercial | ML-based PII detection returning a redacted copy of text; native AWS integration. | AWS-bound; not on-prem without heavy infra. |
| Private AI (Limina) | Commercial | De-identification API/container, 52 languages, synthetic replacement, on-prem deployable. | License cost; exact on-prem container terms unverified. |
| Nightfall AI | Commercial | Developer DLP API redacts PII in ~4 lines; broad SaaS DLP. | SaaS egress model defeats keeping data in-house; best for SaaS surfaces, not inline local scrub. |
| Microsoft Purview DLP | Commercial | Policy-based DLP extended to M365 Copilot; broad enterprise coverage. | Heavyweight; more policy enforcement than inline API redaction of arbitrary log text. |

---

## tok_scrub — Pre-scrub PII before sending text to a third-party tokenizer/diagnostics API

| Candidate | Tag | Capability fit | Gap / uncertainty |
|---|---|---|---|
| Microsoft Presidio | OSS | Self-hosted, zero data egress — tokenizer API never sees raw PII. Ideal. | Needs infra; entity coverage depends on recognizers. |
| Private AI | Commercial | On-prem container; synthetic replacement preserves token-stream utility. | Cost; streaming latency for tokenizer unverified. |
| scrubadub | OSS | Lightweight Python lib scrubbing emails/phones/names from free text; trivial inline use. | Limited entities (regex/basic NER); not PHI-grade. |
| Faker (synthetic) | OSS | Generate realistic synthetic stand-ins to feed tokenizer. | Not a detector — pair with Presidio for detect→replace. |
| Azure AI Language PII | Commercial | API redaction. | Egress concern — partially defeats the purpose if the tokenizer is the worry. |
| Google Cloud DLP | Commercial | De-id transforms. | Same egress conflict. |

---

## rag_red — Post-retrieval PII redaction (scrub sensitive spans from retrieved RAG documents)

| Candidate | Tag | Capability fit | Gap / uncertainty |
|---|---|---|---|
| Microsoft Presidio | OSS | Per-chunk redaction before prompt injection; text + image. | Retrieval-scale latency; misses semantic leakage across chunks. |
| Private AI | Commercial | On-prem, multi-language, synthetic replacement keeps chunk coherence. | Cost. |
| Google Cloud DLP / SDP | Commercial | Inspect+deidentify retrieved docs. | Cloud egress per query. |
| Amazon Comprehend | Commercial | Redacted-copy API. | AWS egress. |
| Azure AI Language PII | Commercial | Redact entities. | Azure egress. |
| Nightfall | Commercial | API redaction. | SaaS egress. |
| Llama Guard (semantic) | OSS | Can flag PII/secrets in retrieved context. | Built as a safety classifier, not a redactor; would need to drive masking. PII coverage unverified. |

---

## an_out — Output filter/redactor (redact generated summary before analyst views it)

| Candidate | Tag | Capability fit | Gap / uncertainty |
|---|---|---|---|
| Azure OpenAI Content Filter (Personal Information filter) | Commercial | Scans LLM output to identify/flag known PII. | "Flag" ≠ always "redact"; tied to Azure OpenAI; defined entity types only. |
| OpenAI Privacy Filter | OSS / Open-weight | Open-weight model for detecting & redacting PII in text (released 2025). Strong candidate. | New; license/on-prem viability to verify. |
| Private AI | Commercial | De-identify generated summaries; on-prem. | Cost. |
| Microsoft Presidio | OSS | Post-generation redaction of summaries. | Misses semantic leakage. |
| GuardrailsAI (Output Guards) | OSS | Validators (PII, regex) on LLM output; OnFailAction=redact. | Redaction depends on underlying detectors. |
| NeMo Guardrails (output rails) | OSS | Output moderation rails. | More safety/topic than PII; PII coverage limited. |
| Llama Guard | OSS | Input-output safeguard; classifies unsafe output. | Safety taxonomy, not a redactor; partial. |

---

## post_dlp — Semantic (LLM-based) egress DLP inspector (catches regex-missed leakage; separate instance from app LLM)

| Candidate | Tag | Capability fit | Gap / uncertainty |
|---|---|---|---|
| Llama Guard 3/4 | OSS | LLM classifier for input/output safety incl. PII/secret-ish categories; can run as a separate inspector model. | Safety taxonomy, not a full PII/secret detector; needs prompt tuning for implied-leakage ("rare condition"). |
| OpenAI Privacy Filter | OSS / Open-weight | Purpose-built open model to detect/redact PII in text; good inspector candidate. | New; license terms to verify; secret/credential coverage unclear. |
| Azure AI Content Safety (PII filter) | Commercial | Inspect outbound completions for PII. | Cloud egress; defined entity types only. |
| Lakera Guard | Commercial | Real-time API against data leakage, prompt injection, jailbreaks for LLM apps; strong *semantic* detection. | Black-box SaaS; cost; content egress to Lakera. |
| NeMo Guardrails (input/output rails) | OSS | Configurable rails; can host a separate inspector. | PII/secret leakage not first-class; needs custom rails. |
| Private AI | Commercial | Semantic de-id with context; on-prem. | Cost; semantic coverage of *implied* PII unclear. |
| GuardrailsAI | OSS | Output validators incl. PII + custom LLM-based checks; can run as separate inspector. | Turnkey semantic check must be defined by you. |
| PromptGuard / Rebuff | OSS | Prompt-injection / jailbreak detection. | **Gap:** miscast as DLP — they catch injection, NOT PII/secret semantic leakage. Exclude for this control. |

---

## Cross-cutting notes
- **Classic vs semantic split:** Presidio, Google DLP, Azure/Comprehend PII, Nightfall, Purview = classic PII/secret DLP (regex/NER/dictionaries). They will *miss* the "patient with the rare condition" style leakage that only `post_dlp` (LLM inspector) targets.
- **No-egress requirement:** For `an_dlp`/`tok_scrub` the self-hostable options (Presidio, Private AI on-prem, scrubadub, OpenAI Privacy Filter) are the only ones that don't contradict the data-residency goal; cloud APIs (Google/Azure/AWS/Nightfall) require egress waivers or VPC-SC.
- **Uncertainties flagged:** OpenAI Privacy Filter license/on-prem status, Private AI on-prem container terms, Llama Guard exact PII/secret coverage, Lakera pricing/egress. Verify before procurement.
