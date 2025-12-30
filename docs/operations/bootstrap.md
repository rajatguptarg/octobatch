# Octobatch Foundations and Bootstrap (TASK-001)

This document captures the deployment-ready scaffolding for Task-001. It wires external dependencies, configures secrets, and ships FastAPI skeletons for the API Gateway, Campaign Service, Selection Service, and Token Service. All services expose `/healthz` to verify connectivity to Postgres, Redis, blob storage, and the configured GitHub API base URL.

## External dependencies

Provision the following before deploying the Helm chart:

- **PostgreSQL**: connection string stored in the `octobatch-postgres` secret key `POSTGRES_DSN`.
- **Redis**: URL stored in the `octobatch-redis` secret key `REDIS_URL`.
- **S3-compatible storage**: endpoint + credentials stored in `octobatch-blobstore` secret keys `BLOBSTORE_ENDPOINT`, `BLOBSTORE_BUCKET`, `BLOBSTORE_ACCESS_KEY_ID`, `BLOBSTORE_SECRET_ACCESS_KEY`, `BLOBSTORE_SESSION_TOKEN` (optional).
- **GitHub App credentials**: stored in `github-app-credentials` keys `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`. Supports GitHub.com or GHES via `GITHUB_API_BASE_URL` Helm value.

## Running services locally

```bash
pip install -e .
export OCTOBATCH_POSTGRES_DSN="postgresql://user:pass@localhost:5432/octobatch"
export OCTOBATCH_REDIS_URL="redis://localhost:6379/0"
export OCTOBATCH_BLOBSTORE_ENDPOINT="http://localhost:9000"
export OCTOBATCH_BLOBSTORE_BUCKET="octobatch-artifacts"
export OCTOBATCH_BLOBSTORE_ACCESS_KEY_ID="minio"
export OCTOBATCH_BLOBSTORE_SECRET_ACCESS_KEY="minio123"
export OCTOBATCH_GITHUB_APP_ID="12345"
export OCTOBATCH_GITHUB_APP_PRIVATE_KEY="$(cat /path/to/private-key.pem)"

uvicorn octobatch.api_gateway.main:app --port 8000
uvicorn octobatch.campaign.main:app --port 8001
uvicorn octobatch.selection.main:app --port 8002
uvicorn octobatch.token.main:app --port 8003
```

Each service will serve `/healthz` for dependency checks. The token service also exposes `/tokens/installations/{installation_id}` to exchange the GitHub App credentials for an installation token, caching responses until just before expiry.

## Helm deployment

- Chart location: `helm/octobatch`.
- Values file: `helm/octobatch/values.yaml` sets service replicas, resource defaults, GitHub API base URL, secret names, and NetworkPolicy allowlists.
- Deploy: `helm upgrade --install octobatch helm/octobatch -f /path/to/values.override.yaml`
- Post-deploy verification: `kubectl get pods -l app.kubernetes.io/name=octobatch` then port-forward any pod and hit `/healthz`.

### Network policies

NetworkPolicies default to deny egress for each service, then allowlists:

- GitHub API (`networkPolicy.githubCidrs` on port 443)
- Postgres (`networkPolicy.postgresCidrs` on port 5432)
- Redis (`networkPolicy.redisCidrs` on port 6379)
- Blobstore (`networkPolicy.blobstoreCidrs` on port 443)
- DNS (enabled with `networkPolicy.allowDNS: true`, targeting kube-dns)

Populate CIDR lists per environment to unlock the required dependencies.

## Health expectations

The `/healthz` response includes:

- `postgres`, `redis`, `blobstore`, and `github_api` checks with latency measurements.
- `healthy` boolean summarizing all checks.

Missing configuration is treated as unhealthy to surface miswired secrets early.

## Token minting flow

1. Token Service reads the GitHub App ID and private key from the mounted secret.
2. It builds a JWT (`iss=app_id`, short-lived) and calls `POST /app/installations/{installation_id}/access_tokens` against the configured GitHub API base.
3. Responses are cached in-memory until `expires_at - 60s` by default; subsequent requests return the cached token until refreshed.
4. API Gateway can forward token requests or consumers can call the Token Service directly.

Use a non-production GitHub installation for CI integration testing to validate the minting path end-to-end.
