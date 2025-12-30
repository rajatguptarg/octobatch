# TASK-001 Foundations and Bootstrap

## Objective
Deploy the foundational infrastructure and skeleton services required to run GitHub campaign operations with secure credential handling and verified health.

## Components
- **PostgreSQL**: source of truth for campaign, spec, run, and credential metadata. Managed via an externally provided endpoint. Connection string stored in Kubernetes secret `octobatch-postgres`.
- **Redis**: queue, rate limits, and dedupe via streams and semaphores. Endpoint + auth stored in secret `octobatch-redis`.
- **S3-compatible storage**: artifact blob storage (logs, patches, diffs). Bucket + credentials stored in secret `octobatch-blobstore`.
- **Helm values**: `helm/octobatch/values.yaml` configured with endpoints, secrets, and per-service resources. Includes NetworkPolicies default-deny with GitHub/S3/DB/Redis allowlists.

## Deployable services
- **API Gateway**: FastAPI entrypoint with routes for health, campaign CRUD, token minting, selection, run orchestration.
- **Campaign Service**: owns campaigns/spec lifecycle, run creation, and orchestration hooks.
- **Selection Service**: GitHub GraphQL client wrapper; exposes selection run endpoints.
- **Token Service**: exchanges GitHub App private key + installation id for access tokens, caches tokens, and returns minting responses.

Deployments use Kubernetes Deployments with PodDisruptionBudgets and HorizontalPodAutoscalers (HPA). All pods run as non-root, drop capabilities, and mount secrets via projected volumes.

## GitHub App bootstrap
- Create GitHub App with permissions: `contents:read|write`, `pull_requests:read|write`, `metadata:read`, `members:read`, `checks:read`.
- Capture `app_id`, `installation_id`, `private_key` (PEM), `webhook_secret` in secret `github-app-credentials`.
- Allow configurable `GITHUB_API_BASE` (GitHub.com or GHES) via Helm value `github.apiBaseUrl`.

## Credential and token flow
1. Token Service loads private key from `github-app-credentials`.
2. Mint JWT signed with app key; exchange for installation access token via GitHub API at configured base URL.
3. Cache token with TTL minus 60s; expose `/tokens/installations/{installation_id}` returning `token`, `expires_at`, and `permissions`.
4. API Gateway proxies token requests to Token Service; consumers use returned token for GitHub operations.

## Health and verification
- `/healthz` endpoint on all services verifies dependency connectivity (Postgres, Redis, S3, GitHub API reachability with HEAD request).
- Readiness probes ensure migrations executed and caches warmed.
- CI integration test hits Token Service against GitHub sandbox using test installation to validate minting end-to-end.

## Deployment steps
1. Provision Postgres/Redis/S3 endpoints and secrets.
2. Render Helm chart with environment-specific values; apply to cluster.
3. Validate service health via `kubectl get deploy` and `kubectl port-forward` to run smoke tests.
4. Record installation ids and webhook endpoints for later reconciliation pipeline.

## Rollback
- Helm uninstall releases to remove deployments.
- Revoke installation tokens via GitHub if misconfigured permissions are detected.
- Use dry-run scopes when testing new permissions to minimize impact.
