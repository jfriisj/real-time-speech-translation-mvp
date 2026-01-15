# Live Testing Report: <Plan/Feature Name>

**Plan/Branch Reference**: agent-output/planning/NNN-<feature>-plan.md (or <branch/commit>)
**Date**: YYYY-MM-DD
**Live Testing Agent**: LiveTesting
**Target Environment**: docker-compose local / staging / other
**Device(s)**: <host + client device(s)>

## Summary

- **Status**: PASS / FAIL
- **Key findings**:
  - <finding>

## Environment Details

- **Host OS/Hardware**: <e.g., Linux x86_64, 16GB RAM, GPU?>
- **Docker/Compose version**: <version>
- **Service image/build**: <tag/commit>
- **Network**: <localhost / LAN / staging URL>
- **Relevant env vars (redacted)**:
  - <NAME>=<redacted>

## Steps Executed (Evidence)

### Bring up
- **Command**:
  - `docker compose up -d --build`
- **Result**: PASS/FAIL
- **Evidence**:
  - `docker compose ps` output summary:
  - `docker logs speech-recognition-service --tail 200` summary:

### Health checks
- **Commands**:
  - `curl -sS -f http://localhost:8001/health/`
  - `curl -sS -f http://localhost:8001/health/ready`
  - `curl -sS -f http://localhost:8001/health/live`
  - `curl -sS -f http://localhost:8001/health/models`
- **Result**: PASS/FAIL
- **Notes**:
  - <notes>

### Transcription smoke (/transcribe)
- **Audio source**: synthetic / consented test audio
- **Command**:
  - `curl -sS -X POST "http://localhost:8001/transcribe" -F "audio=@<file>" -F "language=en"`
- **Result**: PASS/FAIL
- **Response summary** (no sensitive payloads):
  - <summary>
- **Logs checked**:
  - <errors/exceptions?>

### Real device client check (optional)
- **Client device**: <device>
- **Commands/steps**:
  - <steps>
- **Result**: PASS/FAIL

## Results

- **Startup behavior**: <time to ready, model load observations>
- **Stability**: <restarts, timeouts>
- **Performance notes**: <latency, CPU/RAM/GPU notes>

## Privacy & Compliance

- **Data used**: <synthetic vs real>
- **PII handling**: <how prevented/redacted>
- **Retention**: <what was stored and where>

## Issues Found (if any)

### Issue 1: <title>
- **Severity**: BLOCKER / HIGH / MEDIUM / LOW
- **Repro steps**:
  - <steps>
- **Observed**:
  - <observed>
- **Expected**:
  - <expected>
- **Evidence (redacted)**:
  - <logs/snippets>

## Go/No-Go Recommendation (Pre-PR)

- **Recommendation**: GO / NO-GO
- **Blocking items**:
  - <item>
- **Suggested follow-ups**:
  - <item>

## Handoff

- If **FAIL**: Handing off to Implementer for fixes.
- If **PASS**: Handing off to UAT for value validation.
