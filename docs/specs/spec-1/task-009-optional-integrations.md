# TASK-009 Optional Selection Integrations and Auto-merge

## Objective
Add optional selection sources and configurable auto-merge for campaigns when checks/approvals are satisfied.

## Selection integrations
- **CODEOWNERS**: parse org-level CODEOWNERS files to include repos owned by specified teams/users.
- **Teams API**: query GitHub teams and map to repositories via REST `GET /orgs/{org}/teams/{team_slug}/repos`.
- **Catalog import**: pluggable provider interface to ingest repo lists from external catalogs; register providers with namespaced IDs.
- Feature flags per provider (e.g., `selection.codeowners.enabled`).

## Repo resolution
- Selection Service merges optional sources with query results, annotating `selection_reason` (`codeowners`, `team`, `catalog`).
- Conflicts resolved by priority order (include override > exclude patterns > optional integrations).

## Auto-merge configuration
- Campaign-level setting `autoMerge.enabled` + `strategy` (`merge`, `squash`, `rebase` if allowed by repo) and `requirements` (checks, approvals).
- Publisher sets PR auto-merge via GraphQL mutation when desired state satisfied (checks green + approval count >= configured threshold).
- Reconciler re-applies auto-merge setting if removed.

## Tests
- Mock CODEOWNERS/teams responses to ensure correct repo resolution and reason tagging.
- Auto-merge tests verifying mutation only sent when policy conditions met and feature flag enabled.
- Ensure policy respected: no auto-merge on repos disallowing the chosen strategy.

## Rollback
- Feature flags allow disabling integrations or auto-merge globally without code changes.
