# TTS Validation Performance Report

Phrases source: /app/tests/data/metrics/tts_phrases.json
Iterations per phrase: 10

## Latency (Synthesis Only)
- P50: 769.36 ms
- P95: 1226.41 ms

## Real-Time Factor (RTF)
- Mean RTF: 0.297
- P50 RTF: 0.285

## Speed Control
- Speed A: 1.0
- Speed B: 1.2
- Duration A: 1600.00 ms
- Duration B: 1350.00 ms
- Delta: -15.62%

## Notes
- Latency reflects local synthesis time only (no Kafka/MinIO upload).