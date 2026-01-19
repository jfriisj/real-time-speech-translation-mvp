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
- **Notes**: Initial smoke run completed with 4/5 successful chains; full 100-run baseline pending.

## Run Configuration
- **Command**: `python tests/e2e/measure_latency.py --count 5 --output latency_summary.json`
- **Warmup Discard**: 5 requests (effective discard = min(warmup, successes))
- **Timeout**: 10s per request

## Results (JSON Summary)
```json
{
  "meta": {
    "timestamp": "2026-01-19T10:14:45.913737Z",
    "run_id": "2d879916-41a2-4577-b144-bd3ec9b0e2eb",
    "warmup_discarded": 4
  },
  "counts": {
    "total": 5,
    "success": 4,
    "failure": 1
  },
  "latencies_ms": {
    "p50": 0.0,
    "p90": 0.0,
    "p99": 0.0
  },
  "failures": {
    "timeout": 1,
    "broken_chain": 0
  }
}
```

## Interpretation
- The metric represents **publication delta latency**: $T2 - T0$ where timestamps are set at event creation/publish time.
- This does not include consumer poll wait time or internal service processing start time beyond event creation.

## Follow-up
- Run the full N=100 campaign and replace this section with the official baseline metrics.
