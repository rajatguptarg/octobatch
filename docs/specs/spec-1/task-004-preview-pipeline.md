# TASK-004 Preview Pipeline and Artifact Handling

## Objective
Execute preview runs via sandboxed Kubernetes Jobs, store artifacts deterministically, and expose per-repo preview status, logs, and diffs without writing to GitHub.

## Job Runner design
- Consume `ExecuteTransform` tasks from Redis stream `preview.tasks`.
- Create K8s Job with:
  - **Init container**: clone repo at base ref using access token; volume-mount workspace.
  - **Main container**: executes ordered steps from spec; enforces per-step timeout via `bash -lc 'timeout ${STEP_TIMEOUT}s ...'`.
  - **Sidecar**: streams logs to stdout and uploads to Artifact Proxy.
- Security: runAsNonRoot, readOnlyRootFilesystem, seccomp `RuntimeDefault`, default deny egress with allowlist for GitHub.

## Artifact handling
- Artifact Proxy issues short-lived upload/download tokens scoped to `run_id/repo_slug`. Tokens minted via Token Service and validated with HMAC signature.
- Artifacts stored under `s3://{bucket}/preview/{run_id}/{repo_slug}/` with keys `logs.txt`, `patch.diff`, `summary.json`.
- Diff summaries include file stats, test outcomes, and patch hash.

## Timeout and redaction
- Per-step timeout defaults to 10 minutes; overall Job timeout 45 minutes with Kubernetes `activeDeadlineSeconds`.
- Log redaction filters tokens and secrets using regex patterns (`ghs_`, `AWS_SECRET_ACCESS_KEY`, etc.) before upload.

## UI/API surface
- `GET /runs/{run_id}/executions` returns status, log URI, patch URI, diff summary, exit code.
- UI displays status badges, streamable logs, and download links for patch/diff summary.
- Only repos with non-empty patch are flagged as `ReadyToPublish`.

## Tests
- E2E preview using sample repo to ensure patch upload/download works.
- Security context tests assert non-root uid/gid and network policy enforcement.
- Idempotency: dedupe key `preview:{run_id}:{repo}` prevents duplicate jobs.

## Rollback
- Pause preview consumer to stop launching new jobs.
- Remove network deny if clone failures traced to egress; reinstate after allowlist adjustment.
