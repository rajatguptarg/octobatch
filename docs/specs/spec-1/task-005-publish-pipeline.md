# TASK-005 Publish Pipeline and Throttles

## Objective
Create deterministic branches/PRs for repos with patches, enforce throttles via Redis, and persist changeset records with pause/kill controls.

## Publish flow
1. Consume `Publish` tasks from Redis stream `publish.tasks` keyed by `run_id` and `repo`.
2. Fetch patch from artifact storage; apply atop base branch; commit with deterministic message and author `Octobatch Bot <bot@octobatch>`.
3. Branch naming: `campaign/{campaign_id}/{spec_version}/{slug}`.
4. Push via installation token; create PR with template fields (title/body/labels/reviewers/assignees/draft flag).
5. Persist `changesets` row with PR URL, head/base SHAs, desired patch hash, desired branch, and state transitions.

## Throttles and concurrency caps
- Redis counter `pr_daily:{org}` with TTL midnight; cap default 200/day/org.
- Redis semaphore `publish_concurrency:{org}` limits concurrent GitHub API calls.
- If throttle exceeded, task rescheduled with `not_before` and backoff.

## Duplicate safety
- Dedup key `publish:{campaign_id}:{repo}:{desired_patch_hash}` prevents duplicate PR creation.
- If PR exists with same branch, update PR body/labels instead of creating new.

## Controls
- API endpoints to pause/resume publish consumer and adjust throttles per org.
- UI displays publish queue depth, remaining quota, and per-repo status.
- Kill switch sets `publish.disabled=true` in config to stop consuming new tasks.

## Tests
- Integration tests against GitHub sandbox to verify branch determinism and PR creation.
- Throttle boundary tests simulate hitting caps and ensure rescheduling.
- Retry/backoff coverage for transient failures.

## Rollback
- Pause consumer to halt new publishes; already-created branches/PRs remain.
- Closing PRs or deleting branches left to operator discretion.
