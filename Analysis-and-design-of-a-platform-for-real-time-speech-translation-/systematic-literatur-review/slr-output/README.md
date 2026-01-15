# SLR Output (Audit Trail)

This folder is the **document-first audit trail** for the 7-role SLR agent workflow.

```text
slr-output/
├── 01-protocol/
├── 02-search/
├── 03-screening/
├── 04-quality/
├── 05-extraction/
├── 06-synthesis/
└── 07-report/
```

Agents (VS Code Copilot) are defined in:
- `.github/agents/slr-workflow/`

Suggested usage:
- `@slr-protocolplanner` → writes protocol artifacts
- `@slr-librarian` → runs searches + exports records
- `@slr-selector` → screening decisions
- `@slr-appraiser` → risk-of-bias / methodology
- `@slr-extractor` → extraction tables
- `@slr-synthesizer` → thematic synthesis
- `@slr-reporter` → final PRISMA manuscript
