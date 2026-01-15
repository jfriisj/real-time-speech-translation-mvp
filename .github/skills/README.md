# Agent Skills

This repository defines **Agent Skills** under `.github/skills/` following the Agent Skills standard.

## Enable in VS Code (Preview)

- Enable the `chat.useAgentSkills` setting.
- Copilot will discover skills via the YAML frontmatter in each `SKILL.md`.

## Available Skills

- `compose-bringup`: Bring up a Docker Compose stack and check status.
- `cpu-mode-assertions-torch`: Assert CPU-only runtime inside a container using `torch`.
- `docker-logs-snapshot`: Capture Docker/Compose logs + container state as attachable debugging evidence.
- `http-health-smoke`: Smoke check health/readiness HTTP endpoints.
- `multipart-audio-smoke`: Multipart audio upload smoke test for transcription endpoints.
- `python-code-quality-scan`: Run analyzer MCP tools (Ruff + optional dead-code scan) as a quality gate.
- `python-pytest-run-capture`: Run pytest and capture output/env/exit code to artifacts.
- `synthetic-wav-sample`: Generate a non-sensitive WAV sample for tests.
- `version-audit-quickscan`: Quick scan for version strings to avoid release inconsistencies.

## Contributing a Skill

- Create a folder: `.github/skills/<skill-name>/`
- Add `.github/skills/<skill-name>/SKILL.md` with YAML frontmatter:

```markdown
---
name: skill-name
description: What it does and when to use it
---
```

- Add optional resources (scripts/examples) inside the same folder.
