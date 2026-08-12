# LLM Private-Data Exposure — C4 Controls

C4 (PlantUML) diagrams and supporting material for modeling **where private data
actually leaks in AI systems** — beyond the usual "one guardrails box":

- AI analyzers / Cortex-style SIEM/SOAR summarization
- Tokenizers (token / logprob / hidden-state inversion)
- Semantic search (embedding inversion)
- RAG (over-broad retrieval + indirect prompt injection)
- Supply chain & vulnerability controls
- Post-usage detection & alerting (the layer most programs skip)

The central reframe: **the LLM is a new type of DLP** — a semantic inspector that
catches leakage regex misses, but only if deployed as a *separate* model instance
from the app it watches.

## Files

| File | What |
|---|---|
| `01-context.puml` | C4 Level 1 — System Context: actors + control scope |
| `02-container.puml` | C4 Level 2 — Containers: where controls live |
| `03-component.puml` | C4 Level 3 — Components: controls by lifecycle stage |
| `04-data-exposure-controls.puml` | C4 Level 3 — Private-data exposure across surfaces, mapped to OWASP GenAI LLM Top 10 (2026) |
| `05-owasp-coverage.md` | Full OWASP 2026 coverage matrix + surface notes |
| `article.md` | Long-form article: "Where Private Data Actually Leaks in AI Systems" |

## Render the diagrams

The `.puml` files use the C4-PlantUML macros via `!includeurl`, so they need internet
access to render on the public server.

- **Local (recommended):** `sudo apt install default-jre-headless plantuml && plantuml *.puml`
- **VS Code:** install the *PlantUML* extension, open a `.puml`, `Alt+D`.
- **Online:** paste each file into https://www.plantuml.com/plantuml/uml/ or planttext.com.

## License

MIT.
