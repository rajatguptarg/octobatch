# TASK-003 Repo Selection Engine

## Objective
Select repositories via GitHub GraphQL with pagination, caching, and persistence of selection outcomes per run with reasons.

## GraphQL selection
- Use `search(query: $q, type: REPOSITORY, first: 100, after: $cursor)` for pagination.
- Cache repo metadata (id, nameWithOwner, defaultBranchRef) in Redis with TTL 24h and etags to minimize API calls.
- Support base URL override for GHES via `GITHUB_API_BASE`.
- Backoff logic: token bucket using Redis keys `rate_limit:{installation_id}`; exponential backoff on `rateLimit` errors.

## Materializing repo_targets
- Selection Service writes to `repo_targets` table:
  - `selected_bool`, `selection_reason` (query hit, include override), `excluded_reason` (pattern match, archived, forked, denied).
  - `last_evaluated_at` timestamp for re-selection.
- Dedupe key `selection:{campaign_id}:{spec_version}` ensures idempotent runs.
- Handles up to 5,000 repos by batching inserts and streaming pagination cursors.

## API/UI exposure
- Endpoint `POST /campaigns/{id}/selection-runs` triggers selection and returns run id.
- `GET /campaigns/{id}/selection-runs/{run_id}` returns status and counts.
- `GET /campaigns/{id}/repo-targets` supports pagination, filtering by selected/excluded, and includes reasons.
- UI displays repo table with columns: repo, default branch, status, reason.

## Tests
- Mock GraphQL responses to test pagination and cursor handling.
- Cache tests ensure repeated selection hits cached metadata and reduces API calls.
- Performance test: simulate 5,000 repos with throttled responses; verify completion under timeout budget.

## Rollback
- On rate limit errors, selection run retries with smaller page sizes (down to 50) and jittered delay.
- If caching causes stale data, invalidate Redis keys via versioned namespace per deployment.
