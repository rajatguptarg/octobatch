# GitHub Campaigns for Bulk PRs – Tech

## Tech Stack

- **Backend**: FastAPI (Python) services for API Gateway, Campaign, Selection, Publisher, Reconciler, Token Service.
- **Queue**: Redis Streams with consumer groups for task distribution and dedupe.
- **Data Plane**: Kubernetes Jobs with init/main/sidecar containers; NetworkPolicies default deny egress.
- **Storage**: PostgreSQL (source of truth), Redis (cache/rate limits), S3-compatible object storage (e.g., dxflrs/garage, MinIO/S3) via Artifact Proxy.
- **Frontend**: React UI; CLI (language TBD, likely Go/Node/Python) using public APIs.
- **Integrations**: GitHub App (REST for writes, GraphQL for bulk reads), Helm for deployment packaging.

## Key Libraries and Rationale

- FastAPI for async HTTP handling and OpenAPI generation.
- Redis client with Streams support for XPENDING/XCLAIM recovery and token-bucket semantics.
- PostgreSQL ORM/migrations (e.g., SQLAlchemy + Alembic) for schema evolution and durability.
- GitHub REST/GraphQL clients with installation token refresh support.
- Kubernetes Python/Go client for Job creation and log retrieval.
- JWT library for artifact tokens and GitHub App JWTs.

## Build, Test, Lint, Format

- Backend: `uvicorn` for dev server; `pytest` for tests; `ruff`/`black` for lint/format.
- Frontend: `vite`/`webpack` build (to be chosen), `jest`/`react-testing-library` for tests, `eslint`/`prettier`.
- CLI: depends on language; include unit/integration tests and golden output tests.
- CI: run lint + unit + integration suites; build container images per service; helm chart lint.

## Data Storage and Schema Strategy

- PostgreSQL holds campaigns, specs (raw + normalized), runs, repo_targets, executions, changesets, audit_log, GitHub installations.
- Redis holds task streams, dedupe keys, throttles, concurrency semaphores, and caches of repo metadata.
- Object storage holds artifacts (patches, logs, diff summaries) under deterministic prefixes with retention defaults (30 days).
- Schema migrations versioned; backwards-compatible changes favored to avoid downtime.

## Authn/Authz

- GitHub App installation tokens for GitHub API access; Token Service handles mint/refresh.
- Service-to-service auth via short-lived JWTs; Artifact Proxy enforces scoped prefixes.
- UI/CLI auth via API tokens (exact provider TBD; assumption: GitHub-based session or local token).
- Respect branch protections and required checks; no bypass even with admin tokens.

## CI/CD Expectations

- Container images built per service; signed and scanned.
- Helm chart publishes versioned releases; values support GitHub API base URL, external deps, and security settings.
- Staged rollouts with smoke tests; ability to pause/rollback via Helm and queue consumers.

## Observability Tooling

- Metrics via Prometheus (queue depth, job latency, run duration, GitHub API errors, publish throughput, reconcile lag).
- Logs shipped to ELK/OTel-compatible sink with correlation IDs (campaign_id, run_id, repo, task_id).
- Tracing via OpenTelemetry instrumentation across services and GitHub client calls.
- Alerts on webhook latency, queue backlog, publish throughput below target, Artifact Proxy errors, and GitHub API failure spikes.

## Performance and Cost Considerations

- Throttled publish (150–200 PRs/day/org by default) to control API/maintainer load.
- Job resource limits set per step; default deny egress minimizes unnecessary bandwidth.
- Redis rate limits and concurrency caps prevent bursty GitHub API usage; backoff on secondary rate limits.
- Artifact size limits (e.g., 50MB patch, 200MB logs) to control storage costs; retention policies configurable.
- Horizontal scaling via HPA/KEDA on API and queue depth; Job Runner scales with queue backlog.
