# Analysis 013: MinIO Default Credentials in TTS Claim Check Path

## Value Statement and Business Objective
**User Story**: As a security-focused stakeholder, I want to ensure sensitive audio artifacts are not exposed through weak object-store credentials, so that Claim Check storage does not become a lateral attack vector.  
**Business Objective**: Harden the MinIO-backed Claim Check pilot by eliminating default credentials and documenting how every environment injects secrets and limits credential reuse.

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner → Analyst | Dive into the highlighted security finding about MinIO credentials | Verified the current compose/service configuration and summarized root cause, scope, and remediation steps before implementation. |

## Scope
- **Suspected files/endpoints**: `docker-compose.yml` MinIO/minio-init services, `services/tts` runtime configuration (`MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`), and any documentation referencing local credential defaults.
- **Risk surface**: Credential reuse beyond localhost (e.g., pushing compose to a shared test cluster, Gateway fetching objects, or exposing MinIO console through a VPN or CLI).

## Objective
Confirm whether default `minioadmin/minioadmin` credentials are hardcoded in the stack, evaluate how the TTS service consumes them, and document the impact of not rotating them in non-local environments.

## Methodology
- Inspected `docker-compose.yml` to see how MinIO is configured (image, ports, env vars) and how dependent services (like `tts-service`) reference MinIO credentials.
- Cross-referenced the plan/security artifacts to ensure this configuration remains in scope for v0.5.0 (Plan 010 lists MinIO env vars; Security control requires unique creds beyond localhost).
- Matched the plan’s `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` defaults against the compose service env to confirm the risk is systemic rather than isolated.

## Findings
### Fact 1 – Static credentials in compose
`docker-compose.yml` (services `minio` and `minio-init`) sets `MINIO_ROOT_USER: minioadmin` and `MINIO_ROOT_PASSWORD: minioadmin` and uses the `minio/minio:latest` image. The MinIO console and S3 APIs therefore use well-known credentials for every local bring-up.

### Fact 2 – Consumer services replicate the default
The `tts-service` environment section (same compose file) injects `MINIO_ACCESS_KEY: minioadmin` and `MINIO_SECRET_KEY: minioadmin`, so the service bootstraps with the same defaults even if MinIO were reconfigured or deployed elsewhere.

### Fact 3 – Exposure beyond localhost is plausible
While ports are bound to `127.0.0.1` in compose, the same docker file (or derivative) could be deployed to shared staging or test clusters where localhost binding is not enforced. Without credential rotation, any host or service with access to the network namespaces can enumerate audio objects (via `mc` or `curl`).

### Hypothesis – Risk persists unless secrets are injected
If CI/CD pipelines or developers copy the compose stack to other environments, they may not update these credentials (the plan even defaults to `minioadmin`). Attackers with limited network reach could reuse these credentials to download or delete Claim Check objects, leading to information disclosure or tampering.

## Impact
- **Confidentiality**: Sensitive audio transcripts and synthesized speech stored under `tts-audio` could be exfiltrated using default creds. This undermines the privacy intention of Claim Check and may expose translation results or speaker context.
- **Integrity/Availability**: Anyone with knowledge of the defaults can delete buckets or overwrite `tts/{correlation_id}.wav` objects, breaking the XOR contract and potentially invalidating audits or QA evidence.

## Recommendations
1. **Inject secrets per environment**: Require `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` to be provided via env injection (Docker secrets, `.env`, or Vault) with explicit gating that refuses to start if the values equal the defaults. Document this in `agent-output/planning/010-text-to-speech-plan.md` and gate QA runs by verifying non-default values.
2. **Pin the image and rotation cadence**: Upgrade the `minio/minio` image to a pinned tag/digest and record a rotation/update cadence for credentials so that brute-forcing the default becomes a moving target.
3. **Confine sensitive ports to localhost by default**: Keep the `127.0.0.1` binds for compose but add a warning to the plan/security docs that exposing MinIO beyond localhost requires TLS, auth, and rotated credentials.
4. **Audit the TTS config**: Ensure no code or tests ship with hardcoded `minioadmin` values; prefer deriving credentials from environment or a secrets provider with a clear override mechanism.

## Next Steps
- Update Plan 010 and QA instructions to reference credential gating and include an automated check for default values during local/e2e runs.
- When prepping for Epic 1.8 rollout, treat MinIO credentials as a security artifact (rotate per environment, integrate with gateway user perm controls).
- Document the risk and remediation in release notes so auditors understand how the Claim Check storage is protected.
