# TASK-011 Hardening, Observability, and Compliance

## Objective
Strengthen security controls, add observability, and validate performance/retention requirements.

## Observability
- Structured JSON logging with correlation ids (`x-request-id`, `run_id`, `repo`).
- Metrics via Prometheus: run durations, queue latency, GitHub API calls, token cache hits, job success rates.
- Dashboards for publish/preview throughput, error rates, and throttle utilization; alerts on SLA breaches.

## Security controls
- Enforce Pod security: runAsNonRoot, seccomp `RuntimeDefault`, read-only root filesystem, minimal capabilities.
- NetworkPolicies default deny; allow GitHub, Postgres, Redis, and S3 endpoints.
- Size limits: artifact uploads capped (e.g., 25MB) with validation in Artifact Proxy.
- Malware scanning hook on patches before publish.
- Secrets encrypted at rest using KMS-backed Kubernetes secrets or SealedSecrets.

## HA, backups, retention
- Postgres: streaming replicas and daily backups with tested restore procedures.
- Redis: persistence enabled with snapshotting; monitor replication lag.
- Artifact retention TTLs with lifecycle policies (e.g., delete previews after 30 days, publish artifacts after 180 days).

## Performance and scale testing
- Load tests for campaigns with 5,000 repos measuring queue depth, publish throughput, and reconcile latency.
- SLA validation for reconcile loop and throttle behavior under load.

## Tests and simulations
- Pen tests of egress blocking and privilege dropping in Jobs.
- Alert simulations to validate on-call wiring.

## Rollback
- Config flags to relax policies temporarily (e.g., increase size limits or disable malware scanning) while investigating regressions.
