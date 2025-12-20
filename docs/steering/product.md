# GitHub Campaigns for Bulk PRs – Product

## Intent and Problem Statement

Provide an organization-native way to run declarative, auditable bulk pull request campaigns across thousands of repos, replacing ad-hoc scripts and unmanaged PR spam. Users define a campaign spec, preview changes safely, publish with throttles, and reconcile PRs until completion.

## Target Users and Primary Journeys

- Platform/release engineers: create/edit campaign specs, run preview, publish throttled PRs, monitor status.
- Org admins: install/configure GitHub App, set policies/throttles, manage drift policies.
- Maintainers/reviewers: receive consistent PRs, see campaign context and links, request updates or drift handling.
- Operators/SREs: deploy/upgrade service, watch health/alerts, handle incident response.

Primary journeys:

- Author spec → preview → inspect diffs/logs → publish → monitor/open PRs → reconcile drifts → complete campaign.
- Admin configure GitHub App + external deps → verify connectivity → enable throttles/kill switch.
- Maintainer flags manual edits → drift policy marks “needs human” → update/retry as needed.

## Success Metrics and Guardrails

- Time to deliver a 1,000-repo campaign (preview + publish) under configured throttles.
- PR duplication rate: 0 duplicate PRs per repo per spec version.
- Reconcile freshness: <15 minutes lag steady state; 99% webhooks processed <2 minutes.
- Error rate for job executions and GitHub API calls within alert thresholds.
- Security guardrails: 0 bypasses of branch protection or required checks; default deny egress enforced.

## Out of Scope

- Non-GitHub forges (GitLab/Bitbucket).
- Granting privileged network access to workers by default.

## UX Notes

- Spec editor with schema validation and preview of resolved targets.
- Run dashboards grouped by status (no-change/patch/failed/ready/open/merged).
- Repo detail view with logs, patch/diff summary, PR link, retry/close actions.
- Clear indicators for drift policy actions (force-pushed, new PR opened, needs-human).
- CLI mirrors core flows with concise status outputs and campaign/run IDs.

## Launch and Rollout Narrative

- Alpha: internal/staging deployments validating preview/publish flows on small orgs; throttle defaults locked low.
- Beta: selected customers on GitHub.com and GHES; enable reconciliation and drift policies; add observability dashboards.
- GA: throttles configurable, bulk actions and CLI enabled, documentation for HA and backups, optional P2 features gated by flags.
- Comms: coordinate with platform teams and org admins; publish deployment and security notes; provide rollback/kill switch guidance.

## FAQ and Edge Cases

- **What if a repo leaves selection after publish?** Drift policy decides: close PR and delete branch, or mark needs-human.
- **What if branch protection blocks pushes?** Publish fails gracefully, recorded in audit/logs; requires maintainer action.
- **How are secrets handled in logs?** Redaction in runners; artifact proxy enforces size/retention; no storage creds in jobs.
- **What if webhooks are missed?** Periodic reconcile refreshes active changesets to restore accuracy.
- **Can we run on GHES?** Yes, configurable GitHub API base URL; requires GitHub App installed on GHES instance.
