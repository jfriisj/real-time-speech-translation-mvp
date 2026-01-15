# Title/Abstract Screening Report (Level 1)

**Protocol**: systematic-literatur-review/protocol.json (v2.0)

## Counts (PRISMA-style, Level 1)
- Records screened (title/abstract): **50**
- Records excluded at Level 1: **44**
- Records advanced to full-text (INCLUDE + UNSURE): **6**
	- INCLUDE: **0**
	- UNSURE: **6**

## Top exclusion reasons
- **EXCL01** (Model-only; no distributed/system architecture): 24
- **EXCL04** (Does not include ≥2 of ASR/MT/TTS in pipeline): 9
- **EXCL03** (No concrete architecture/system description): 7
- **EXCL02** (Monolithic E2E; no distributed/microservice/EDA described): 3
- **EXCL06** (Outside date range): 1

## Notes / Observations
- The current export file (search_exports/records.csv) contains **empty abstracts for all records**, which materially limits confident Level-1 screening for architecture criteria.
- Per protocol, when the abstract is missing/unclear, records are marked **UNSURE** rather than excluded unless the title alone clearly indicates out-of-scope (e.g., non-speech-translation topics, or outside date range).

## Protocol ambiguities affecting confidence
- **Architecture evidence at TA stage**: With missing abstracts, it is often impossible to verify whether a study describes a distributed/event-driven/microservice architecture versus a monolithic model. This forces conservative **UNSURE** decisions for system-like titles (e.g., IWSLT system submissions, virtual-meeting deployments).
