# GitHub Campaigns for Bulk PRs – Requirements

## Summary

Self-hosted, Kubernetes-based system for running declarative bulk pull request campaigns across GitHub organizations. Users define a campaign spec (targets, steps, PR template), preview changes safely, publish PRs with throttles, and continuously reconcile desired vs. actual GitHub state with auditability and sandboxed execution.

## Goals

- Let orgs apply the same change across 1,000–5,000 repos with throttled, auditable PR creation.
- Provide a declarative campaign spec with deterministic execution and reconciliation.
- Offer safe preview, publish, and drift-handling workflows that respect branch protections and org policies.
- Deliver observability, audit trails, and secure sandboxed execution for self-hosted deployments.

## Non-goals

- Cross-forge support (GitLab/Bitbucket).
- Granting privileged network access to workers by default.

## Scope

- Self-hosted deployment on Kubernetes with external Postgres, Redis, object storage.
- GitHub App integration (GitHub.com or GHES) for repo discovery, patch application, and PR lifecycle.
- Control plane (API, selection, reconciliation, publisher) and data plane (per-repo Kubernetes Jobs).
- UI + CLI for defining specs, previewing, publishing, and monitoring campaigns.

## Personas / Actors

- Platform engineer / release engineer: defines and runs campaigns.
- Org admin: configures GitHub App installation and policies.
- Reviewer/maintainer: receives PRs and may need to interact with drift handling.
- System operator/SRE: deploys and monitors the self-hosted installation.

## Assumptions

- Customer provides reachable Postgres, Redis, and S3-compatible object storage endpoints.
- GitHub App has required fine-grained permissions per org/repo selection.
- Kubernetes cluster supports network policies and restricted pod security settings.

## Requirements

### Functional Requirements

- **REQ-001 Deployment**: System runs self-hosted on Kubernetes with configurable GitHub API base URL (GitHub.com or GHES) and uses customer-provided Postgres, Redis, and S3-compatible storage.
- **REQ-002 GitHub App Auth**: Authenticate via GitHub App installations with fine-grained permissions, using installation access tokens and honoring org policies (SSO, required reviews/checks).
- **REQ-003 Campaign Spec & Storage**: Store campaign metadata and versioned declarative specs defining repo selection, steps, policies, and PR templates with deterministic hashes.
- **REQ-004 Repo Selection**: Resolve target repos via GitHub GraphQL search/pagination, cache metadata, and materialize `repo_targets` per run with inclusion/exclusion reasons.
- **REQ-005 Preview Runs**: Execute preview without GitHub writes; produce per-repo status (no change/patch/failed), logs, and stored patch/diff summaries.
- **REQ-006 Publish Runs**: For repos with changes, create deterministic branch/commit/push/PR applying the spec PR template (title/body/labels/reviewers/assignees).
- **REQ-007 Reconcile Loop**: Webhook + periodic reconciliation keeps PRs aligned with desired state when spec changes, base drifts, repo selection changes, or PRs merge/close.
- **REQ-008 Safety Controls**: Enforce per-org publish throttles, API concurrency caps, kill switch, pause/resume, idempotent jobs, and branch-protection-aware writes.
- **REQ-009 Observability & Audit**: Immutable audit log for actions; metrics for runs and API usage; link every PR/branch to campaign and spec version.
- **REQ-010 Execution Sandboxing**: Per-repo Kubernetes Jobs run steps with deterministic images, per-step timeouts, secret redaction, and default egress deny (allowlist optional).
- **REQ-011 Bulk Actions**: Support retries, close/remove targets, rebase/update all, and PR template updates.
- **REQ-012 Drift Policies**: Provide per-campaign drift options: overwrite (force-push), open new PR, or mark “needs human.”
- **REQ-013 Structured Diff Summaries**: Store git diff and file-level stats for UI rendering and search.
- **REQ-014 CLI**: CLI supports apply/preview/publish flows for power users.
- **REQ-015 Repo Selection Integrations**: (Could) Support additional selection sources such as CODEOWNERS/teams/catalog.
- **REQ-016 Auto-merge Policies**: (Could) Allow enabling GitHub auto-merge when checks and approvals are satisfied and org settings allow.
- **REQ-017 Follow-up Workflows**: (Could) Trigger post-merge tasks (e.g., tracking issues, deployment triggers).

### Non-Functional Requirements

- **NFR-001 Scale & Throttle**: Handle 1,000–1,500 repos per campaign (max 5,000) with default publish throttle 150–200 PRs/day/org (configurable).
- **NFR-002 Performance & Latency**: Webhook deliveries processed within 2 minutes; reconciliation converges within 15 minutes steady state.
- **NFR-003 Reliability & Idempotency**: Jobs and tasks are idempotent, keyed by deterministic dedupe keys with retry/backoff; Postgres is source of truth.
- **NFR-004 Security & Isolation**: Default deny egress for jobs, non-root restricted pods, no object-storage credentials in jobs; secrets encrypted; audit for all GitHub mutations.
- **NFR-005 Observability Coverage**: Metrics for queue depth, job latency, run duration, failure reasons, GitHub API errors, publish throughput; logs and traces include campaign/run/repo/task correlation.

## Acceptance Criteria

- **REQ-001**: Helm values accept external Postgres/Redis/object storage endpoints and GitHub API base URL; deployment succeeds on Kubernetes with all services running.
- **REQ-002**: GitHub App installation tokens retrieved on demand; actions fail if required reviews/checks are missing rather than bypassing protections.
- **REQ-003**: Saving a spec stores versioned YAML/normalized JSON, computes `spec_hash`, and retains history per campaign.
- **REQ-004**: Running selection for a spec persists `repo_targets` with inclusion/exclusion reasons and default branch metadata.
- **REQ-005**: Preview run completes without creating branches/PRs and reports per-repo status plus stored patch/log artifacts retrievable via UI/API.
- **REQ-006**: Publish run creates deterministic branch names, commits, pushes, and PRs with spec-defined template fields for all repos with patches; no duplicates.
- **REQ-007**: On spec edit or base drift, reconciler updates or flags existing PRs according to drift policy; closed/merged PRs reflected in state within SLA.
- **REQ-008**: Throttle prevents exceeding configured PRs/day/org; kill switch or pause halts new publishes; concurrency caps enforced per org.
- **REQ-009**: Every GitHub mutation and user action appears in audit log with campaign/repo identifiers; metrics dashboards show run and API usage.
- **REQ-010**: Jobs run with default egress denied, non-root, read-only root FS; per-step timeouts enforced; secret values redacted from logs.
- **REQ-011**: Users can retry failed targets, close/remove unselected targets, rebase/update all open PRs, and update PR templates via bulk actions.
- **REQ-012**: Drift policy is configurable per campaign and reflected in reconcile behavior (force-push vs. new PR vs. needs-human state).
- **REQ-013**: Diff summaries stored with file-level stats and retrievable for UI search/rendering for each execution.
- **REQ-014**: CLI can authenticate, validate spec, run preview, and publish flows equivalent to UI flows.
- **REQ-015**: (If delivered) Additional selection sources (e.g., CODEOWNERS/teams/catalog) can be configured and resolve to repo targets.
- **REQ-016**: (If delivered) Auto-merge can be toggled per campaign and activates when checks/approvals satisfied per org rules.
- **REQ-017**: (If delivered) Post-merge workflows can trigger configured follow-up actions per campaign.
- **NFR-001**: Campaign with 5,000 repos can complete selection; publish run never exceeds configured daily PR cap.
- **NFR-002**: 99% webhooks processed under 2 minutes; reconcile steady-state lag under 15 minutes in test runs.
- **NFR-003**: Re-running the same task with identical dedupe key produces no duplicate side effects; retries use backoff and dead-letter.
- **NFR-004**: Security scan shows no pods run privileged; artifact uploads happen only via proxy without object-storage creds in pods.
- **NFR-005**: Metrics/logs include campaign_id, run_id, repo, and task_id; dashboards/alerts available for GitHub API errors, queue backlog, and publish throughput.

## Open Questions

- Do we need multi-tenant isolation within a single deployment beyond per-installation scoping?
- Which external identity provider (if any) governs UI/CLI auth beyond GitHub App scoping?
- Are there retention requirements beyond the stated 30-day default for logs/patches?
- Do we need regional deployments or data residency controls for object storage?
