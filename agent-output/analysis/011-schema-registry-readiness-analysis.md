Value Statement and Business Objective
Ensuring the translation service can register its schemas before entering the Kafka loop is the gatekeeper for the TTS pipeline: without successful `TextTranslatedEvent` output the downstream flow never fires, so uncovering and removing the schema-registry startup jam unlocks the e2e smoke tests and closes the QA evidence gap.

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | User | analyze why the e2e smoke test never receives AudioSynthesisEvent | Translation service keeps failing when calling the schema registry, so no translation events ever reach TTS and the smoke test waits forever. |

## Objective
Explain why the translation service is not producing `TextTranslatedEvent`, identify the systemic trigger, and highlight the infrastructure/code changes needed before the TTS e2e can succeed.

## Context
 - Relevant modules/files:
   - [services/translation/src/translation_service/main.py](services/translation/src/translation_service/main.py#L52-L176) (schema registration happens before the Kafka consumer loop, so any failure here aborts the service before it processes messages).
   - [shared/speech-lib/src/speech_lib/schema_registry.py](shared/speech-lib/src/speech_lib/schema_registry.py#L10-L32) (register_schema issues a single HTTP POST via `requests` and bubbles any ConnectionError directly to the caller; no retries or resilience around startup spikes exist).
   - [services/translation/src/translation_service/config.py](services/translation/src/translation_service/config.py#L10-L34) (SCHEMA_REGISTRY_URL defaults to http://schema-registry:8081, so the service always tries to reach the local registry as soon as it boots).
   - [docker-compose.yml](docker-compose.yml#L143-L190) (translation-service depends on schema-registry/kafka but `depends_on` does not wait for the registry to finish initializing, so registration attempts race with schema-registry readiness).
- Known constraints: schema registry takes several seconds to bind port 8081, the translation service exits immediately on unhandled ConnectionError because the schema registration is performed synchronously at startup, and there is no restart policy to resume progress once the registry becomes available.

## Methodology
- Inspected translation service logs with `docker compose logs translation-service --tail=200` to capture the repeated `ConnectionRefusedError` stack traces emitted while hitting schema-registry:8081.
- Confirmed there are no successful translation events by running `docker compose logs translation-service | grep "Published TextTranslatedEvent"` (grep returned nothing) while only one `Translation service started` message is present, proving the consumer loop never ran.
- Reviewed the startup code/config for schema registration and deployment wiring to understand why a single failure kills the service (`register_schemas` precedes consumer/producers, the schema registry client has no retry, and docker-compose has no awareness of registry health).

## Findings
### Facts
- The translation service log dump shows a `requests.exceptions.ConnectionError` when attempting to POST to `schema-registry:8081`, followed by a `MaxRetryError` and a crash before the Kafka consumer ever polls (all occurring during the `register_schemas` call in translation service main; the service never logs any `Published TextTranslatedEvent`).
- grep’ing for `Published TextTranslatedEvent` in the translation service logs returns no hits, so the service has never published a translation event for the TTS pipeline during this run.
- `register_schemas` is executed before any consumer or producer is created, and the `SchemaRegistryClient.register_schema` method raises immediately on failed HTTP calls; there is no retry/backoff, which means any schema-registry startup hiccup terminates the entire service instantly.
### Hypotheses
- Because docker-compose `depends_on` only waits for the container to start, the translation service tries to register its schemas before schema-registry has fully opened port 8081, triggering the ConnectionRefusedError and therefore exiting before any Kafka interaction, which leaves the TTS pipeline without translation events.
- Without a restart policy or persistent retry loop, the translation service never resumes when the registry becomes available, so even once schema-registry eventually starts (and the logs show other services registering their schemas), translation output never appears and the e2e test times out.

## Recommendations
- Add a resilient startup wrapper around `register_schemas`, e.g., retry/ backoff logic with exponential delays and a log-once guard, so the translation service keeps attempting to register until schema-registry is reachable instead of crashing on the first refusal.
- Introduce a readiness gate for schema-registry (a healthcheck or a wait-for-it script) and wire `translation-service` startup to that check, because `depends_on` alone does not prevent racing with the registry’s initialization window.
- Configure the translation-service container with a restart policy (for instance `restart: on-failure`) or keep the process alive while waiting, so it can recheck schema-registry readiness without manual intervention; once the service finally registers, rerun the e2e smoke tests to verify `AudioSynthesisEvent` arrives.

## Open Questions
- Should the schema registry client expose a reusable wait-for-schema loop that other services can share, or should each service implement its own retry/backoff? 
- Do we want to gate the entire deployment on a healthcheck that confirms schema-registry is ready to serve `/subjects` before any service performs registration, to prevent race conditions in the future?

## Handoff
## Handoff to Implementer
**From**: Analyst
**Artifact**: agent-output/analysis/011-schema-registry-readiness-analysis.md
**Status**: Complete
**Key Context**:
- Translation service exits before consuming because schema registration is synchronous and not resilient to schema-registry startup delays.
- SchemaRegistryClient simply raises on HTTP failures (no retry) and docker-compose `depends_on` does not avoid the race with schema-registry readiness.
**Recommended Action**: Implement resilient schema registration (retry/backoff or readiness check) and/or a schema-registry healthgate plus restart policy, then rerun the e2e smoke tests to ensure the pipeline finally emits `TextTranslatedEvent` and `AudioSynthesisEvent`.