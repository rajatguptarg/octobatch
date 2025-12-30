# TASK-006 Reconcile Loop and Drift Policies

## Objective
Ingest GitHub webhooks and periodic syncs to reconcile changesets when specs or base branches change, applying drift policies per campaign.

## Webhook ingestion
- Accept `pull_request`, `push`, and `check_suite` events at `/webhooks/github` with signature verification using webhook secret.
- Map events to `RefreshStatus` or `ReconcileRepo` tasks enqueued into Redis.
- De-dupe using `github_delivery_id` stored in audit log to avoid double-processing.

## Periodic sync
- Cron-like scheduler enqueues `RefreshStatus` for open changesets every 30 minutes to backstop missed webhooks.
- Sync retrieves PR state (merge status, head/base SHAs, checks) and updates `changesets.state` accordingly.

## Drift policies
- Policy stored on campaign: `overwrite` (force-push), `new_pr`, `needs_human`.
- Reconciler compares desired patch hash vs actual head SHA + diff; determines action:
  - **overwrite**: re-run preview/publish, force-push branch with updated patch.
  - **new_pr**: create new deterministic branch suffix `/v{n}` and open new PR, closing old with note.
  - **needs_human**: mark state `NeedsHuman` and post PR comment requesting manual resolution.

## State machine updates
- Reconciler transitions `changesets` based on PR state, merges, closes, or drift detections.
- Audit log records every reconcile action with event source (webhook vs sync) and policy applied.

## Tests
- Simulated webhook payloads to assert task enqueueing and signature validation.
- Base advancement test ensures overwrite/new_pr/needs_human behaviors occur per policy.
- SLA tests verify reconcile within target window (e.g., <5 minutes from webhook receipt).

## Rollback
- If webhook ingestion failing, rely on periodic sync to maintain state until fixed.
- Default drift policy `needs_human` used for safety when policy missing or misconfigured.
