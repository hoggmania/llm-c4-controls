# AI/LLM Supply-Chain Control — Candidate Tooling

> Scope: tools that can *implement* AI/LLM supply-chain, SBOM, provenance, and data-poisoning controls.
> Legend: **OSS** = open-source, **Commercial** = paid/proprietary, **Platform/Free** = hosted free tier.
> "ML-aware" = tooling that natively understands models/datasets/weights vs generic software SBOM.

---

## sc_inv — Model / Vendor Inventory
Catalogue every model/embedding provider, version, and data flow.

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **ModelOp – Evergreen AI Model Inventory** | Commercial | Centralized registry of *all* AI assets (1st/3rd-party models, GenAI, agents, vendor tools, embedded SaaS AI) with ownership. | Governance-focused; weak automated data-flow mapping; commercial licensing cost. |
| **ServiceNow – AI Control Tower (AI asset inventory)** | Commercial | Inventories AI models, systems, prompts, datasets, and MCP servers org-wide. | Heavyweight ITSM-suite module; deployment/integration overhead. |
| **VerifyWise – Model Inventory** | Commercial | Tracks every model with provider, version, deployment details, ownership. | SMB governance platform; limited automated discovery/scanning. |
| **Microsoft Purview / Azure Purview (Unified Catalog)** | Commercial | Data catalog with lineage/metadata; can surface the data estate feeding models. | Data-asset focused, not model-version specific; AI governance is an add-on. |
| **Hugging Face Hub – Model Cards / registry** | Platform/Free | Centralized registry with metadata: `base_model`, `datasets`, `license`, version tags. | Only HF ecosystem; won't cover proprietary/vendor models outside HF. |
| **MLflow Model Registry** | OSS | Tracks model versions, stages, source lineage you train/serve. | Covers your own trained models, not external/vendor catalog; no PII/data-flow mapping. |
| **OWASP Dependency-Track** | OSS | Persistent component inventory (can hold ML-BOMs) for continuous monitoring. | Dependency/component inventory, not a model registry; software-COMP oriented. |

**ML-aware:** Only HF Hub + ML-BOM-bearing tools natively describe model artifacts; most "inventory" products are governance registries, not auto-discovered vendor catalogs.

---

## sc_sbom — SBOM & Dependency Scan
CVE scan of libs, tokenizer deps, RAG document loaders.

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Syft** (anchore) | OSS | Generates CycloneDX/SPDX SBOMs from containers, dirs, binaries, packages. | Software deps only; no ML-artifacts; no CVE scoring itself. |
| **cdxgen / CycloneDX Generator** | OSS | Generates CycloneDX SBOM incl. **HuggingFace AI models**; ML-BOM support (1.6). | Generation only — no vulnerability scan; ML coverage still maturing. |
| **Trivy** (aquasec) | OSS | Container/FS/secret/IaC scan + SBOM gen + CVE detection in one. | Software/container focused; limited tokenizer/RAG-loader / model-weight coverage. |
| **Grype** (anchore) | OSS | Vulnerability scanner over SBOMs, images, containers. | CVEs for packages; not tokenizer logic or model weights. |
| **OWASP Dependency-Check** | OSS | CVE detection for dependencies (NVD). | Java/JS/NVD-centric; weak on ML-specific deps. |
| **OWASP Dependency-Track** | OSS | Continuous SBOM monitoring vs NVD/GHSA/OSV/OSS Index; persistent inventory. | Consumes SBOMs (doesn't generate); software components, not model blobs. |
| **Snyk Open Source** | Commercial | SCA CVE + license scan with CI/CD gates. | App dependencies; limited ML/tokenizer/RAG-specific coverage. |
| **CycloneDX ML-BOM / Zeropath AI-BOM** | Standard / Commercial | ML/AI bill of materials capturing models, datasets, and dependencies. | Emerging standard; tooling/eco still immature ("unsure" on production readiness). |

**ML-aware:** cdxgen is the standout OSS generator that reaches HF models; Trivy/Grype cover the *software* half (tokenizers, loaders, pip deps). No single OSS tool covers both model weights + RAG-loader logic + CVE end-to-end yet.

---

## sc_train — Training / Pre-train PII & Poison Scan
Detect PII or poisoned data in fine-tune/corpus BEFORE it enters the model.

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Microsoft Presidio** | OSS | PII detection + de-identification in unstructured/structured text; custom recognizers. | Text PII only; needs tuning; does **not** detect poisoning. |
| **AWS Macie** | Commercial | Sensitive-data discovery in S3 via ML + pattern matching. | AWS/S3-bound; not corpus-agnostic; no poisoning detection. |
| **Google Cloud DLP / Sensitive Data Protection** | Commercial | Inspect/classify sensitive data in storage and streams. | GCP-bound; no poisoning detection. |
| **Cleanlab** (lib OSS + Studio Commercial) | OSS/Commercial | Detects label errors, outliers, low-quality examples in labeled datasets. | Supervised/labeled-data quality; not direct poisoning-signature detection; no PII. |
| **HiddenLayer – Model Scanner** | Commercial | Scans 30+ model formats for embedded malware/tampering before deploy (Community Scan). | Scans the **trained artifact**, not the training corpus / PII. |
| **ModelScan** (Protect AI) | OSS | Scans model files (pickle/H5/SavedModel) for unsafe serialization/code-exec. | Model-artifact scan, not training-data PII/poison. |
| **TrojAI / DNN trojan detectors** | Research/Unsure | Techniques for detecting backdoors/trojans in trained nets. | Largely research-stage; no off-the-shelf enterprise pre-train scanner ("unsure"). |

**ML-aware:** PII scanning (Presidio/Macie/DLP) is mature; **pre-train data-poisoning detection has NO mature off-the-shelf commercial/OSS tool** — it remains research/labelled-data-quality (Cleanlab) territory. Biggest gap in this control.

---

## sc_lic — License / Provenance Check
Model & dataset license compliance and source attestation.

| Candidate | Type | Fit note | Gaps |
|---|---|---|---|
| **Hugging Face – Model/Dataset Cards (`license` field)** | Platform/Free | Native model + dataset license metadata + base_model lineage on HF Hub. | HF-ecosystem only; relies on maintainer accuracy. |
| **ScanCode Toolkit** | OSS | License + copyright detection; build custom compliance pipelines. | Code/dependency licenses; not model-weight licenses specifically. |
| **FOSSA** | Commercial | Automated OSS license compliance + vuln mgmt; SPDX export, policy engine. | Software deps; limited ML-model license classification. |
| **Mend SCA (WhiteSource)** | Commercial | License compliance + auto-remediation with dev-workflow gates. | Software dependencies; not model/dataset artifacts. |
| **ClearlyDefined** (OpenSSF) | OSS | Curated license/metadata for OSS components. | OSS packages, not model weights/datasets. |
| **sigstore / cosign + in-toto + SLSA** | OSS | Artifact signing + provenance attestation (can attest models/datasets). | Provenance/signing infra, **not** license classification; needs build integration. |
| **OSS Review Toolkit (ORT)** | OSS | License compliance, SBOM, policy as code. | Software-oriented; not ML artifacts. |
| **licensee / askalono** | OSS | Lightweight license-file/SPDX identification. | File-level only; not model/dataset license semantics. |

**ML-aware:** License compliance tools are almost entirely software-SCA; for *models/datasets* you lean on HF metadata + governance platforms (ModelOp/VerifyWise) for manual license capture. **Provenance/attestation** (sigstore/cosign/in-toto/SLSA) is the mature ML-relevant piece but addresses source attestation, not license type.

---

### Cross-cutting notes
- **No single tool covers ML artifacts end-to-end.** Generic SCA (Trivy/Grype/Snyk/Dependabot) handles tokenizer/loader/RAG library CVEs; cdxgen/HF/ML-BOM handle model artifact description; sigstore/SLSA handle provenance; Presidio/Macie/DLP handle corpus PII.
- **Biggest unverified gaps (mark "unsure"):** (1) pre-train *data-poisoning* detection — no production tool; (2) automated *vendor/model data-flow* mapping — mostly manual governance registries; (3) *model-weight license* compliance — software SCA doesn't reach it.
- **Recommended stack pattern:** cdxgen (ML-BOM gen) + Trivy/Grype (CVE) + Dependency-Track (continuous monitoring) + Presidio/Macie/DLP (corpus PII) + sigstore/cosign/SLSA (provenance) + HF/ModelOp (license + inventory), with Cleanlab (data quality) as the only poison-adjacent control.
