# Thesis Outline Plan (Architect)

Date: 2026-01-26

This file maps the project’s problem formulation to the existing LaTeX chapter structure defined in `Analysis-and-design-of-a-platform-for-real-time-speech-translation-/report/main.tex`.

## 1) Thesis Statement & Research Questions

**Working thesis statement**
- Design, implement, and evaluate an event-driven microservice architecture for real-time speech-to-speech translation, with empirical measurement and optimization of latency–scalability–robustness trade-offs, and reproducible evaluation of performance and quality compared to existing solutions.

**Main Research Question (MRQ)**
- How can an event-driven microservice architecture be designed and implemented to deliver robust and scalable real-time speech-to-speech translation with measurable performance optimization?

**Sub-Questions (SQ1–SQ5)**
- SQ1: Which architectural principles and design patterns support an effective real-time speech translation pipeline?
- SQ2: Which factors influence end-to-end latency and the ability to scale?
- SQ3: How can these factors be measured and optimized in practice?
- SQ4: How can the system remain robust and available when individual components fail?
- SQ5: How can system performance and output quality be evaluated and compared against existing solutions?

## 2) Chapter Mapping (file-by-file)

### `chap-introduction.tex`
**Purpose:** Set context, motivate, state problem, list MRQ + SQ1–SQ5, and define measurable success criteria.
- Background & Motivation:
  - Linguistic inclusion and cross-language communication needs.
  - Market dominance of proprietary platforms (Google/Microsoft/AWS) and limited adaptability/cost concerns.
  - Research gap: limited independent guidance on architecture for low-latency + scalable + robust multi-component AI pipelines.
- Problem Statement:
  - Architecture-level gap: integrating ASR → MT → (optional) TTS under strict latency constraints with horizontal scaling.
- Research Questions:
  - Insert MRQ + SQ1–SQ5.
- Success Criteria:
  - Define how “success” is measured: latency (percentiles), throughput/capacity, robustness/availability, resource usage, quality, and deployability/extensibility.

### `chap-background.tex`
**Purpose:** State-of-the-art, core theory and concepts.
- Real-time speech translation pipeline overview (ASR/MT/TTS) and typical bottlenecks.
- Microservices and event-driven architecture theory:
  - Microservices patterns (service boundaries, orchestration vs choreography).
  - Event streaming concepts (Kafka), schema governance (Schema Registry/Avro).
  - Distributed-systems trade-offs relevant to this thesis (ordering, at-least-once, idempotency, backpressure).

### `chap-analysis-and-design.tex`
**Purpose:** Architecture design and analysis that answers SQ1 and prepares SQ2–SQ4.
- Proposed system architecture:
  - Event contract, topics, message envelope, correlation/traceability.
  - Component boundaries (gateway/VAD/ASR/translation/(TTS)).
- Key design decisions and rationale:
  - Event-driven communication choice, service decomposition, failure handling patterns.
  - Latency and scaling design levers (batching, partitioning, concurrency, payload policies).

### `chap-implementation.tex`
**Purpose:** Concrete implementation choices enabling evaluation.
- Implementation of each service and the event backbone.
- Deployment approach (local Compose; optionally Kubernetes if used).
- CI/CD and test strategy (unit + integration + smoke), schema management.

### `chap-evaluation.tex`
**Purpose:** Empirical evaluation answering SQ2–SQ5.
- Metrics definition and measurement method:
  - E2E latency definition and per-stage latency; report percentiles.
  - Throughput/capacity (requests/s, concurrent sessions) under increasing load.
  - Robustness experiments (component failure, poison messages, retries, recovery time).
  - Resource usage (CPU/memory) vs throughput/latency.
- Quality evaluation:
  - ASR quality (WER/CER), MT quality (BLEU/COMET), plus optional human evaluation.
  - Comparison framing against commercial solutions (method + limitations).

### `chap-conclusion.tex`
**Purpose:** Summarize contributions, answer MRQ, and list future work.
- Contributions: reference architecture, reproducible measurement approach, and implementation findings.
- Limitations: dataset constraints, hardware constraints, and scope.
- Future work: edge deployment, multimodal inputs, improved autoscaling/governance, stronger security analysis.

## 3) BibTeX Strategy

**Citation key format (decision):** keep existing lower-case keys in the style `authorYYYYshort`.
- Examples: `mordor2024speech`, `unesco2022inclusion`, `vaswani2017attention`.
- Rationale: matches existing citations already used in the case material and reduces refactoring.

## 4) Notes / Open Decisions (for later drafting)

- Numeric targets for latency/throughput/availability are currently intentionally left as placeholders until the measurement baseline is locked (Evaluation chapter).
- Whether TTS is included in the MVP evaluation should be stated explicitly in Introduction scope boundaries.
