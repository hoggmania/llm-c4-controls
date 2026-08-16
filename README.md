# LLM Private-Data Exposure — C4 Controls

C4 (PlantUML) diagrams and supporting material for modeling **where private data
actually leaks in AI systems** — beyond the usual "one guardrails box":

- AI analyzers / Cortex-style SIEM/SOAR summarization
- Tokenization & model diagnostics (third-party processing, logprob exposure, token inflation)
- Semantic search (embedding inversion)
- RAG (over-broad retrieval + indirect prompt injection)
- Supply chain & vulnerability controls
- Post-usage detection & alerting (the layer most programs skip)
- Agent tool/MCP authorization and runtime resilience

The central reframe: **the LLM is a new type of DLP** — a semantic inspector that
catches leakage regex misses, but only if deployed as a *separate* model instance
from the app it watches. For agents, the companion rule is: **the model is not an
authorization boundary**. It must not hold direct tool credentials or have a direct
network path to external actions.

OWASP mappings use the [official OWASP project repository](https://github.com/owasp/www-project-top-10-for-large-language-model-applications),
which identifies the 2026 release as current and links to its
[canonical Markdown source](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/tree/main/2026/final).
Agent tool/runtime mappings use the separate [OWASP Top 10 for Agentic Applications
2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
as their primary framework.

## Two detailed control views

The Level 3 diagrams separate two related questions that a single guardrails box cannot
answer:

- **Private-data exposure (`04`)** — where sensitive data leaks across analyzers,
  tokenization and diagnostics, semantic search, RAG, supply chain and post-usage
  monitoring. Components are mapped to `LLM01`–`LLM10` from the OWASP GenAI LLM Top
  10 2026.
- **Agent tool/runtime controls (`05`)** — how a proposed tool or MCP action is typed,
  validated, authorized, approved, constrained, executed and audited. Components are
  mapped primarily to `ASI01`–`ASI10` and secondarily to the applicable LLM risks.

The agent view covers every ASI category but does not claim complete mitigation. It
marks partial coverage for goal integrity, signed/pinned tool provenance, persistent
memory, agent-to-agent protocols and per-agent behavioral attestation. The full
component crosswalk and coverage strength are in [`05-owasp-coverage.md`](05-owasp-coverage.md).

## Files

| File | What |
|---|---|
| `01-context.puml` | C4 Level 1 — System Context: actors + control scope |
| `02-container.puml` | C4 Level 2 — Containers: where controls live |
| `03-component.puml` | C4 Level 3 — Components: controls by lifecycle stage |
| `04-data-exposure-controls.puml` | C4 Level 3 — Private-data exposure across surfaces, mapped to OWASP GenAI LLM Top 10 2026 |
| `05-agent-tool-runtime-controls.puml` | C4 Level 3 — Agent tool/MCP and runtime controls, mapped primarily to OWASP Agentic Top 10 2026 and secondarily to OWASP GenAI LLM Top 10 2026 |
| `05-owasp-coverage.md` | OWASP GenAI LLM and Agentic Top 10 2026 coverage matrices + surface notes |
| `CANDIDATE_APPS.md` | Candidate applications (open + closed source) implementing each control, with a 41-row completeness matrix + per-control detail |
| `candidate-apps/` | Per-cluster research tables + rendered completeness heatmap backing `CANDIDATE_APPS.md` |
| `linkedin-completeness-summary.md` | LinkedIn-ready narrative of the findings (with embedded heatmap) |
| `article.md` | Long-form article: "Where Private Data Actually Leaks in AI Systems" |

## Render the diagrams

The `.puml` files use the C4-PlantUML macros via `!includeurl`, so they need internet
access to render on the public server.

- **Local (recommended):** `sudo apt install default-jre-headless plantuml && plantuml *.puml`
- **VS Code:** install the *PlantUML* extension, open a `.puml`, `Alt+D`.
- **Online:** paste each file into https://www.plantuml.com/plantuml/uml/ or planttext.com.

## License

MIT.
