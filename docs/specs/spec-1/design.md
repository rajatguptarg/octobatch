# GitHub Campaigns for Bulk PRs – Design

## Overview and Approach

Self-hosted control plane orchestrates declarative campaigns that transform many GitHub repos. A Kubernetes-backed data plane runs per-repo jobs in sandboxed containers. Declarative specs drive repo selection, preview, publish, and reconciliation. Durable state lives in Postgres; Redis Streams provide work queueing with idempotent tasks. Artifact Proxy isolates object storage access. Reconciliation aligns GitHub PRs with desired intent using webhooks and periodic syncs. Design emphasizes deterministic naming/hashes, throttles, and auditability. (Refs: REQ-001–REQ-014, NFR-001–NFR-005)

## Architecture

Control-plane services (API Gateway, Campaign Service, Selection Service, Publisher, Reconciler, Token Service, UI) run as Deployments. Redis Streams back task queues; Postgres stores campaigns/specs/runs/changesets. Artifact Proxy mediates uploads/downloads to S3-compatible storage. Job Runner posts per-repo tasks to Kubernetes Jobs in the data plane. GitHub App installation tokens authenticate GitHub API operations. Webhooks flow to API Gateway and enqueue reconcile work. NetworkPolicies enforce default deny egress for Jobs; per-org throttles enforced in Redis. (Refs: REQ-001–REQ-014)

## Components and Responsibilities

- **API Gateway**: Receives UI/CLI requests, enforces auth, validates specs, exposes run/status endpoints. (REQ-002, REQ-003, REQ-014)
- **Campaign Service**: Persists campaigns/specs/runs, computes hashes, enqueues tasks, watches Jobs, collects results/logs. (REQ-003, REQ-004, REQ-005)
- **Selection Service**: GitHub GraphQL discovery, caches repo metadata, materializes repo_targets snapshots. (REQ-004)
- **Job Runner**: Consumes ExecuteTransform tasks, creates K8s Jobs with init/main/sidecar containers, injects artifact tokens. (REQ-005, REQ-010)
- **Publisher**: Consumes publish/close/rebase/update tasks, pushes branches, creates/updates PRs with templates, enforces throttles. (REQ-006, REQ-008)
- **Reconciler**: Processes webhooks/periodic refresh, computes desired vs. actual changesets, enqueues actions per drift policy. (REQ-007, REQ-012)
- **Artifact Proxy**: Hardened upload/download for patches/logs/diff summaries; enforces prefix scoping and size limits. (REQ-005, REQ-013, NFR-004)
- **Token Service**: Mints short-lived installation tokens and artifact tokens. (REQ-002, REQ-010)
- **UI**: Spec editor, run dashboards, repo detail views, bulk actions; uses APIs only. (REQ-005, REQ-006, REQ-011)
- **CLI**: Mirrors apply/preview/publish via API. (REQ-014)

## Data Model

- **PostgreSQL tables**: `github_installations`, `campaigns`, `campaign_specs` (raw YAML + normalized JSON + spec_hash), `runs`, `repo_targets`, `executions`, `changesets`, `audit_log`. (REQ-001, REQ-003, REQ-004, REQ-007, REQ-009)
- **Redis Streams**: `campaign_tasks` with consumer groups `job-runner`, `publisher`, `reconciler`; dead-letter `campaign_tasks_dlq`. (REQ-005–REQ-008, NFR-003)
- **Artifacts in object storage**: `patch.diff|tar.gz`, `diff_summary.json`, `logs/`, optional artifacts per repo under deterministic prefixes. (REQ-005, REQ-013, NFR-004)
- **Deterministic keys**: `spec_hash`, `desired_patch_hash`, `dedupe_key = sha256(campaign_id + repo + spec_version + task_type + desired_patch_hash)`. (REQ-003, NFR-003)

## API / Interface Design

- **Spec endpoints**: Create/list/get specs; validate against schema; return spec_hash and normalized JSON. (REQ-003)
- **Runs**: `POST /runs` for preview/publish; `GET /runs/{id}` for status; `POST /runs/{id}/pause|resume|kill`. (REQ-005–REQ-008)
- **Repo targets**: List selection results with reasons; retry failed selection. (REQ-004)
- **Bulk actions**: Retry, close/unselect, rebase/update, update PR template; drift policy settings per campaign. (REQ-011, REQ-012)
- **Artifacts**: Signed URLs or proxy endpoints for patches/diffs/logs; access controlled by campaign/run scope. (REQ-005, REQ-013)
- **CLI**: Auth + commands `apply|preview|publish|status`; uses same APIs. (REQ-014)
- **Webhooks**: `pull_request`, `push`, `check_run`, `check_suite`, etc. received at API Gateway and normalized to reconcile tasks. (REQ-007)

## State Transitions and Key Flows

- **Campaign lifecycle**: Spec saved → selection snapshot → preview run (ExecuteTransform tasks) → publish run (PublishChangeset tasks) → reconcile loop updates states until merged/closed. (REQ-003–REQ-007)
- **Changeset state machine**: Unselected → Selected → Previewed → {NoChange|ReadyToPublish} → Publishing → Open → {Updating|NeedsHuman|Merged|Closed}. Updating loops to Open; failures return to Selected on retry. (REQ-007, REQ-012)
- **Reconcile triggers**: Webhooks (PR, pushes, checks) and periodic sync enqueue RefreshStatus/ReconcileRepo tasks; drift policy decides force-push, new PR, or needs-human flag. (REQ-007, REQ-012)
- **Throttling**: Publish tasks checked against per-org daily quota and concurrency semaphores before execution; tasks delayed with `not_before` when capped. (REQ-008, NFR-001)
- **Idempotency**: dedupe_key prevents duplicate in-flight tasks; Postgres terminal states make replays safe; branch names deterministic (`campaign/<campaign_id>/<spec_version>/<repo_slug>`). (REQ-006, NFR-003)

## Security and Privacy

- GitHub App least-privilege permissions; tokens short-lived and cached with expiry. (REQ-002)
- Jobs run non-root, read-only root filesystem, drop capabilities, seccomp=RuntimeDefault; default deny egress with optional allowlist. (REQ-010, NFR-004)
- Artifact Proxy isolates object storage credentials; size limits and optional malware scanning. (REQ-010, NFR-004)
- Audit log records all GitHub mutations and user actions with correlation IDs; secrets encrypted at rest. (REQ-009, NFR-004)
- Branch protection and org policies respected; no bypass of required checks/reviews. (REQ-002, REQ-008)

## Reliability and Failure Modes

- Redis Streams with consumer groups; stalled-task recovery via XPENDING/XCLAIM; dead-letter queue for inspection. (NFR-003)
- Visibility timeouts per task type; retries with backoff; job TTLs and sweepers for stuck resources. (REQ-010, NFR-003)
- Publish throttles prevent overload; kill switch/pause halts new publishes. (REQ-008)
- Webhook backstop via periodic reconcile to handle missed deliveries. (REQ-007, NFR-002)
- Object storage/Artifact Proxy outages degrade previews/publishes; tasks retry and surface errors; audit/logs persist locally until upload succeeds. (REQ-005, REQ-013)

## Observability

- Metrics: queue depth, job latency, run duration, per-step failure codes, GitHub API errors, publish throughput, reconciliation lag. (REQ-009, NFR-005)
- Logs: Structured logs with campaign_id/run_id/repo/task_id; pod logs collected and uploaded via Artifact Proxy. (REQ-005, REQ-009)
- Tracing: Propagate correlation IDs through control-plane services and GitHub mutations. (NFR-005)
- Alerts: API error rates, queue backlog thresholds, publish throughput below target, webhook processing latency breach. (REQ-009, NFR-002)

## Tradeoffs and Alternatives

- **Redis Streams vs. other queues**: Chosen for durability/backpressure and XPENDING recovery; alternative would be Postgres advisory locks or Kafka. (REQ-005, NFR-003)
- **Force-push vs. new PR**: Exposed via drift policy to balance determinism vs. maintainer friendliness. (REQ-012)
- **Sidecar result server vs. kubectl cp**: Sidecar avoids exec/tar complexity and keeps credentials scoped. (REQ-010)
- **Default deny egress**: Improves security but may slow steps requiring external fetches; allowlist is opt-in. (REQ-010, NFR-004)

## Rollout Plan

- Phase 1: Deploy core services (API, Campaign Service, Selection, Token Service), Postgres/Redis wiring, GitHub App bootstrap. (REQ-001–REQ-004)
- Phase 2: Preview pipeline with Job Runner, Artifact Proxy, UI preview views. (REQ-005, REQ-010, REQ-013)
- Phase 3: Publish pipeline with Publisher, throttles, PR template application. (REQ-006, REQ-008)
- Phase 4: Reconcile loop with webhooks + periodic sync; drift policies. (REQ-007, REQ-012)
- Phase 5: Bulk actions, CLI parity, optional P2 features (selection integrations, auto-merge, follow-ups). (REQ-011, REQ-014–REQ-017)
- Phase 6: Hardening, observability dashboards, security scans, HA tuning. (REQ-008–REQ-010, NFR-004–NFR-005)

## Appendix: Mapping to Requirements

- Architecture/components: REQ-001–REQ-014, NFR-001–NFR-005
- Data model: REQ-003–REQ-007, REQ-009, REQ-013, NFR-003–NFR-004
- API design: REQ-003–REQ-014
- Security: REQ-002, REQ-008–REQ-010, NFR-004
- Reliability/observability: REQ-005–REQ-009, NFR-002–NFR-005
- Rollout: aligns with phased delivery of REQ-001–REQ-017
