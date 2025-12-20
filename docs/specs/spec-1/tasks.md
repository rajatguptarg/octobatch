# GitHub Campaigns for Bulk PRs – Tasks

## Execution Plan

- Phase 1: Foundations (deploy scaffolding, persistence, GitHub App bootstrap).
- Phase 2: Spec ingestion and repo selection.
- Phase 3: Preview pipeline (jobs, artifacts, UI).
- Phase 4: Publish pipeline (branches, PRs, throttles).
- Phase 5: Reconcile loop (webhooks + periodic sync, drift policies).
- Phase 6: Bulk actions and CLI parity.
- Phase 7: Hardening, observability, and security controls.
- Phase 8: Optional P2 capabilities (selection integrations, auto-merge, follow-ups).

## Task List

### TASK-001 Foundations and Bootstrap

- **Implements**: REQ-001, REQ-002, NFR-001, NFR-004
- **Steps**:
  - Provision Postgres, Redis, and S3-compatible storage endpoints; configure Helm values.
  - Deploy API Gateway, Campaign Service, Selection Service, Token Service skeletons.
  - Create GitHub App, capture installation details, configure base API URL (GitHub.com or GHES).
  - Wire GitHub App credential storage and token minting flow.
- **Definition of Done**: Services deploy on Kubernetes; health checks pass; Token Service returns installation token; external dependencies reachable.
- **Test Notes**: Integration test token minting against GitHub API (sandbox); connectivity checks to Postgres/Redis/object storage.
- **Risk / Rollback**: Misconfigured GitHub App permissions—use dry-run token scopes; rollback via Helm uninstall.

### TASK-002 Spec Schema and Versioning

- **Implements**: REQ-003, NFR-003
- **Steps**:
  - Define JSON schema for campaign spec; implement YAML → normalized JSON conversion with stable ordering.
  - Persist campaign metadata, specs, and spec_hash; expose CRUD endpoints.
  - Store spec versions per campaign with audit entries.
- **Definition of Done**: Saving a spec validates against schema, stores raw + normalized forms, and returns spec_hash; version history viewable.
- **Test Notes**: Schema validation unit tests; spec hashing determinism tests; API contract tests.
- **Risk / Rollback**: Schema drift—version schemas and gate incompatible changes; rollback schema migrations carefully.

### TASK-003 Repo Selection Engine

- **Implements**: REQ-004, NFR-001
- **Steps**:
  - Implement GitHub GraphQL selection with pagination and caching of repo metadata/default branches.
  - Materialize repo_targets per run with inclusion/exclusion reasons.
  - Expose selection results via API/UI.
- **Definition of Done**: Selection run persists repo_targets for a spec; UI/API returns repo list with reasons; handles 5,000 repos within limits.
- **Test Notes**: Mock GitHub GraphQL; pagination and cache tests; performance test on large repo sets.
- **Risk / Rollback**: GraphQL rate limits—apply backoff and token-bucket; fallback to smaller page sizes.

### TASK-004 Preview Pipeline and Artifact Handling

- **Implements**: REQ-005, REQ-010, REQ-013, NFR-003, NFR-004
- **Steps**:
  - Build Job Runner to consume ExecuteTransform tasks and create K8s Jobs with init/main/sidecar containers.
  - Implement artifact token minting and Artifact Proxy upload/download for patches/diff summaries/logs.
  - Enforce per-step timeouts, default deny egress, non-root pods, and redaction of secrets in logs.
  - UI/API surfaces per-repo preview status, logs, and patch/diff summary retrieval.
- **Definition of Done**: Preview run executes without writing to GitHub; artifacts stored under deterministic prefixes; logs accessible; sandboxing defaults enforced.
- **Test Notes**: E2E preview on sample repos; security context checks; artifact size/retention tests; dedupe key idempotency tests.
- **Risk / Rollback**: Misconfigured egress blocks repo clones—allowlist GitHub domains; disable preview queue consumption to pause.

### TASK-005 Publish Pipeline and Throttles

- **Implements**: REQ-006, REQ-008, NFR-001, NFR-003
- **Steps**:
  - Implement publish tasks to create deterministic branches, commits, pushes, and PRs with template fields.
  - Enforce per-org daily PR throttles and API concurrency caps via Redis counters/semaphores.
  - Persist changeset records with PR URLs/SHAs and link to spec version.
  - UI/API controls for pause/resume/kill and throttle configuration.
- **Definition of Done**: Publish run creates PRs only for repos with patches; never exceeds daily cap; duplicate runs do not create extra PRs; pause/kill halts new publishes.
- **Test Notes**: Integration against test org; throttle boundary tests; branch determinism tests; retry/backoff behavior.
- **Risk / Rollback**: Rate-limit bursts—backoff and schedule with not_before; rollback by pausing publisher consumer.

### TASK-006 Reconcile Loop and Drift Policies

- **Implements**: REQ-007, REQ-012, NFR-002, NFR-003
- **Steps**:
  - Ingest GitHub webhooks (PR, push, checks) and enqueue RefreshStatus/ReconcileRepo tasks.
  - Add periodic sync to backstop missed webhooks.
  - Implement drift policies: force-push overwrite, open new PR, needs-human state.
  - Update changeset state machine and UI indicators accordingly.
- **Definition of Done**: Spec edits or base drifts trigger reconcile actions per policy within SLA; states reflect merged/closed/needs-human; periodic sync running.
- **Test Notes**: Simulated webhook flows; base-branch advancement tests; drift policy behavior tests; SLA timing checks.
- **Risk / Rollback**: Webhook outages—rely on periodic sync; misapplied force-push—default to needs-human policy for safety.

### TASK-007 Bulk Actions and Template Updates

- **Implements**: REQ-011, REQ-012
- **Steps**:
  - Add API/UI bulk actions: retry failed, close/remove unselected targets, rebase/update all, update PR templates.
  - Ensure actions respect throttles and dedupe keys.
- **Definition of Done**: Bulk actions available and reflected in task queue; actions respect throttles and drift policies.
- **Test Notes**: Bulk rebase/update on sample PRs; retry idempotency; template update propagation.
- **Risk / Rollback**: Large bulk updates hitting caps—queue with not_before; rollback by pausing consumer.

### TASK-008 CLI Parity

- **Implements**: REQ-014
- **Steps**:
  - Implement CLI commands `apply|preview|publish|status` using API authentication.
  - Provide config for API base URL and GitHub App auth flow.
- **Definition of Done**: CLI can run end-to-end preview/publish equivalent to UI; outputs reference campaign/run IDs.
- **Test Notes**: CLI integration tests against staging; auth fallback tests.
- **Risk / Rollback**: Version skew—include API version negotiation; rollback by disabling CLI publish command flag.

### TASK-009 Optional Selection Integrations and Auto-merge

- **Implements**: REQ-015, REQ-016
- **Steps**:
  - Add optional selection sources (CODEOWNERS/teams/catalog) pluggable into selection service.
  - Allow campaign-level auto-merge configuration when checks/approvals satisfied.
- **Definition of Done**: Optional sources selectable; resolved repos appear in repo_targets; auto-merge toggles in PR creation/update flow.
- **Test Notes**: Integration tests with mock CODEOWNERS/teams; auto-merge enabling under satisfied checks; ensure policy respect.
- **Risk / Rollback**: Mis-selection—gate behind feature flags; disable auto-merge flag by config.

### TASK-010 Follow-up Workflows

- **Implements**: REQ-017
- **Steps**:
  - Add hooks for post-merge actions (e.g., create tracking issues, trigger deployments) configurable per campaign.
  - Execute via queue tasks with dedupe and retries; record in audit log.
- **Definition of Done**: Post-merge actions can be configured and run with audit entries; failures retried or surfaced in UI.
- **Test Notes**: Mock follow-up actions; audit log coverage; retry and idempotency tests.
- **Risk / Rollback**: Downstream side effects—ship with off-by-default flag; rollback by disabling hooks.

### TASK-011 Hardening, Observability, and Compliance

- **Implements**: REQ-008–REQ-010, REQ-013, NFR-002–NFR-005
- **Steps**:
  - Implement metrics/alerts dashboards; structured logging with correlation IDs.
  - Enforce security contexts, NetworkPolicies, size limits, malware scanning hook, secret encryption.
  - Add HA and backup guidance; TTL/retention for artifacts.
  - Run performance tests to validate scale/throttles and reconcile SLAs.
- **Definition of Done**: Observability dashboards live; alerts configured; security controls verified; SLAs measured; documentation updated.
- **Test Notes**: Pen tests of egress blocking; load tests for 5,000-repo campaigns; alert firing simulations.
- **Risk / Rollback**: Over-restrictive policies blocking jobs—allowlist adjustments; rollback via config toggles.
