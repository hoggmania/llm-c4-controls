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
component crosswalk and coverage strength are in [`docs/owasp-coverage.md`](docs/owasp-coverage.md).

## Repository layout

| Path | What |
|---|---|
| `diagrams/` | C4 `.puml` sources (`01-`..`05-`) |
| `diagrams/rendered/` | Rendered PNGs of the C4 diagrams + the LinkedIn layers figure |
| `docs/c4-guide.md` | How to read the C4 model and the five diagram views |
| `docs/agentic-controls.md` | Agentic control philosophy one-pager (OWASP Agentic Top 10 2026) |
| `docs/owasp-coverage.md` | OWASP GenAI LLM + Agentic Top 10 2026 coverage matrices |
| `docs/tool-candidates.md` | Candidate apps (open + commercial) per control — 41-row completeness matrix |
| `docs/oss-reference-architecture.md` | Concrete OSS-only reference architecture (Mermaid) |
| `docs/article.md` | Long-form article: "Where Private Data Actually Leaks in AI Systems" |
| `docs/research/` | Per-cluster tool research tables backing `tool-candidates.md` |
| `docs/completeness-heatmap.png` | Rendered completeness heatmap |
| `posts/linkedin-completeness-summary.md` | LinkedIn-ready narrative of the findings |

## Render the diagrams

The `.puml` files use the C4-PlantUML macros via `!includeurl`, so they need internet
access to render on the public server.

- **Local (recommended):** `sudo apt install default-jre-headless plantuml && plantuml diagrams/*.puml`
- **VS Code:** install the *PlantUML* extension, open a `.puml`, `Alt+D`.
- **Online:** paste each file into https://www.plantuml.com/plantuml/uml/ or planttext.com.

## License

MIT.
