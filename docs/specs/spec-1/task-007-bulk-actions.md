# TASK-007 Bulk Actions and Template Updates

## Objective
Provide bulk actions across changesets while respecting throttles and dedupe keys, including template updates.

## Bulk actions
- **Retry failed**: enqueue publish/preview reruns for changesets in `Failed` state; dedupe key `retry:{changeset_id}`.
- **Close/remove unselected**: for repos no longer matching selection, close PR and delete branch if policy allows.
- **Rebase/update all**: enqueue jobs to rebase campaign branches onto latest default branch and rerender patches.
- **Update PR templates**: re-render PR title/body/labels/reviewers for all open PRs when template fields change; update PR via GitHub API.

## API/UI
- Endpoint `POST /campaigns/{id}/bulk-actions` with payload `{action, target_filter}`; returns task batch id.
- UI presents confirmation dialogs showing affected counts and throttle impact estimates.
- Actions queued into Redis with throttles enforced via same counters/semaphores as publish pipeline.

## Safety and dedupe
- Every action carries dedupe key including campaign id, repo, and desired patch hash to avoid duplicate mutations.
- Bulk operations paused when publish pause flag set.
- Respect drift policies—do not force-push during rebase if policy is `needs_human`.

## Tests
- Idempotency tests ensure repeated bulk requests do not duplicate PR updates.
- Throttle compliance tests simulate large bulk updates hitting caps and confirm rescheduling.
- Template update tests verify PR metadata changes without altering commit content.

## Rollback
- Bulk queues can be paused to stop new tasks; existing PRs remain untouched until resume.
