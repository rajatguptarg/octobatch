# TASK-010 Follow-up Workflows

## Objective
Execute configurable post-merge actions with dedupe, retries, and audit coverage.

## Actions
- Create tracking issues in specified repo/project with links to merged PRs.
- Trigger deployment webhooks or CI pipelines with payloads referencing campaign and repo.
- Send notifications (Slack/webhook) summarizing merged PR outcomes.

## Execution model
- Campaign config includes `followUps[]` with `{type, config, dedupeKeyTemplate, retries, backoff}`.
- After detecting PR merge, enqueue `FollowUp` task with dedupe key `followup:{campaign_id}:{repo}:{action}`.
- Worker executes action with retry policy and records result.

## Audit and observability
- Audit log entry per action with status, payload, and response code.
- Metrics: success/failure counts, retry counts, duration histograms.

## Tests
- Mock actions to ensure retries and dedupe behave as expected.
- Audit log coverage tests verifying entries created for success/failure.
- Idempotency tests to ensure duplicate merge events do not duplicate actions.

## Rollback
- Feature flag `followUps.enabled` default false; disable to halt new actions.
- Failed actions surfaced in UI with retry option for operators.
