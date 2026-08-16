# AI Post-Usage Detection / Alerting / Feedback — Candidate Tools by Control

Research into OSS + commercial tools that can **implement** the four post-usage controls. Each control lists 3–8 candidates with license type, a one-line fit note, and gaps. Maturity flags: **Mature** (production-proven), **Nascent** (early/partial), **Custom** (build-your-own). "unsure" marks claims I could not independently verify.

---

## post_emb — Embedding-Exposure Detector
*Flags a vector store / embedding logs copied to or queried from an unexpected/untrusted party.*

**Maturity: Nascent → effectively a Custom / build-your-own control.** No turnkey "embedding-exfiltration-to-untrusted-party" product exists; the space is dominated by infra-posture scanners and manual audit logging. Treat this as the gap to engineer.

| Candidate | OSS / Commercial | Fit note | Gaps |
|---|---|---|---|
| **Custom embedding-access & egress monitor** (build: query-log audit + egress DLP on vector endpoints) | Build | The only way to actually flag *who* queried/copied embeddings and whether the party is out-of-policy | Fully bespoke; needs instrumentation at retrieval + network egress layer |
| **Orca Security** (cloud security platform) | Commercial | Agentless detection of **publicly-exposed / unauthenticated vector DB instances** across cloud | Detects misconfig exposure, not query-level exfil to a specific untrusted party |
| **CSPM for vector stores** (Wiz, Lacework, Prisma Cloud) | Commercial | Finds internet-exposed vector DBs, missing auth, lateral-movement risk | Infra posture only; no semantic "untrusted party" scoring |
| **Vector DB native audit/RBAC** (Pinecone, Weaviate, Milvus, pgvector) | Commercial / OSS | API keys, RBAC, per-namespace audit logs can surface anomalous query volume per caller | No built-in trust-party detection; partial, manual correlation needed |
| **Langfuse / LangSmith retrieval-span logging** | OSS / Commercial | Trace which embeddings were retrieved by which user/session; can alert on anomalous retrieval | Not purpose-built for exposure; no party-trust classification |

---

## post_anom — Anomaly & Leak Detection
*Unusual volume, token-inflation patterns, secret regex appearing in outputs.*

**Maturity: Mature** for token-volume/observability (LLM ops tools, APM) and for secret scanning (DLP/scanners); combining them into one pipeline is the integration work.

| Candidate | OSS / Commercial | Fit note | Gaps |
|---|---|---|---|
| **LangSmith** (LangChain) | Commercial (free tier) | Tracing + monitoring: token/cost volume, error rates, custom eval alerts | No native secret-leak regex on outputs; secret scanning must be added |
| **Langfuse** | OSS + Cloud | Hierarchical traces w/ token usage, cost, latency; custom metadata + dashboards for volume anomaly | Secret/output-leak detection not built in |
| **Helicone** | OSS + Cloud | AI-gateway proxy: logs every call, cost/token analytics, rate-limit & anomaly alerts | No secret/content DLP; observability only |
| **AgentOps** | OSS SDK + Cloud | Agent session replay + metrics; good for per-agent token-volume spikes | Light on secret-leak and content scanning |
| **Datadog LLM Observability** | Commercial | Anomaly monitors on token/log volume; ties to full APM + alerts | Secret-in-output detection needs custom pipeline |
| **Splunk / Elastic ML** | Commercial (Elastic core OSS-leaning) | ML anomaly detection on log volume; Splunk has end-to-end LLM observability patterns | Generic; secret-regex in LLM output needs custom correlation |
| **Nightfall AI** | Commercial | DLP that detects secrets, PII, credentials **in LLM prompts/outputs** and blocks exfil | Focused on content; not a token-volume anomaly tool |
| **TruffleHog / GitGuardian / detect-secrets** | OSS / Commercial | Mature secret-regex + active-verification scanners; can run on captured outputs | Built for code repos, not streaming LLM output by default (needs wiring) |

---

## post_drift — Drift & Feedback Loop
*Quality, bias, behavior-change monitoring; user-flagged leaks feed back into policy.*

**Maturity: Mature** for ML/LLM drift & eval (Evidently, Deepchecks, Giskard, Arize, Fiddler, Arthur); the *feedback-into-policy* loop is best closed via observability platforms' score/annotation features.

| Candidate | OSS / Commercial | Fit note | Gaps |
|---|---|---|---|
| **Evidently** | OSS + Cloud | Drift detection (data/LLM quality), RAG/chatbot eval from dev→prod | Feedback-to-policy loop is manual; needs your orchestration |
| **Deepchecks** | OSS + Commercial | LLM & ML evaluation suites, drift/quality tests | Sensitive to setup; production monitoring tier is commercial |
| **Giskard** | OSS + Commercial | LLM/ML testing incl. bias, robustness, RAG evaluation | Bias/behavior monitoring in prod needs integration |
| **Arize Phoenix** | OSS (Phoenix) / Commercial (Arize) | OpenInference tracing + LLM-as-judge eval; OSS is offline workbench, online monitoring is paid | Online drift monitoring requires upgrade to SaaS |
| **WhyLabs** (WhyLogs OSS) | Commercial (WhyLogs OSS) | LLM/ML observability, drift & data-quality monitoring at scale | WhyLogs is OSS; managed platform is commercial |
| **Arthur** | Commercial | Real-time perf monitoring, drift, bias/fairness, hallucination detection | Closed source; cost/lock-in |
| **Fiddler** | Commercial | LLM observability: hallucination, safety, PII, correctness monitoring | Commercial; no OSS core |
| **Langfuse feedback scores** | OSS + Cloud | User-flagged feedback scores + human review feed directly into eval datasets | Drift statistics lighter than dedicated ML-monitoring tools |

---

## post_rt — Red-Team & Review Queue
*Human review workflow for high-risk / near-miss events incl. suspected prompt-injection attempts.*

**Maturity: Mature** for automated red-team scanning (garak, PyRIT, Promptfoo, CyberSecEval) and for prompt-injection guardrails (Lakera); **Nascent** for a unified human review *queue* purpose-built for AI incidents (mostly assembled from LangSmith/Langfuse annotation queues + ticketing).

| Candidate | OSS / Commercial | Fit note | Gaps |
|---|---|---|---|
| **garak** (NVIDIA-backed) | OSS | Extensive known-vulnerability LLM scanner; detailed attack/response reports | Pre-deploy/offline scanning; not a live review queue |
| **PyRIT** (Microsoft) | OSS | Customizable, semi-auto red-teaming w/ human-in-the-loop curation | Framework, not a managed review workflow |
| **Promptfoo** (OpenAI) | OSS + Cloud | Red-team plugins (OWASP/MITRE-mapped), fuzz testing, dashboard reports | Scanning + reporting; queue/triage is basic |
| **CyberSecEval** (Meta) | OSS | Focused on LLM-generated-code & NL vulnerabilities | Narrow scope (code security) |
| **Lakera Guard** | Commercial | Real-time prompt-injection / jailbreak / data-leak detection; **logs flagged attempts for review**, SIEM integration | Detection only; review queue is your SIEM/ticketing |
| **LangSmith Annotation Queues** | Commercial | Auto-route low-scoring / suspected-injection traces to SME review; feedback feeds datasets & judge calibration | Commercial; review at scale/triage is basic |
| **Langfuse Annotation Queues** | OSS + Cloud | Built-in reviewer UI, queue mgmt, score configs; self-hostable | Reviewer-queue ops (multi-reviewer routing, CI gate) are basic |
| **HumanLayer** | OSS SDK (cloud commercial) | Human-in-the-loop API letting agents request human approval/feedback on risky actions | General HITL primitive, not AI-incident-specific; "unsure" on deep AI-red-team queue features |

---

### Cross-cutting notes
- **post_emb** is the standout gap — no product detects "embeddings copied/queried by an untrusted party"; plan a custom build (audit logs + egress DLP + CSPM) rather than buying a tool.
- **post_anom / post_drift / post_rt** each have mature components but **no single integrated product**; the realistic implementation is a pipeline (observability/tracing → drift/eval → secret/PII DLP → red-team scans → annotation queue → policy feedback).
- Secret-leak and prompt-injection detection are the best-served sub-problems (Nightfall, TruffleHog, Lakera); volume-anomaly is served by APM/LLM-ops; unified human review queues remain the weakest link.
