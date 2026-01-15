# Supplementary Search Plan (v1.0)
## LLM/AI Pipeline Best Practices in Microservice/Event-Driven Architectures

**Purpose**
This supplementary search plan targets literature that actually answers the thesis-adjacent question:

> What architecture patterns and operational best practices are reported for running LLM/AI pipelines in microservice/event-driven distributed systems (low latency, scalability, robustness, observability)?

It is designed to complement (not replace) the S2ST-specific SLR. If the S2ST SLR yields zero included studies, this plan supports extracting *transferable systems evidence* from adjacent domains (LLM serving, online inference platforms, event-driven AI workflows), which can be justified in the thesis as “cross-domain architectural evidence.”

---

## Scope (recommended)

### Two-strand execution (matches your `protocol.json` intent)
- **Strand A — LLM in microservice architecture**: LLM is one component inside a larger distributed/event-driven workflow.
- **Strand B — LLM implemented as a microservice**: serving/inference stack, deployment, scaling, GPU scheduling, tail latency, multi-tenancy.

### Inclusion criteria (practical + thesis-aligned)
Include studies that:
- Describe a **distributed** architecture (microservices/SOA/cloud-native systems) OR a clearly decomposed serving stack.
- Include at least one **systems quality attribute**: latency (ideally tail), throughput, scaling/autoscaling, reliability/resilience, observability.
- Provide **operational/architectural detail** (diagrams, components, communication patterns, deployment model, evaluation setup).
- Can be **peer-reviewed or high-detail technical reports** (depending on your thesis rules). If you must stay strictly scholarly, tag “grey literature” separately instead of excluding it.

### Exclusion criteria
Exclude:
- Purely model-architecture/training papers with no deployment/serving/system detail.
- Prompting-only papers with no runtime/ops architecture.
- Opinion pieces without concrete architecture.

---

## Where to search (high-yield for architecture/ops)

### Scholarly indices
- **ACM Digital Library** (systems/software engineering)
- **IEEE Xplore**
- **DBLP** (good for venue targeting)
- **Google Scholar** (broad recall; use carefully with strict screening)

### Venue targeting (manual)
- Distributed systems / cloud: SoCC, EuroSys, NSDI, OSDI, Middleware, ICDCS
- Software engineering: ICSE, FSE, ESEM
- Streaming/event-driven: DEBS

---

## Query blocks (copy/paste)

### Block definitions
- **LLM terms**: ("large language model" OR LLM OR "generative AI" OR "foundation model")
- **Serving terms**: (serving OR inference OR "model serving" OR "inference server" OR "token streaming" OR batching OR "KV cache")
- **Microservice/Distributed terms**: (microservice* OR "distributed system" OR "cloud native" OR Kubernetes OR k8s OR "service mesh" OR "API gateway")
- **Event-driven terms**: ("event-driven" OR Kafka OR Pulsar OR RabbitMQ OR NATS OR "message broker" OR "event streaming" OR "pub/sub" OR "stream processing")
- **Quality terms**: (latency OR "tail latency" OR p95 OR p99 OR throughput OR scalability OR autoscaling OR reliability OR resilience OR observability OR tracing)

### Strand B (LLM as a microservice): serving + ops
Use this when you want “how to serve LLMs reliably and fast.”

**Core query**
- (LLM terms) AND (Serving terms) AND (Microservice/Distributed terms) AND (Quality terms)

**Variant 1 (Kubernetes/autoscaling focus)**
- (LLM terms) AND ("model serving" OR inference) AND (Kubernetes OR autoscaling OR "horizontal scaling") AND (latency OR throughput)

**Variant 2 (multi-tenancy/scheduling focus)**
- (LLM terms) AND (inference OR serving) AND ("GPU scheduling" OR "resource management" OR multi-tenant OR "admission control") AND (p95 OR p99 OR latency)

### Strand A (LLM inside an event-driven architecture): workflows + messaging
Use this when you want “best practices to integrate LLMs into pipelines.”

**Core query**
- (LLM terms) AND (Event-driven terms) AND (Microservice/Distributed terms) AND (observability OR tracing OR reliability OR latency)

**Variant 1 (workflow/orchestration focus)**
- (LLM terms) AND (orchestration OR choreography OR workflow) AND (microservice* OR "distributed system") AND (latency OR reliability)

**Variant 2 (RAG/agent pipeline ops focus)**
- (LLM terms) AND (RAG OR "retrieval augmented" OR agent* OR tool-use) AND (microservice* OR "event-driven") AND (observability OR tracing OR evaluation)

---

## Screening heuristics (to keep it architecture-focused)
A paper likely qualifies if it includes at least 2 of:
- A component diagram/service decomposition
- A deployment model (containers/Kubernetes/service mesh)
- A communication model (sync RPC vs async/event bus)
- Quantitative metrics (latency percentiles, throughput, scaling curves)
- Failure handling patterns (retries, DLQ, circuit breaker, backpressure)

---

## Outputs to produce (recommended)
- `search_logs/` for each source + query string used
- A deduped `records.csv` with **abstracts** where possible
- Title/abstract screening sheet
- Full-text decision sheet for UNSURE
- A short synthesis mapping patterns → impacts (latency/scaling/robustness)

---

## How to connect this to your thesis (wording you can reuse)
- “No S2ST-specific microservice architecture studies were identified in the screened academic subset. Therefore, we additionally reviewed cross-domain systems literature on LLM/AI serving and event-driven microservice workflows to derive transferable architecture patterns applicable to real-time speech translation pipelines.”

