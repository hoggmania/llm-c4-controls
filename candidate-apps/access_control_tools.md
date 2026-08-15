# Access-Control / Authorization Tooling for AI, LLM & Agent Systems

Candidate tools per control. License: **OSS** = open source, **Comm** = commercial/proprietary, **OSS/Comm** = open-core (OSS engine + paid cloud/managed tier). Type: **Generic** = general policy/identity/infra tool repurposed for AI; **AI-native** = built for LLM/RAG/agent workflows. Capability claims verified via vendor docs/web (Aug 2026); items I could not verify are tagged **`unsure`**.

---

## an_rbac — Field-level RBAC limiting what an AI analyzer can read from a case/log store

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **OpenSearch / Elasticsearch field-level security (FLS)** | OSS (OpenSearch) / Comm (Elastic) | Generic | Native FLS + document-level security on the index; exclude fields like `ssn`, `pii` per role so the analyzer's reads are stripped server-side. | Coarse (field-level, not value-level); must map analyzer identity to a role; not aware of agent "purpose". |
| **OPA (Open Policy Agent)** | OSS | Generic | General-purpose PDP; "data filtering" via partial evaluation can rewrite/permit an analyzer query to only allowed columns. | You build the field-mapping layer; no built-in field catalog for arbitrary stores. |
| **Snowflake Dynamic Data Masking / Row Access Policies** | Comm | Generic | If the case/log store is Snowflake, masking policies + row access policies gate columns/rows by role at query time. | Locked to Snowflake; not for generic log stores. |
| **Cerbos** | OSS/Comm | AI-native (NHI/agent-aware) | PDP with derived roles + CEL conditions; can express "analyzer role X may read fields {a,b} but not {ssn}". Explicitly markets non-human-identity authz. | Field-level enforcement still requires the app to respect the decision; no native column masking. |
| **OpenFGA** | OSS | Generic (agent modeling supported) | Zanzibar ReBAC; can model object+field grants (`document:case#field:ssn@analyzer`). Has an "Authorization for Agents" modeling guide. | Field-level modeling is possible but not first-class; `unsure` on turnkey field extraction from arbitrary stores. |
| **AWS Verified Permissions (Cedar)** | Comm | Generic | Managed Cedar PDP; policies can gate attributes/fields of a resource. | Cedar is resource/action oriented; field-gating needs you to model fields as resources. |
| **Microsoft Purview / Varonis (DLP/IGA)** | Comm | Generic | Classification + field/column discovery and access governance over case stores; good for PII field inventory. | Heavy enterprise suite; not a runtime PDP for agent calls — pairs with a PDP. |

**Generic vs AI-native:** Best runtime enforcement = OpenSearch FLS or OPA data-filtering (generic, DB-adjacent); Cerbos/OpenFGA are the most agent/NHI-aware options.

---

## ss_acl — Tenant / namespace ACLs for per-tenant vector-store isolation

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **Pinecone (namespaces)** | Comm | AI-native | Serverless namespaces give *physical* isolation per tenant; one namespace per tenant, queries scoped to one namespace. | Namespace is only a logical key in pod-based indexes; cross-namespace query risk if app forgets the `namespace` param. |
| **Weaviate (native multi-tenancy)** | OSS/Comm | AI-native | Each tenant on its own shard = strong logical+physical isolation; `withTenant()` scoping; active/inactive tenant states. | Tenant key must be supplied per request; misconfiguration can cross tenants. |
| **Milvus (multi-tenancy + RBAC)** | OSS/Comm | AI-native | DB-level / collection-level / partition-key strategies; RBAC supported at DB & collection level (not partition/partition-key). | Physical isolation only at DB/collection tier; partition-key tier is logical. |
| **Qdrant (payload filtering / shard keys)** | OSS/Comm | AI-native | `group_id` payload filter runs inside HNSW traversal; custom `shard_key` for physical isolation; API-key auth. | Payload filtering is logical (must filter every query); physical isolation needs shard keys. |
| **pgvector + PostgreSQL RLS** | OSS | Generic (DB repurposed) | Row-Level Security enforces tenant isolation at the DB — "hard multi-tenancy" so a missed filter can't leak. | Operational overhead; RLS + HNSW perf tuning; not a dedicated vector DB. |
| **Chroma (Cloud tenant/database)** | OSS/Comm | AI-native | Chroma Cloud has tenant + database isolation; metadata filtering for logical scoping. | Self-hosted multi-tenancy/auth is more DIY (`unsure` on first-class tenant ACLs in OSS server). |
| **MongoDB Atlas Vector Search** | Comm | AI-native | Tenant separation via DB-per-tenant + MongoDB RBAC/field-level encryption. | Vector search ACLs ride on Atlas RBAC; cross-tenant query guardrails are app-side. |

**Generic vs AI-native:** Pinecone/Weaviate/Milvus/Qdrant/Chroma are AI-native vector stores with native tenant primitives; pgvector+RLS is the generic-DB repurposing pattern (strongest guarantee, most ops).

---

## rag_acl — Doc-level pre-retrieval ACL so only authorized docs are retrieved

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **OpenFGA** | OSS | Generic (agent modeling) | Model doc↔user/group relations (ReBAC); resolve the caller's allowed doc set pre-retrieval, filter by `doc_id`. | You must sync doc ACLs into the model; not a retriever itself. |
| **OPA** | OSS | Generic | Evaluate `allowed(user, doc)` at query time; return permitted doc IDs to the retriever as a filter. | ACL data must be supplied to OPA; no native doc ingestion. |
| **Azure AI Search (document-level access)** | Comm | AI-native (search) | Native security trimming: stores ACL/RBAC-scope/Purview-label/SharePoint-ACL metadata and filters results by the caller's Entra identity at query time. | Azure-centric; POSIX-like ACL/RBAC-scope support is *preview* (`unsure` on GA). |
| **Glean** | Comm | AI-native | Enterprise search that inherits and enforces source-system permissions (SharePoint, Drive, Slack, 275+ connectors); permissions-aware retrieval by default. | Closed SaaS; you cede retrieval stack to Glean; cost/lock-in. |
| **Microsoft Graph / SharePoint ACL sync → indexer** | Comm | AI-native (M365) | Graph extracts effective permissions per doc; indexer ingests ACL metadata for query-time trimming. | Bound to M365/SharePoint sources. |
| **LlamaIndex / LangChain metadata filters** | OSS | AI-native (framework) | Attach `allowed_groups`/`acl` metadata to nodes; apply a metadata filter from the user's groups at retrieval. | Framework pattern, not a standalone service; you own ACL sync + filter correctness. |
| **Cerbos / AWS Verified Permissions** | OSS/Comm / Comm | Generic | PDP returns the set of permitted doc IDs/attributes; retriever filters accordingly. | No document ingestion; ACL source still required. |

**Generic vs AI-native:** Azure AI Search, Glean, and M365 Graph are the AI/search-native pre-retrieval ACL paths; OPA/OpenFGA/Cerbos are generic PDPs you wire in front of any retriever.

---

## pdp — Tool Policy Decision Point for agent tool calls (allowlist, least privilege, tenant scope, read/write authZ)

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **OPA** | OSS | Generic | Stateless PDP; Rego policies enforce tool allowlist, tenant scope, read/write per (agent, tool, resource). Widely used (Permit runs on OPA). | Rego learning curve; you host/evaluate it in the agent loop. |
| **Cerbos** | OSS/Comm | AI-native (agent/NHI) | Purpose-built PDP for RBAC/ABAC/PBAC/ReBAC; "Fine-Grained Authorization for AI Gateways" + NHI support; CEL conditions, audit. | Needs Cerbos Hub/Synapse for external attribute enrichment. |
| **AWS Verified Permissions (Cedar)** | Comm | Generic | Managed Cedar PDP; expressive policies for tool actions, principals, tenant scopes. | AWS-hosted; policy authoring in Cedar; less agent-ecosystem tooling. |
| **OpenFGA** | OSS | Generic (agent modeling) | Relationship-based checks like `agent:runner#can_call@tool:send_email`; agent authorization guide. | ReBAC-centric; ABAC/allowlist needs modeling effort. |
| **AuthZed / SpiceDB** | OSS/Comm | Generic (Zanzibar) | Zanzibar-inspired permissions DB; real-time checks for agent↔tool↔resource; consistency controls. | SpiceDB is a permissions *store*; you write the PDP wrapper. |
| **Casbin** | OSS (Apache) | Generic | Multi-model (ACL/RBAC/ABAC/ReBAC) authz library in 20+ languages; embeddable PDP. | Library, not a service; no native agent/tenant semantics. |
| **Permit.io / Aserto** | Comm (OSS core) | Generic (AuthZ-as-a-Service) | Managed fine-grained authz with OPA/OPAL underpinnings; policy UI + API for agent tool gating. | Vendor dependency; `unsure` on deep agent-specific primitives beyond standard models. |

**Generic vs AI-native:** Cerbos is the most explicitly agent/NHI-oriented PDP; everything else is a generic authz engine adapted to the agent loop.

---

## identity — Identity & delegation context (OIDC / workload identity) binding user, agent, tenant, purpose, delegated authority

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **Keycloak** | OSS | Generic | Open-source IdP; OIDC/SAML, identity brokering, groups/roles → carry user+tenant claims to the agent. | Primarily human identity; workload/agent identity needs extension. |
| **Okta / Auth0** | Comm | Generic | Workforce OIDC IdP; OIDC tokens with groups/scopes; Auth0 also markets FGA for "users and agent identities". | Commercial; agent/delegation semantics are app-modeled. |
| **Azure Entra ID** | Comm | Generic | OIDC/CIE; rich group/role claims, workload identity federation for non-human principals. | Azure-centric. |
| **SPIFFE / SPIRE** | OSS (CNCF) | Generic (infra) | Cryptographic workload identity (SVIDs) for agents/services; federation across trust domains; integrates with Cerbos for NHI. | Machine/workload focus; mapping to human user+tenant+purpose is your design. |
| **HashiCorp Vault (JWT/OIDC auth + dynamic creds)** | OSS/Comm | Generic | Issues short-lived, scoped credentials to agents/workloads; auth via OIDC/JWT/SPIFFE; revocable. | Secret/cred issuance, not full identity federation. |
| **Auth0 Fine-Grained Authorization (FGA / OpenFGA)** | Comm/OSS | Generic | Bind agent identity to fine-grained resource relationships including agent principals. | See rag_acl/pdp; identity binding is partial. |

**Generic vs AI-native:** All are generic identity/workload primitives; none ships a turnkey "user+agent+tenant+purpose+delegation" tuple — you compose OIDC (Keycloak/Okta/Entra) for humans + SPIFFE/Vault for workloads and pass delegation claims through the PDP.

---

## sc_cfg — Provider config & key hygiene: signed DPAs, no hard-coded keys, tenant isolation, kill-switch to cut a compromised model provider

| Tool | License | Type | Fit note | Gaps |
|---|---|---|---|---|
| **HashiCorp Vault (dynamic secrets, KMS, revocation)** | OSS/Comm | Generic | Central secret store; dynamic short-lived LLM creds; `lease revoke -prefix` = instant kill-switch for a provider's credentials; encrypts at rest. | Key hygiene only; provider routing/kill-switch at the gateway is separate. |
| **LiteLLM (proxy / router)** | OSS/Comm | AI-native | Single control plane for 100+ models; virtual keys (no hard-coded provider keys in app), fallbacks, load balancing, per-key/tenant budgets; **disable a provider/deployment in config = kill-switch**. Supports BYOK tenant isolation. | You operate the proxy; "kill-switch" is config change + redeploy, not a one-click vendor feature. |
| **Portkey (AI gateway)** | Comm (OSS gateway) | AI-native | Virtual keys vault provider keys; 250+ models, fallbacks, guardrails, budgets; disable a virtual key / drop a target = provider cut. | Managed tier is commercial; kill-switch is operational (config), not a flagged safety product. |
| **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager** | Comm | Generic | Managed secret storage + rotation; no hard-coded keys; IAM-scoped per tenant. | Cloud-bound; no model-provider routing or kill-switch logic. |
| **Mozilla SOPS + External Secrets Operator** | OSS | Generic (K8s) | Encrypt provider keys in Git (SOPS); ESO syncs them into K8s secrets per namespace/tenant at runtime — clean key hygiene in GitOps. | K8s-only; no runtime provider kill-switch. |
| **Cloud KMS (AWS KMS / Azure Key Vault HSM / GCP KMS)** | Comm | Generic | Envelope-encrypt provider keys; tenant-scoped key rings; audit. | Key management, not provider cut-over. |

**Kill-switch note:** There is **no off-the-shelf "provider kill-switch product"** from Anthropic/OpenAI — provider cut-over is an *architectural pattern* implemented at the AI gateway (LiteLLM/Portkey) by removing/blacklisting a deployment, or at the secret layer (Vault `lease revoke`) by yanking credentials. Mark **`unsure`** for any vendor claiming a native one-click model-provider kill-switch; treat it as gateway/secret-operations discipline. Signed DPAs are a contractual control (procurement/legal), not a tool feature.

**Generic vs AI-native:** LiteLLM and Portkey are the AI-native layers that combine key-vaulting + tenant routing + provider kill-switch; Vault/Secrets Manager/SOPS/KMS are generic secret-hygiene primitives you point the gateway at.

---

### Cross-cutting observation
- **Most "AI authorization" tooling is generic policy/identity infra adapted to agents** (OPA, OpenFGA, Cerbos, Keycloak, Vault). Genuinely AI-native pieces are the **vector stores** (tenant isolation) and the **LLM gateways** (LiteLLM/Portkey: keys + routing + kill-switch).
- **No single product covers all six controls.** A realistic stack: Keycloak/Entra + SPIFFE for identity → OPA/Cerbos as PDP → OpenFGA/OPA for RAG/doc ACL → Pinecone/Weaviate (tenant ACL) + pgvector RLS → LiteLLM/Portkey + Vault for provider hygiene/kill-switch.
- Items flagged **`unsure`** (Azure AI Search GA status, Chroma OSS tenant ACLs, Permit agent primitives, native provider kill-switch) should be re-validated against current vendor docs before commitment.
