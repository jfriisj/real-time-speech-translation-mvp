# MVP Latency Baseline (Traceability Probe)

**Date**: 2026-01-19
**Plan**: [agent-output/planning/004-traceability-and-latency-plan.md](agent-output/planning/004-traceability-and-latency-plan.md)
**Run Type**: Initial baseline (publication delta latency)

## Environment
- **Host**: Local dev workstation
- **CPU/GPU**: CPU-only (local)
- **OS**: Linux
- **Kafka**: docker-compose.yml (local)
- **Schema Registry**: docker-compose.yml (local)
- **Notes**: Baseline run completed with 100/100 successful chains after a warmup phase.

## Run Configuration
- **Command**: `python tests/e2e/measure_latency.py --count 100 --output latency_summary.json`
- **Warmup Discard**: 5 requests (effective discard = min(warmup, successes))
- **Timeout**: 10s per request

## Results (JSON Summary)
```json
{
  "meta": {
    "timestamp": "2026-01-19T10:29:45.296853Z",
    "run_id": "9ffb6a9f-7907-410e-9c7d-82dc8980b286",
    "warmup_discarded": 5
  },
  "counts": {
    "total": 100,
    "success": 100,
    "failure": 0
  },
  "latencies_ms": {
    "p50": 1045.0,
    "p90": 1155.8000000000002,
    "p99": 1402.7300000000018
  },
  "failures": {
    "timeout": 0,
    "broken_chain": 0
  }
}
```

## Interpretation
- The metric represents **publication delta latency**: $T2 - T0$ where timestamps are set at event creation/publish time.
- This does not include consumer poll wait time or internal service processing start time beyond event creation.

## Follow-up
- Confirm baseline against target environments if needed (GPU or different hardware).
