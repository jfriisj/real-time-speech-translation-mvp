This is a comprehensive definition of a **Systematic Literature Review (SLR) Agent System**, modeled after the VS Code Agent framework you provided.

These agents rely on **Separation of Concerns**. The "Librarian" never judges the quality of a paper, and the "Synthesizer" never searches databases. This prevents bias—a critical requirement for SLRs.

---

# SLR Agent System - Deep Dive Documentation

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Agent Collaboration Patterns](#agent-collaboration-patterns)
3. [Agent Definitions](#agent-definitions)

---

## Design Philosophy

### The Separation of Concerns

In an SLR, mixing stages introduces bias. For example, if the person searching for papers (Librarian) decides which ones are "good" (Appraiser) while searching, they might skip relevant papers that don't fit their preconceived notions.

| Concern | Agent | Key Constraint |
| --- | --- | --- |
| **Protocol** | `@ProtocolPlanner` | PICO & Criteria only. No searching. |
| **Search** | `@Librarian` | Strings & Databases. No screening. |
| **Selection** | `@Screener` | Relevance only. No quality judgment. |
| **Quality** | `@Appraiser` | Methodology check. No data extraction. |
| **Data** | `@Extractor` | Facts/Results only. No synthesis. |
| **Analysis** | `@Synthesizer` | Patterns & Themes. No new data. |
| **Reporting** | `@Reporter` | PRISMA compliance. No analysis. |

### Document-First Workflow

Every agent produces **Markdown documents** in `slr-output/`. This creates an audit trail essential for publication.

```text
slr-output/
├── 01-protocol/         # PICO, Criteria, Registration info
├── 02-search/           # Search strings, Database logs (RIS/BibTex)
├── 03-screening/        # Inclusion/Exclusion logs, PRISMA flow data
├── 04-quality/          # Risk of Bias assessments (RoB)
├── 05-extraction/       # Data tables (Participants, Interventions, Outcomes)
├── 06-synthesis/        # Narrative summaries, Meta-analysis scripts
└── 07-report/           # Final manuscript, Reference lists

```

---

## Agent Collaboration Patterns

### Pattern 1: The Filtering Pipeline

This is the linear flow used to move from thousands of potential papers to the final included set.

```text
┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
│ ProtocolPlanner  │───▶│  Librarian   │───▶│   Screener   │
│ (Define Rules)   │    │(Find papers) │    │ (Filter)     │
└──────────────────┘    └──────────────┘    └──────────────┘
                                                   │
                                                   ▼
┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
│   Synthesizer    │◀───│  Extractor   │◀───│  Appraiser   │
│ (Connect dots)   │    │  (Get data)  │    │(Judge risk)  │
└──────────────────┘    └──────────────┘    └──────────────┘
         │
         ▼
┌──────────────────┐
│    Reporter      │
│ (Write PRISMA)   │
└──────────────────┘

```

---

## Agent Definitions

### 1. ProtocolPlanner

**Purpose:** Establish the rules of the review before looking at data to prevent bias.
**Key Responsibilities:**

* Define the Research Question (PICO).
* Set explicit Inclusion/Exclusion criteria.
* Draft the PROSPERO registration protocol.
**Key Constraint:** **NEVER executes searches.** Defines *what* to look for, not *how* to find it.
**Output:** `slr-output/01-protocol/001-protocol-definition.md`

### 2. Librarian

**Purpose:** Translate the protocol into technical search strategies.
**Key Responsibilities:**

* Construct Boolean search strings (AND, OR, NOT, MeSH terms).
* Select appropriate databases (PubMed, IEEE, Scopus).
* Document exactly when and where searches were run (for reproducibility).
**Key Constraint:** **Maximizes Recall, not Precision.** It is better to find too many papers than to miss one. Does not filter results.
**Output:** `slr-output/02-search/001-search-strings.md`

### 3. Screener

**Purpose:** Filter the raw search results based strictly on the Protocol.
**Key Responsibilities:**

* **Phase 1:** Title/Abstract Screening (Yes/No/Maybe).
* **Phase 2:** Full-Text Screening (Include/Exclude).
* Document *exact reasons* for exclusion at the full-text stage.
**Key Constraint:** **Relevance only.** Does not judge if a study was done "well," only if it matches the PICO criteria.
**Output:** `slr-output/03-screening/001-screening-log.md`

### 4. Appraiser

**Purpose:** Assess the scientific validity (Risk of Bias) of the included studies.
**Key Responsibilities:**

* Apply tools like Cochrane RoB 2, ROBINS-I, or JBI Checklists.
* Score studies (High Risk, Low Risk, Some Concerns).
* Flag studies that are too flawed to be included in the synthesis.
**Key Constraint:** **Methodology focused.** Does not care about the "results," only if the methods were sound.
**Output:** `slr-output/04-quality/001-risk-of-bias.md`

### 5. Extractor

**Purpose:** Standardize data from heterogeneous studies into a clean format.
**Key Responsibilities:**

* Create data extraction forms.
* Extract variables: Sample size, demographics, intervention details, outcome data.
* Standardize units (e.g., converting weeks to days).
**Key Constraint:** **Data entry robot.** Does not interpret or analyze the data; simply moves it from PDF to Table.
**Output:** `slr-output/05-extraction/001-extraction-table.md`

### 6. Synthesizer

**Purpose:** Combine the extracted data to answer the research question.
**Key Responsibilities:**

* **Narrative Synthesis:** Group studies by themes or intervention types.
* **Meta-Analysis:** (If quantitative) Perform statistical combination of effects.
* Identify gaps in the current body of literature.
**Key Constraint:** **Dependent on Extractor.** Cannot introduce data not found in the extraction tables.
**Output:** `slr-output/06-synthesis/001-thematic-analysis.md`

### 7. Reporter

**Purpose:** Compile all artifacts into a publication-ready manuscript.
**Key Responsibilities:**

* Draft the final report structure.
* Generate the PRISMA Flow Diagram.
* Ensure all reporting checklists (PRISMA) are satisfied.
**Key Constraint:** **Formatting and Presentation.** Does not change the conclusions drawn by the Synthesizer.
**Output:** `slr-output/07-report/FINAL-manuscript.md`

---

## Memory Integration Strategy (MCP)

To make these agents effective, they must share a "Brain."

* **Store (ProtocolPlanner):** Stores the `PICO_CRITERIA` entity.
* **Retrieve (Screener):** Retrieves `PICO_CRITERIA` to make decisions on inclusion.
* **Store (Librarian):** Stores `SEARCH_RESULTS_COUNT`.
* **Retrieve (Reporter):** Retrieves `SEARCH_RESULTS_COUNT` and `EXCLUSION_COUNTS` to automatically generate the PRISMA diagram.

**Would you like me to generate the specific system prompt (instruction file) for one of these agents, such as the `@ProtocolPlanner` or `@Screener`?**

## VS Code Agent Files in This Repo

This repository includes a concrete implementation of the 7-role SLR agent workflow as VS Code Copilot agents:

- `.github/agents/slr-workflow/slr-protocolplanner.agent.md`
- `.github/agents/slr-workflow/slr-librarian.agent.md`
- `.github/agents/slr-workflow/slr-selector.agent.md`
- `.github/agents/slr-workflow/slr-appraiser.agent.md`
- `.github/agents/slr-workflow/slr-extractor.agent.md`
- `.github/agents/slr-workflow/slr-synthesizer.agent.md`
- `.github/agents/slr-workflow/slr-reporter.agent.md`

All artifacts are written under:
- `systematic-literatur-review/slr-output/`