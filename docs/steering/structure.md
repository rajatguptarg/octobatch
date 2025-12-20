# GitHub Campaigns for Bulk PRs – Structure

## Proposed Repo Layout

- `api/` – FastAPI gateway + routing, auth, webhook ingestion.
- `services/campaign/` – Campaign Service (specs, runs, execution orchestration).
- `services/selection/` – Selection Service (GitHub GraphQL discovery, caching).
- `services/publisher/` – Publisher worker and throttling logic.
- `services/reconciler/` – Reconcile worker processing webhooks/periodic sync.
- `services/token/` – Token Service for GitHub App installations and artifact tokens.
- `services/job-runner/` – Worker creating Kubernetes Jobs per repo-task.
- `services/artifact-proxy/` – Hardened upload/download facade to object storage.
- `ui/` – React frontend.
- `cli/` – CLI client.
- `charts/` – Helm chart and values examples.
- `docs/` – Architecture docs, runbooks, security/ops notes, ADRs.
- `scripts/` – Local tooling, schema/codegen helpers.
- `tests/` – Integration/e2e harness; service-specific tests colocated.

## Module Boundaries and Ownership

- Control plane services own their APIs and data slices in Postgres; shared models and clients live in a common library (avoid cyclic deps).
- Job Runner and Artifact Proxy own execution contracts and artifact schema.
- Publisher/Reconciler share GitHub client abstractions with rate-limit handling.
- UI/CLI consume public APIs only; no direct DB access.

## Naming Conventions

- Branches: `campaign/<campaign_id>/<spec_version>/<repo_slug>`.
- Queues/streams: `campaign_tasks`, `campaign_tasks_dlq`.
- Task IDs: UUID; dedupe keys: `sha256(campaign_id + repo + spec_version + task_type + desired_patch_hash)`.
- Table names as specified in design; migrations under `migrations/`.
- Config: environment variables prefixed per service (e.g., `CAMPAIGN_`, `PUBLISHER_`).

## Documentation Layout

- `docs/architecture.md` – component overviews and diagrams.
- `docs/operations.md` – deployment, scaling, throttles, backups, kill switch.
- `docs/security.md` – permissions, network policies, hardening, audit.
- `docs/runbooks/*.md` – incident handling (webhook backlog, queue saturation, publish failures).
- `docs/api/*.md` – API/CLI contracts, spec schema reference.

## Testing Conventions

- Unit tests near code; integration/e2e under `tests/` with service composition.
- Use fixtures for GitHub API mocks and Kubernetes client fakes.
- Load/performance scenarios scripted under `tests/load/`.
- Security/regression suites for sandboxing and throttle enforcement.

## ADR Strategy

- Store ADRs in `docs/adrs/ADR-YYYYMMDD-<topic>.md`.
- Record decisions on queue technology, artifact delivery model, drift policy defaults, and security posture.
- Include context, decision, alternatives, and consequences; link to requirements IDs when relevant.
