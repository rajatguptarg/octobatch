# TASK-002 Spec Schema and Versioning

## Objective
Define the campaign spec schema, normalize and hash specs deterministically, and persist versions with full CRUD and auditability.

## JSON schema
- Root object with fields `name`, `description`, `targets`, `steps`, `changesetTemplate`, and optional `policies`.
- `targets`: `org`, `query` (string), `exclude` (array of repo patterns), `include` (explicit repo list), `pinnedRef` (optional branch/SHA).
- `steps`: array of objects `{image, command[], env?, timeoutSeconds?}` with required pinned image digests.
- `changesetTemplate`: `{branch, commitMessage, prTitle, prBody, labels[], reviewers[], assignees[], draft?}`.
- `policies`: `{publishThrottlePerOrg, driftPolicy, closeOnUnselect, rebaseMode}` with enums for drift policy (`overwrite|new_pr|needs_human`) and rebase mode (`auto|manual|disabled`).

Schema stored at `schemas/campaign-spec/v1.json` with versioned `$id` and `$schema`. Future changes add `v2` without mutating `v1`.

## Normalization and hashing
- Accept YAML input; parse to canonical JSON using sorted object keys and stable array ordering.
- Remove null/empty optional fields during normalization.
- Compute `spec_hash = sha256(normalized_json_bytes)`.
- Persist both `raw_yaml` and `normalized_json` for audit.

## Persistence and CRUD
- API endpoints:
  - `POST /campaigns/{id}/specs`: validate against schema, normalize, hash, store new version.
  - `GET /campaigns/{id}/specs/{version}`: return raw + normalized + hash.
  - `GET /campaigns/{id}/specs`: list versions with metadata.
  - `DELETE /campaigns/{id}/specs/{version}`: soft-delete with audit entry.
- Database columns: `campaign_specs.version` auto-incremented per campaign; `spec_hash` unique per `(campaign_id, spec_hash)`.

## Version history and audit
- Insert audit log entry for every create/update/delete with actor, campaign_id, version, and hash.
- Expose version history UI with entries: `{version, created_at, created_by, spec_hash}`.
- Enforce immutability: updating a spec creates a new version rather than editing previous rows.

## Tests
- Unit tests validate schema; invalid fields rejected.
- Determinism tests: identical YAML (with different ordering) yield identical `normalized_json` and `spec_hash`.
- API contract tests for CRUD routes and version ordering.

## Rollback and compatibility
- Keep prior schema versions available; gate incompatible changes behind feature flag `specSchemaVersion`.
- Database migrations backward-compatible by preserving existing columns and indexes.
