# octobatch
Octobatch is a self-hosted platform for declaratively running large-scale code change campaigns across thousands of GitHub repositories. Define a campaign spec, preview changes safely, open pull requests in bulk with throttles, and continuously reconcile them until merged.

## What it does
- Campaign specs with validation and previews before publishing
- Throttled bulk PR publishing at org scale
- Continuous reconciliation to handle drift, failures, and retries
- Auditable runs with logs, artifacts, and status dashboards
- GitHub App-first security model (no branch protection bypass)

## Architecture (proposed)
- FastAPI control plane services for campaign management, selection, publishing, reconciliation, and tokens
- Redis Streams for queues, dedupe, and throttling
- Kubernetes Jobs for per-repo execution
- PostgreSQL as the system of record; S3-compatible storage for artifacts
- React UI and CLI consuming public APIs

## Documentation
- Product goals and user journeys: `docs/steering/product.md`
- Proposed repo structure: `docs/steering/structure.md`
- Tech stack and ops expectations: `docs/steering/tech.md`
- First spec package: `docs/specs/spec-1/spec-1.md`

## Status
Foundational FastAPI skeletons for the API Gateway, Campaign Service, Selection Service, and Token Service now live under `src/octobatch`. Each exposes `/healthz` to verify Postgres, Redis, blobstore, and GitHub API connectivity. A Helm chart (`helm/octobatch`) packages the services with default-deny NetworkPolicies and secret wiring for Postgres (`octobatch-postgres`), Redis (`octobatch-redis`), blob storage (`octobatch-blobstore`), and GitHub App credentials (`github-app-credentials`).
