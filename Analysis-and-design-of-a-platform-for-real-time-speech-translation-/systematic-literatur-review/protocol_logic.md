# Protocol Logic (SLR) — Event-driven microservice architectures for real-time speech translation (2014–2025)

This document explains the reasoning behind the SLR protocol in `protocol.json` so the review can be executed by another reviewer without additional context.

## 1) Framework choice: SPIDER (and why not PICO)

**Chosen framework: SPIDER** (Sample, Phenomenon of Interest, Design, Evaluation, Research type).

**Why SPIDER fits this topic**
- The review is **systems/architecture-oriented**, not a clinical or strictly intervention/comparator study.
- The evidence base is expected to include **engineering papers** (architecture descriptions, benchmarking, load testing, fault tolerance evaluations) where “intervention” and “comparison” are often implicit or heterogeneous.
- SPIDER explicitly supports mixed evidence and evaluation types (benchmarks, engineering studies, case studies), aligning with real-time distributed AI pipelines.

**Why PICO is less suitable here**
- PICO assumes a relatively stable notion of an **intervention** and a **comparison**; for architecture papers, comparisons are inconsistent (some compare sync vs async, others compare brokers, others compare orchestration vs choreography, and many have no direct comparator).

## 2) Construct decomposition and synonyms (traceable + auditable)

The search space is driven by three constructs that map directly to the research questions:

## 2.1) Scope split for LLM-focused architecture evidence (two-strand execution)

To support an SLR that covers LLM platform architecture work (beyond speech-translation-only), the protocol splits search execution into **two parallel strands**:

- **Strand A — LLM in microservice architecture**: LLMs are *one component inside* a broader microservice/event-driven/distributed architecture (focus: integration, orchestration/choreography, messaging, observability, latency/scalability/robustness at system level).
- **Strand B — LLM implemented as a microservice**: LLM is packaged/deployed as a *standalone service* (focus: model serving stack, inference server/gateway, token streaming/batching, GPU scheduling, autoscaling, reliability, cost/latency).

Why this split matters:
- Terminology differs: Strand A papers often talk about “platform architecture” and “event-driven microservices” but may not use “model serving” terms.
- Strand B papers often focus on inference/serving and may not describe broader EDA workflows.
- Running both strands reduces false negatives and makes PRISMA accounting cleaner (records can be tagged by strand at export time).

### Construct A — Architecture paradigm (event-driven / microservices / distributed)
**Purpose:** capture papers that describe system-level architectural structure and communication patterns (RQ1).

- Canonical term: **event-driven microservice architecture**
- Key synonym clusters:
  1. **Microservices/distributed**: microservice*, distributed system, service-oriented architecture (SOA)
  2. **Event-driven/messaging**: event-driven, message-driven, asynchronous messaging, publish-subscribe, stream processing
  3. **Coordination**: orchestration, choreography, workflow engine, saga pattern

Rationale: architecture papers vary widely in terminology; using multiple clusters reduces false negatives.

### Construct B — Pipeline task (speech translation pipeline; ASR/MT/TTS)
**Purpose:** ensure the review remains focused on **speech translation pipelines**, not generic translation or generic ASR (RQ1–RQ3).

- Canonical term: **real-time speech translation pipeline**
- Synonyms include: speech-to-speech translation, spoken language translation (SLT), simultaneous speech translation, streaming translation
- Component anchors: ASR / automatic speech recognition / speech-to-text; machine translation / MT / NMT; text-to-speech / TTS

**Unit-of-analysis constraint:** at least **2 of {ASR, MT, TTS}** must be covered by the described pipeline.

### Construct C — Outcomes and evaluation (latency/scalability/robustness; secondary quality)
**Purpose:** focus the review on measurable or concretely discussed performance and system qualities (RQ2–RQ3).

- Primary outcomes: end-to-end latency, throughput/concurrency, scalability, robustness/availability/resilience
- Secondary outcomes: quality metrics (WER, BLEU, COMET, etc.)

Rationale: the thesis problem statement emphasizes **latency, scalability, robustness** as primary, while quality is secondary but still relevant for evaluation trade-offs.

## 3) Eligibility criteria (testable, reviewer-applicable)

The protocol defines **inclusion** and **exclusion** criteria as statements that can be applied consistently:

### Inclusion criteria — reasoning
- **Date range (2014–2025)**: aligns with the deep-learning era and modern microservices/event-driven practice.
- **English**: ensures consistent screening and extraction.
- **Architecture requirement**: must be distributed/microservice/event-driven (explicitly stated or evidenced by decomposition + asynchronous communication). This prevents drift into purely model-level literature.
- **Pipeline requirement (≥2 components)**: avoids including papers that are only ASR or only MT with no pipeline integration.
- **Outcome requirement**: must discuss/evaluate at least one of latency/scalability/robustness. This keeps the review aligned to the thesis’s performance optimization focus.
- **Venue type**: peer-reviewed papers are included; preprints are allowed if they contain sufficient technical detail, because some systems work is first published as preprints.

### Exclusion criteria — reasoning
- **Model-only** and **monolithic end-to-end** papers are excluded to maintain architecture focus.
- **No concrete architecture**: opinion pieces without design specifics cannot support extraction.
- **Not ≥2 components**: removes single-component contributions not addressing pipeline integration.
- **Non-scholarly artifacts**: blogs/marketing/patents are excluded for reproducibility and evidence quality.
- **Duplicates**: handled via explicit deduplication rules.

## 4) Database / source selection rationale

The protocol specifies a pragmatic set of sources balancing coverage and executability:

- **OpenAlex**: broad cross-disciplinary coverage; good for initial high-recall discovery.
- **Semantic Scholar**: strong for CS/AI; often provides abstracts and links.
- **arXiv**: essential for preprints in speech/MT/systems.
- **Crossref**: best for DOI enrichment and metadata normalization.
- **PubMed (optional)**: included only if scoping suggests speech translation in biomedical/clinical settings.

**Subscription databases (IEEE/ACM/Scopus/WoS)** are listed as “manual execution acceptable” in the overall workflow because access varies and is often paywalled.

## 5) How each Boolean string maps to constructs

Each database query is built from the same logical components:

- **B (speech translation pipeline)** AND **A (architecture paradigm)** AND optionally **C (evaluation/outcomes)**

When executing the LLM platform architecture split:
- **Strand A queries** use: **LLM terms** AND **architecture/ops terms**
- **Strand B queries** use: **LLM terms** AND **serving/inference microservice terms** AND optionally **ops terms**

Importantly, this split changes **query construction and tagging**, not the inclusion/exclusion criteria.

## 5.1) Iteration-2 search broadening (INCLUDE=0 handoff)

This protocol includes an explicit Iteration-2 search strategy to improve recall when the initial review yields **zero included studies**.

### Why broaden
The initial corpus in this topic area is often dominated by **model-centric speech/NLP papers** that do not describe distributed deployment, microservice boundaries, or event-driven messaging. Systems-oriented papers may instead use:
- **General architecture language** ("system architecture", "pipeline architecture", "production deployment")
- **Cloud-native/ops language** ("Kubernetes", "autoscaling", "service mesh", "load balancing")
- **SOA language** ("service-oriented", "SOA")
and may be published in **software engineering / distributed systems venues** (ICSE/FSE/ESEM, SoCC/EuroSys) rather than speech/NLP venues.

### What changes (auditable)
Iteration-2 broadens the search by:
1. Keeping the **speech-translation anchor** (B) but relaxing the architecture requirement in the query from *only microservice/event-driven* to *(microservice/event-driven OR cloud-native/SOA/deployment/ops terms)*.
2. Using a **multi-query plan** per source (OpenAlex/arXiv/Crossref/Semantic Scholar) to compensate for limited boolean expressiveness.
3. Adding **manual venue targeting** for systems/SE/cloud venues via ACM DL / IEEE Xplore / DBLP.

### Bias and limitation impact
- **Precision decreases** (more noise) by design; this is handled by strict screening criteria (architecture evidence + ≥2 of ASR/MT/TTS).
- **Terminology bias is reduced** (fewer false negatives) by adding cloud-native/SOA/deployment terms.
- **Venue bias is reduced** by explicitly targeting ICSE/FSE/ESEM and SoCC/EuroSys.

### OpenAlex
- Uses broad keyword blocks because OpenAlex’s boolean expressiveness is limited.
- Relies on **year/type/language filters** for precision.

Iteration-2 adds a **query plan** (multiple simpler queries) that pairs the speech-translation anchor with either architecture terms (microservice/event-driven) or deployment/ops terms (kubernetes/kafka/orchestration).

### Semantic Scholar
- Provides a **query plan** with multiple queries because boolean behavior can vary.
- The second query explicitly anchors ASR + MT + real-time + microservices to catch papers that do not use “speech translation” terminology.

### arXiv
- Uses fielded search (`ti:`/`abs:`) for better precision.
- Applies date filtering post-retrieval if necessary.

Iteration-2 adds a recall-oriented query that looks for "system architecture"/deployment/orchestration terms alongside the speech-translation anchor, recognizing that some systems papers do not explicitly say "microservice".

### Crossref
- Uses a broad bibliographic query for discovery, but primarily intended for **metadata/DOI enrichment**.

Iteration-2 uses multiple focused `query.bibliographic` strings (microservice / event-driven / cloud native kubernetes / system architecture) to increase coverage while still allowing deduplication.

### PubMed
- Uses `[Title/Abstract]` and date range `[dp]` syntax.

## 6) Screening process, deduplication, and conflict handling

- The protocol defines four stages: identification → deduplication → title/abstract screening → full-text screening.
- **Deduplication order** is explicit and auditable: DOI → normalized title+year → URL → fuzzy title.
- **Conflict resolution** is defined for single-reviewer default with optional second-reviewer escalation.

## 7) Data extraction fields and quality appraisal approach

### Extraction fields
Fields are chosen to answer the RQs and support synthesis:
- Architecture patterns and messaging tech answer **RQ1**.
- Measurement setups and metrics answer **RQ2**.
- Benchmarks and evaluation approaches answer **RQ3**.

### Quality appraisal
A **hybrid checklist** is used:
- MMAT-inspired criteria for empirical rigor
- A custom architecture reporting checklist for system descriptiveness

Importantly: quality ratings are used to **weight synthesis**, not automatically exclude studies, unless a paper lacks minimal architectural detail.

## 8) Synthesis plan and feasibility conditions

- Default synthesis is **thematic mapping** from architectural patterns → reported outcomes/trade-offs.
- Meta-analysis is **conditional** and only attempted if outcomes and contexts are sufficiently comparable.

## 9) Known limitations and potential bias

- **Terminology variance**: architecture papers may not use consistent terms (“real-time”, “streaming”, “simultaneous”). Mitigation: multiple synonym clusters and multiple queries where needed.
- **Database limitations**: OpenAlex/Crossref are not perfect substitutes for subscription indexes. Mitigation: allow “manual execution required” where relevant.
- **Abstract-only bias**: some records may have missing abstracts. Mitigation: Level-1 includes an `UNSURE` pathway; Level-2 relies on best-available full text.
- **Preprint inclusion**: increases coverage but may include non-peer-reviewed work. Mitigation: tag preprints and reflect in quality appraisal.

## 10) PRISMA traceability

Every PRISMA phase is mapped to concrete artifacts:
- Identification: `search_logs/*`, `search_report.md`
- Deduplication: `search_exports/dedup_summary.json`
- Screening: `screening/title_abstract_decisions.csv`
- Eligibility (full text): `analysis/full_text_decisions.csv`
- Included + synthesis: `analysis/data_extraction_matrix.json`, `analysis/synthesis_summary.md`
